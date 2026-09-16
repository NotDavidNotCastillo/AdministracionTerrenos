from database import conectar_bd  # sirve para conectarse a la base de datos y realizar las consultas
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


def abrir_proyecto(usuario=None):
    global ventana_proyecto, tabla_proyectos

    try:
        if ventana_proyecto.winfo_exists():
            ventana_proyecto.lift()
            ventana_proyecto.focus_force()
            return
    except (NameError, tk.TclError):
        pass

    ventana_proyecto = tk.Toplevel()
    ventana_proyecto.title("Gestión de Proyectos")
    ventana_proyecto.geometry("1100x600")
    ventana_proyecto.resizable(False, False)

    tk.Label(ventana_proyecto, text="Gestión de Proyectos",
             font=("Arial", 22, "bold")).pack(pady=12)

    # ==== MARCO DE BÚSQUEDA ====
    marco_busqueda = tk.Frame(ventana_proyecto)
    marco_busqueda.pack(pady=5)

    tk.Label(marco_busqueda, text="Buscar:").pack(side="left", padx=5)
    entrada_busqueda = tk.Entry(marco_busqueda, width=28)
    entrada_busqueda.pack(side="left", padx=5)

    combo_busqueda = ttk.Combobox(
        marco_busqueda,
        values=["Todos", "Nombre", "Ubicación", "Estado"],
        state="readonly", width=18
    )
    combo_busqueda.set("Todos")
    combo_busqueda.pack(side="left", padx=5)

    tk.Button(marco_busqueda, text="Buscar", width=12,
              command=lambda: cargar_proyectos(entrada_busqueda.get(), combo_busqueda.get())).pack(side="left", padx=5)
    tk.Button(marco_busqueda, text="Mostrar todos", width=14,
              command=lambda: (entrada_busqueda.delete(0, tk.END), cargar_proyectos())).pack(side="left", padx=5)

    # ==== MARCO DE TABLA ====
    marco_tabla = tk.Frame(ventana_proyecto)
    marco_tabla.pack(fill="both", expand=True, padx=15, pady=10)

    columnas = ("idproyecto", "nombre", "ubicacion", "fecha_inicio", "estado")
    tabla_proyectos = ttk.Treeview(marco_tabla, columns=columnas, show="headings", height=18)

    encabezados = {
        "idproyecto": "ID", "nombre": "Nombre Proyecto", "ubicacion": "Ubicación",
        "fecha_inicio": "Fecha Inicio", "estado": "Estado"
    }
    anchos = {
        "idproyecto": 60, "nombre": 250, "ubicacion": 250,
        "fecha_inicio": 130, "estado": 150
    }
    for columna in columnas:
        tabla_proyectos.heading(columna, text=encabezados[columna])
        tabla_proyectos.column(columna, width=anchos[columna], anchor="center", stretch=False)

    tabla_proyectos.pack(side="left", fill="both", expand=True)
    scroll_y = ttk.Scrollbar(marco_tabla, orient="vertical", command=tabla_proyectos.yview)
    scroll_y.pack(side="right", fill="y")
    tabla_proyectos.configure(yscrollcommand=scroll_y.set)

    # ==== MARCO DE BOTONES ====
    marco_botones = tk.Frame(ventana_proyecto)
    marco_botones.pack(pady=8)

    tk.Button(marco_botones, text="Agregar proyecto", width=17,
              command=agregar_proyecto).pack(side="left", padx=5)
    tk.Button(marco_botones, text="Editar proyecto", width=17,
              command=editar_proyecto).pack(side="left", padx=5)
    tk.Button(marco_botones, text="Ver estatus", width=17,
              command=cambiar_estatus).pack(side="left", padx=5)
    tk.Button(marco_botones, text="Actualizar", width=17,
              command=cargar_proyectos).pack(side="left", padx=5)
    tk.Button(marco_botones, text="Cerrar", width=17,
              command=ventana_proyecto.destroy).pack(side="left", padx=5)

    cargar_proyectos()


# ============ CARGAR / BUSCAR ============

