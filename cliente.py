import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import re

from database import conectar_bd


def abrir_clientes(usuario=None):
    global ventana_clientes, tabla_clientes

    try:
        if ventana_clientes.winfo_exists():
            ventana_clientes.lift()
            ventana_clientes.focus_force()
            return
    except (NameError, tk.TclError):
        pass

    ventana_clientes = tk.Toplevel()
    ventana_clientes.title("LotesDB - Gestión de Clientes")
    ventana_clientes.geometry("1000x600")
    ventana_clientes.resizable(False, False)

    rol = usuario.get("NombreRol")
    print(rol)

    # === PERMISOS ===
    # get_crear    = bool(usuario.get("Crear")) if usuario else False
    # get_editar   = bool(usuario.get("Editar")) if usuario else False
    # get_eliminar = bool(usuario.get("Eliminar")) if usuario else False

    tk.Label(ventana_clientes, text="Gestión de Clientes",
             font=("Arial", 22, "bold")).pack(pady=12)

    marco_busqueda = tk.Frame(ventana_clientes)
    marco_busqueda.pack(pady=5)

    tk.Label(marco_busqueda, text="Buscar:").pack(side="left", padx=5)
    entrada_busqueda = tk.Entry(marco_busqueda, width=28)
    entrada_busqueda.pack(side="left", padx=5)

    combo_busqueda = ttk.Combobox(
        marco_busqueda,
        values=["Todos", "Identidad", "Nombre", "Apellido", "Teléfono",
                "Correo", "Ciudad", "Dirección"],
        state="readonly", width=18
    )
    combo_busqueda.set("Todos")
    combo_busqueda.pack(side="left", padx=5)

    tk.Button(marco_busqueda, text="Buscar", width=12,
              command=lambda: cargar_clientes(entrada_busqueda.get(), combo_busqueda.get())).pack(side="left", padx=5)
    tk.Button(marco_busqueda, text="Mostrar todos", width=14,
              command=lambda: (entrada_busqueda.delete(0, tk.END), cargar_clientes())).pack(side="left", padx=5)

    marco_tabla = tk.Frame(ventana_clientes)
    marco_tabla.pack(fill="both", expand=True, padx=15, pady=10)

    columnas = ("idcliente", "identidad", "nombre", "apellido", "telefono",
                "correo", "direccion", "ciudad", "estado")
    tabla_clientes = ttk.Treeview(marco_tabla, columns=columnas, show="headings", height=18)

    encabezados = {
        "idcliente": "ID", "identidad": "Identidad", "nombre": "Nombre",
        "apellido": "Apellido", "telefono": "Teléfono", "correo": "Correo",
        "direccion": "Dirección", "ciudad": "Ciudad", "estado": "Estado"
    }
    anchos = {
        "idcliente": 50, "identidad": 120, "nombre": 130, "apellido": 130,
        "telefono": 110, "correo": 160, "direccion": 180, "ciudad": 120,
        "estado": 90
    }
    for columna in columnas:
        tabla_clientes.heading(columna, text=encabezados[columna])
        tabla_clientes.column(columna, width=anchos[columna], anchor="center", stretch=False)

    tabla_clientes.pack(side="left", fill="both", expand=True)
    scroll_y = ttk.Scrollbar(marco_tabla, orient="vertical", command=tabla_clientes.yview)
    scroll_y.pack(side="right", fill="y")
    tabla_clientes.configure(yscrollcommand=scroll_y.set)

    # ==== MARCO DE BOTONES ====
    marco_botones = tk.Frame(ventana_clientes)
    marco_botones.pack(pady=8)

    boton_agregar = tk.Button(
        marco_botones,
        text="Agregar cliente", width=17, command=agregar_cliente
    )
    boton_agregar.pack(side="left", padx=5)

    boton_editar = tk.Button(
        marco_botones,
        text="Editar cliente",
        width=17, command=editar_cliente,
    )
    boton_editar.pack(side="left", padx=5)

    boton_anular = tk.Button(
        marco_botones,
        text="Anular cliente",
        width=17,
        command=anular_cliente
    )
    boton_anular.pack(side="left", padx=5)

    tk.Button(marco_botones, text="Actualizar", width=17,
              command=cargar_clientes).pack(side="left", padx=5)
    tk.Button(marco_botones, text="Cerrar", width=17,
              command=ventana_clientes.destroy).pack(side="left", padx=5)

    boton_activar = tk.Button(
        marco_botones,
        text="Activar cliente",
        width=18,
        command=activar_cliente,
    )
    boton_activar.pack(side="left", padx=5)