def cargar_proyectos(filtro="", tipo="Todos"):
    for item in tabla_proyectos.get_children():
        tabla_proyectos.delete(item)

    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()

        query = "SELECT IdProyecto, NombreProyecto, Ubicacion, FechaInicio, Estado FROM Proyectos"
        params = []

        if filtro and tipo != "Todos":
            columnas = {
                "Nombre": "NombreProyecto",
                "Ubicación": "Ubicacion",
                "Estado": "Estado"
            }
            if tipo in columnas:
                query += f" WHERE {columnas[tipo]} LIKE ?"
                params.append(f"%{filtro}%")

        cursor.execute(query, params)
        for fila in cursor.fetchall():
            fecha = fila[3].strftime("%Y-%m-%d") if fila[3] else ""
            tabla_proyectos.insert("", "end", values=(fila[0], fila[1], fila[2], fecha, fila[4]))
        conexion.close()
    except Exception as e:
        messagebox.showerror("Error", f"Error al cargar proyectos:\n{e}")


# ============ AGREGAR ============

def agregar_proyecto():
    ventana = tk.Toplevel()
    ventana.title("Agregar Proyecto")
    ventana.geometry("400x320")
    ventana.resizable(False, False)

    tk.Label(ventana, text="Nuevo Proyecto", font=("Arial", 16, "bold")).pack(pady=10)

    tk.Label(ventana, text="Nombre del Proyecto:").pack(anchor="w", padx=20)
    entry_nombre = tk.Entry(ventana, width=40)
    entry_nombre.pack(padx=20, pady=5)

    tk.Label(ventana, text="Ubicación:").pack(anchor="w", padx=20)
    entry_ubicacion = tk.Entry(ventana, width=40)
    entry_ubicacion.pack(padx=20, pady=5)

    tk.Label(ventana, text="Fecha Inicio (YYYY-MM-DD):").pack(anchor="w", padx=20)
    entry_fecha = tk.Entry(ventana, width=40)
    entry_fecha.pack(padx=20, pady=5)

    tk.Label(ventana, text="Estado:").pack(anchor="w", padx=20)
    combo_estado = ttk.Combobox(ventana, values=["En Proceso", "En Desarrollo", "Aprobado", "Concluido", "Liquidado"],
                                state="readonly", width=37)
    combo_estado.current(0)
    combo_estado.pack(padx=20, pady=5)

    def guardar():
        nombre = entry_nombre.get().strip()
        ubicacion = entry_ubicacion.get().strip()
        fecha = entry_fecha.get().strip()
        estado = combo_estado.get().strip()

        if not nombre:
            messagebox.showwarning("Validación", "El nombre del proyecto es obligatorio.")
            return

        try:
            fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date() if fecha else None
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD.")
            return

        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute(
                "INSERT INTO Proyectos (NombreProyecto, Ubicacion, FechaInicio, Estado) VALUES (?, ?, ?, ?)",
                (nombre, ubicacion, fecha_dt, estado)
            )
            conexion.commit()
            conexion.close()
            messagebox.showinfo("Éxito", "Proyecto agregado correctamente.")
            ventana.destroy()
            cargar_proyectos()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar proyecto:\n{e}")

    tk.Button(ventana, text="Guardar", width=15, command=guardar).pack(pady=15)


# ============ EDITAR ============

def editar_proyecto():
    seleccion = tabla_proyectos.selection()
    if not seleccion:
        messagebox.showwarning("Validación", "Seleccione un proyecto de la tabla para editar.")
        return

    valores = tabla_proyectos.item(seleccion[0], "values")
    id_proyecto = valores[0]

    ventana = tk.Toplevel()
    ventana.title("Editar Proyecto")
    ventana.geometry("400x320")
    ventana.resizable(False, False)

    tk.Label(ventana, text="Editar Proyecto", font=("Arial", 16, "bold")).pack(pady=10)

    tk.Label(ventana, text="Nombre del Proyecto:").pack(anchor="w", padx=20)
    entry_nombre = tk.Entry(ventana, width=40)
    entry_nombre.insert(0, valores[1])
    entry_nombre.pack(padx=20, pady=5)

    tk.Label(ventana, text="Ubicación:").pack(anchor="w", padx=20)
    entry_ubicacion = tk.Entry(ventana, width=40)
    entry_ubicacion.insert(0, valores[2] if valores[2] != "None" else "")
    entry_ubicacion.pack(padx=20, pady=5)

    tk.Label(ventana, text="Fecha Inicio (YYYY-MM-DD):").pack(anchor="w", padx=20)
    entry_fecha = tk.Entry(ventana, width=40)
    entry_fecha.insert(0, valores[3])
    entry_fecha.pack(padx=20, pady=5)

    tk.Label(ventana, text="Estado:").pack(anchor="w", padx=20)
    combo_estado = ttk.Combobox(ventana, values=["En Proceso", "En Desarrollo", "Aprobado", "Concluido", "Liquidado"],
                                state="readonly", width=37)
    combo_estado.set(valores[4])
    combo_estado.pack(padx=20, pady=5)

    def actualizar():
        nombre = entry_nombre.get().strip()
        ubicacion = entry_ubicacion.get().strip()
        fecha = entry_fecha.get().strip()
        estado = combo_estado.get().strip()

        if not nombre:
            messagebox.showwarning("Validación", "El nombre del proyecto es obligatorio.")
            return

        try:
            fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date() if fecha else None
        except ValueError:
            messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD.")
            return

        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute(
                "UPDATE Proyectos SET NombreProyecto=?, Ubicacion=?, FechaInicio=?, Estado=? WHERE IdProyecto=?",
                (nombre, ubicacion, fecha_dt, estado, id_proyecto)
            )
            conexion.commit()
            conexion.close()
            messagebox.showinfo("Éxito", "Proyecto actualizado correctamente.")
            ventana.destroy()
            cargar_proyectos()
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar proyecto:\n{e}")

    tk.Button(ventana, text="Actualizar", width=15, command=actualizar).pack(pady=15)


# ============ VER / CAMBIAR ESTATUS ============

def cambiar_estatus():
    seleccion = tabla_proyectos.selection()
    if not seleccion:
        messagebox.showwarning("Validación", "Seleccione un proyecto de la tabla para ver/cambiar su estatus.")
        return

    valores = tabla_proyectos.item(seleccion[0], "values")
    id_proyecto = valores[0]
    nombre = valores[1]
    estado_actual = valores[4]

    ventana = tk.Toplevel()
    ventana.title("Estatus del Proyecto")
    ventana.geometry("400x250")
    ventana.resizable(False, False)

    tk.Label(ventana, text="Estatus del Proyecto", font=("Arial", 16, "bold")).pack(pady=10)

    tk.Label(ventana, text=f"Proyecto: {nombre}", font=("Arial", 11)).pack(pady=5)
    tk.Label(ventana, text=f"Estatus actual: {estado_actual}", font=("Arial", 11, "bold"),
             fg="blue").pack(pady=5)

    tk.Label(ventana, text="Nuevo Estatus:").pack(anchor="w", padx=20, pady=(15, 0))
    combo_estado = ttk.Combobox(ventana, values=["En Proceso", "En Desarrollo", "Aprobado", "Concluido", "Liquidado"],
                                state="readonly", width=37)
    combo_estado.set(estado_actual)
    combo_estado.pack(padx=20, pady=5)

    def guardar_estatus():
        nuevo_estado = combo_estado.get().strip()
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute(
                "UPDATE Proyectos SET Estado=? WHERE IdProyecto=?",
                (nuevo_estado, id_proyecto)
            )
            conexion.commit()
            conexion.close()
            messagebox.showinfo("Éxito", "Estatus actualizado correctamente.")
            ventana.destroy()
            cargar_proyectos()
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar estatus:\n{e}")

    tk.Button(ventana, text="Guardar Estatus", width=17, command=guardar_estatus).pack(pady=15)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    abrir_proyecto()
    root.mainloop()