def validar_datos_cliente(identidad, nombre, apellido, telefono, correo):
    if not re.fullmatch(r"[0-9\-]+", identidad):
        messagebox.showwarning("Identidad inválida", "La identidad solo puede contener números y guiones.")
        return False

    if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+", nombre):
        messagebox.showwarning("Nombre inválido", "El nombre solo puede contener letras y espacios.")
        return False

    if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+", apellido):
        messagebox.showwarning("Apellido inválido", "El apellido solo puede contener letras y espacios.")
        return False

    if telefono and not re.fullmatch(r"[0-9\-\+\s]+", telefono):
        messagebox.showwarning("Teléfono inválido", "El teléfono solo puede contener números, espacios, + y guiones.")
        return False

    if correo and not re.fullmatch(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", correo):
        messagebox.showwarning("Correo inválido", "Ingrese un correo válido. Ejemplo: usuario@gmail.com")
        return False

    return True


def cargar_clientes(filtro="", campo="Todos"):
    for fila in tabla_clientes.get_children():
        tabla_clientes.delete(fila)

    conexion = None
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()

        sql = """
            SELECT
                C.IdCliente,
                C.Identidad,
                C.Nombre,
                C.Apellido,
                C.Telefono,
                C.Correo,
                C.Direccion,
                CI.NombreCiudad,
                C.Estado
            FROM Clientes C
            LEFT JOIN Ciudades CI ON C.IdCiudad = CI.IdCiudad
        """

        parametros = ()
        if filtro.strip():
            f = f"%{filtro.strip()}%"
            condiciones = {
                "Todos": """
                    C.Identidad LIKE ? OR C.Nombre LIKE ? OR C.Apellido LIKE ?
                    OR C.Telefono LIKE ? OR C.Correo LIKE ? OR C.Direccion LIKE ?
                    OR CI.NombreCiudad LIKE ?
                """,
                "Identidad": "C.Identidad LIKE ?",
                "Nombre": "C.Nombre LIKE ?",
                "Apellido": "C.Apellido LIKE ?",
                "Teléfono": "C.Telefono LIKE ?",
                "Correo": "C.Correo LIKE ?",
                "Ciudad": "CI.NombreCiudad LIKE ?",
                "Dirección": "C.Direccion LIKE ?"
            }
            sql += " WHERE " + condiciones.get(campo, condiciones["Todos"])
            parametros = (f,) * (7 if campo == "Todos" else 1)

        sql += " ORDER BY C.IdCliente DESC"
        cursor.execute(sql, parametros)

        for cliente in cursor.fetchall():
            estado_texto = "ACTIVO" if cliente[8] else "INACTIVO"
            tabla_clientes.insert("", tk.END, values=(
                cliente[0], cliente[1], cliente[2], cliente[3],
                cliente[4] or "", cliente[5] or "", cliente[6] or "",
                cliente[7] or "", estado_texto
            ))

        cursor.close()
        conexion.close()

    except Exception as error:
        if conexion is not None:
            conexion.close()
        messagebox.showerror("Error", f"No se pudieron cargar los clientes.\n\n{error}")


def cargar_ciudades():
    conexion = None
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT IdCiudad, NombreCiudad
            FROM Ciudades
            WHERE Estado = 1
            ORDER BY NombreCiudad;
        """)
        ciudades = cursor.fetchall()
        cursor.close()
        conexion.close()
        return ciudades
    except Exception as error:
        if conexion is not None:
            conexion.close()
        messagebox.showerror("Error", f"No se pudieron cargar las ciudades.\n\n{error}")
        return []


def obtener_cliente_seleccionado():
    seleccion = tabla_clientes.selection()
    if not seleccion:
        messagebox.showwarning("Seleccione un cliente", "Debe seleccionar un cliente de la tabla.")
        return None
    return tabla_clientes.item(seleccion[0], "values")


def agregar_cliente():
    global ventana_formulario

    try:
        if ventana_formulario.winfo_exists():
            ventana_formulario.lift()
            ventana_formulario.focus_force()
            return
    except (NameError, tk.TclError):
        pass

    ventana_formulario = tk.Toplevel(ventana_clientes)
    ventana_formulario.title("Agregar Cliente")
    ventana_formulario.geometry("520x420")
    ventana_formulario.resizable(False, False)

    tk.Label(ventana_formulario, text="Nuevo Cliente", font=("Arial", 20, "bold")).pack(pady=15)
    marco = tk.Frame(ventana_formulario)
    marco.pack()

    campos = [
        ("Identidad:", "identidad"),
        ("Nombre:", "nombre"),
        ("Apellido:", "apellido"),
        ("Teléfono:", "telefono"),
        ("Correo:", "correo"),
        ("Dirección:", "direccion"),
    ]

    entradas = {}
    for fila, (texto, clave) in enumerate(campos):
        tk.Label(marco, text=texto).grid(row=fila, column=0, padx=10, pady=7, sticky="e")
        entradas[clave] = tk.Entry(marco, width=34)
        entradas[clave].grid(row=fila, column=1, padx=10, pady=7)

    tk.Label(marco, text="Ciudad:").grid(row=6, column=0, padx=10, pady=7, sticky="e")
    combo_ciudad = ttk.Combobox(marco, width=31, state="readonly")
    ciudades = cargar_ciudades()
    combo_ciudad["values"] = [c[1] for c in ciudades]
    combo_ciudad.grid(row=6, column=1, padx=10, pady=7)

    def guardar():
        identidad = entradas["identidad"].get().strip()
        nombre = entradas["nombre"].get().strip()
        apellido = entradas["apellido"].get().strip()
        telefono = entradas["telefono"].get().strip()
        correo = entradas["correo"].get().strip()
        direccion = entradas["direccion"].get().strip()
        ciudad_nombre = combo_ciudad.get().strip()

        for valor, mensaje in [
            (identidad, "Debe ingresar la identidad."),
            (nombre, "Debe ingresar el nombre."),
            (apellido, "Debe ingresar el apellido."),
            (ciudad_nombre, "Debe seleccionar una ciudad.")
        ]:
            if not valor:
                messagebox.showwarning("Campo obligatorio", mensaje)
                return

        if not validar_datos_cliente(identidad, nombre, apellido, telefono, correo):
            return

        conexion = None
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT IdCiudad FROM Ciudades
                WHERE NombreCiudad = ? AND Estado = 1;
            """, (ciudad_nombre,))
            ciudad = cursor.fetchone()
            if ciudad is None:
                messagebox.showerror("Error", "La ciudad seleccionada no es válida.")
                cursor.close(); conexion.close(); return

            idciudad = ciudad[0]

            cursor.execute("SELECT COUNT(*) FROM Clientes WHERE Identidad = ?;", (identidad,))
            if cursor.fetchone()[0] > 0:
                messagebox.showwarning("Cliente duplicado", "Ya existe un cliente con esa identidad.")
                cursor.close(); conexion.close(); return

            cursor.execute("""
                INSERT INTO Clientes (
                    IdCiudad, Nombre, Apellido, Identidad, Telefono,
                    Correo, Direccion, Estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1);
            """, (
                idciudad, nombre, apellido, identidad,
                telefono or None, correo or None, direccion or None
            ))
            conexion.commit()
            cursor.close(); conexion.close()

            messagebox.showinfo("Cliente registrado", "El cliente se registró correctamente.")
            cargar_clientes()

            for entrada in entradas.values():
                entrada.delete(0, tk.END)
            combo_ciudad.set("")
            entradas["identidad"].focus()

        except Exception as error:
            if conexion is not None:
                conexion.close()
            messagebox.showerror("Error", f"No se pudo registrar el cliente.\n\n{error}")

    tk.Button(ventana_formulario, text="Guardar", width=18, command=guardar).pack(pady=12)
    tk.Button(ventana_formulario, text="Cerrar", width=18,
              command=ventana_formulario.destroy).pack()
    entradas["identidad"].focus()


def editar_cliente():
    seleccionado = obtener_cliente_seleccionado()
    if seleccionado is None:
        return

    idcliente = seleccionado[0]
    conexion = None
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT Identidad, Nombre, Apellido, Telefono, Correo, Direccion, IdCiudad
            FROM Clientes WHERE IdCliente = ?;
        """, (idcliente,))
        cliente = cursor.fetchone()
        cursor.close(); conexion.close()
    except Exception as error:
        if conexion is not None:
            conexion.close()
        messagebox.showerror("Error", f"No se pudo cargar el cliente.\n\n{error}")
        return

    if not cliente:
        messagebox.showerror("Error", "No se encontró el cliente seleccionado.")
        return

    ventana_editar = tk.Toplevel(ventana_clientes)
    ventana_editar.title("Editar Cliente")
    ventana_editar.geometry("520x420")
    ventana_editar.resizable(False, False)

    tk.Label(ventana_editar, text="Editar Cliente", font=("Arial", 20, "bold")).pack(pady=15)
    marco = tk.Frame(ventana_editar)
    marco.pack()

    etiquetas = ["Identidad:", "Nombre:", "Apellido:", "Teléfono:", "Correo:", "Dirección:"]
    claves = ["identidad", "nombre", "apellido", "telefono", "correo", "direccion"]
    entradas = {}

    for i, (texto, clave) in enumerate(zip(etiquetas, claves)):
        tk.Label(marco, text=texto).grid(row=i, column=0, padx=10, pady=7, sticky="e")
        entradas[clave] = tk.Entry(marco, width=34)
        entradas[clave].grid(row=i, column=1, padx=10, pady=7)
        entradas[clave].insert(0, cliente[i] or "")

    tk.Label(marco, text="Ciudad:").grid(row=6, column=0, padx=10, pady=7, sticky="e")
    combo_ciudad = ttk.Combobox(marco, width=31, state="readonly")
    ciudades = cargar_ciudades()
    combo_ciudad["values"] = [c[1] for c in ciudades]
    combo_ciudad.grid(row=6, column=1, padx=10, pady=7)

    # cliente[6] = IdCiudad
    ciudad_actual = None
    if cliente[6]:
        for c in ciudades:
            if c[0] == cliente[6]:
                ciudad_actual = c[1]
                break
    if ciudad_actual:
        combo_ciudad.set(ciudad_actual)

    def actualizar():
        identidad = entradas["identidad"].get().strip()
        nombre = entradas["nombre"].get().strip()
        apellido = entradas["apellido"].get().strip()
        telefono = entradas["telefono"].get().strip()
        correo = entradas["correo"].get().strip()
        direccion = entradas["direccion"].get().strip()
        ciudad_nombre = combo_ciudad.get().strip()

        for valor, mensaje in [
            (identidad, "Debe ingresar la identidad."),
            (nombre, "Debe ingresar el nombre."),
            (apellido, "Debe ingresar el apellido."),
            (ciudad_nombre, "Debe seleccionar una ciudad.")
        ]:
            if not valor:
                messagebox.showwarning("Campo obligatorio", mensaje)
                return

        if not validar_datos_cliente(identidad, nombre, apellido, telefono, correo):
            return

        conexion = None
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT IdCiudad FROM Ciudades
                WHERE NombreCiudad = ? AND Estado = 1;
            """, (ciudad_nombre,))
            ciudad = cursor.fetchone()
            if ciudad is None:
                messagebox.showerror("Error", "La ciudad seleccionada no es válida.")
                cursor.close(); conexion.close(); return

            cursor.execute("""
                SELECT COUNT(*) FROM Clientes
                WHERE Identidad = ? AND IdCliente <> ?;
            """, (identidad, idcliente))
            if cursor.fetchone()[0] > 0:
                messagebox.showwarning("Identidad duplicada", "Ya existe otro cliente con esa identidad.")
                cursor.close(); conexion.close(); return

            cursor.execute("""
                UPDATE Clientes SET
                    Identidad = ?, Nombre = ?, Apellido = ?, Telefono = ?,
                    Correo = ?, Direccion = ?, IdCiudad = ?
                WHERE IdCliente = ?;
            """, (
                identidad, nombre, apellido, telefono or None,
                correo or None, direccion or None, ciudad[0], idcliente
            ))
            conexion.commit()
            cursor.close(); conexion.close()

            messagebox.showinfo("Cliente actualizado", "El cliente se actualizó correctamente.")
            ventana_editar.destroy()
            cargar_clientes()

        except Exception as error:
            if conexion is not None:
                conexion.close()
            messagebox.showerror("Error", f"No se pudo actualizar el cliente.\n\n{error}")

    tk.Button(ventana_editar, text="Guardar cambios", width=18, command=actualizar).pack(pady=12)
    tk.Button(ventana_editar, text="Cerrar", width=18,
              command=ventana_editar.destroy).pack()


def anular_cliente():
    cliente = obtener_cliente_seleccionado()
    if cliente is None:
        return

    idcliente = cliente[0]
    nombre = f"{cliente[2]} {cliente[3]}"

    if not messagebox.askyesno("Confirmar anulación", f"¿Está seguro de anular al cliente?\n\n{nombre}"):
        return

    conexion = None
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("UPDATE Clientes SET Estado = 0 WHERE IdCliente = ?;", (idcliente,))
        conexion.commit()
        cursor.close(); conexion.close()
        messagebox.showinfo("Cliente anulado", "El cliente fue anulado correctamente.")
        cargar_clientes()
    except Exception as error:
        if conexion is not None:
            conexion.close()
        messagebox.showerror("Error", f"No se pudo anular el cliente.\n\n{error}")


def activar_cliente():
    cliente = obtener_cliente_seleccionado()
    if cliente is None:
        return

    idcliente = cliente[0]
    nombre = f"{cliente[2]} {cliente[3]}"
    estado = cliente[8]

    if estado == "ACTIVO":
        messagebox.showinfo("Cliente activo", "El cliente seleccionado ya está ACTIVO.")
        return

    confirmar = messagebox.askyesno(
        "Confirmar activación",
        f"¿Desea activar nuevamente al cliente:\n\n{nombre}?"
    )
    if not confirmar:
        return

    conexion = None
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("UPDATE Clientes SET Estado = 1 WHERE IdCliente = ?;", (idcliente,))
        conexion.commit()
        cursor.close(); conexion.close()
        messagebox.showinfo("Cliente activado", "El cliente fue activado correctamente.")
        cargar_clientes()
    except Exception as error:
        if conexion is not None:
            conexion.close()
        messagebox.showerror("Error", f"No se pudo activar el cliente.\n\n{error}")


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    abrir_clientes()
    root.mainloop()