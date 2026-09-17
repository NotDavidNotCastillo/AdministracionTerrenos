from database import conectar_bd  # conectar a base de datos con mssql_python
import tkinter as tk
from tkinter import ttk, messagebox
import hashlib

# Variables globales de la ventana
ventana_usuarios = None
tabla_usuarios = None
entry_usuario = None
entry_correo = None
entry_clave = None
combo_rol = None
var_estado = None
roles_dict = {}          # {"vendedor": 2, "administrador": 1, ...}
id_usuario_seleccionado = None

def abrir_usuarios():
    global ventana_usuarios, tabla_usuarios, entry_usuario, entry_correo
    global entry_clave, combo_rol, var_estado

    try:
        if ventana_usuarios is not None and ventana_usuarios.winfo_exists():
            ventana_usuarios.lift()
            ventana_usuarios.focus_force()
            return
    except (NameError, AttributeError, tk.TclError):
        pass

    ventana_usuarios = tk.Toplevel()
    ventana_usuarios.title("LotesDB - Gestión de Usuarios")
    ventana_usuarios.geometry("800x550")
    ventana_usuarios.resizable(False, False)

    # ---------------- Formulario ----------------
    panel_formulario = tk.LabelFrame(ventana_usuarios, text="Datos del usuario", padx=10, pady=10)
    panel_formulario.pack(fill="x", padx=10, pady=10)

    tk.Label(panel_formulario, text="Usuario:").grid(row=0, column=0, sticky="w", pady=4)
    entry_usuario = tk.Entry(panel_formulario, width=25)
    entry_usuario.grid(row=0, column=1, padx=(5, 20))

    tk.Label(panel_formulario, text="Correo:").grid(row=0, column=2, sticky="w", pady=4)
    entry_correo = tk.Entry(panel_formulario, width=25)
    entry_correo.grid(row=0, column=3, padx=5)

    tk.Label(panel_formulario, text="Contraseña:").grid(row=1, column=0, sticky="w", pady=4)
    entry_clave = tk.Entry(panel_formulario, width=25, show="*")
    entry_clave.grid(row=1, column=1, padx=(5, 20))

    tk.Label(panel_formulario, text="Rol:").grid(row=1, column=2, sticky="w", pady=4)
    combo_rol = ttk.Combobox(panel_formulario, width=22, state="readonly")
    combo_rol.grid(row=1, column=3, padx=5)

    var_estado = tk.IntVar(value=1)
    tk.Checkbutton(panel_formulario, text="Activo", variable=var_estado).grid(
        row=2, column=0, sticky="w", pady=(6, 0)
    )

    # ---------------- Botones ----------------
    panel_botones = tk.Frame(ventana_usuarios)
    panel_botones.pack(fill="x", padx=10)

    tk.Button(panel_botones, text="Agregar", width=12, command=agregar_usuario).pack(side="left", padx=5)
    tk.Button(panel_botones, text="Actualizar", width=12, command=actualizar_usuario).pack(side="left", padx=5)
    tk.Button(panel_botones, text="Eliminar", width=12, command=eliminar_usuario).pack(side="left", padx=5)
    tk.Button(panel_botones, text="Limpiar", width=12, command=limpiar_campos).pack(side="left", padx=5)

    # ---------------- Tabla ----------------
    panel_tabla = tk.Frame(ventana_usuarios)
    panel_tabla.pack(fill="both", expand=True, padx=10, pady=10)

    scroll_y = ttk.Scrollbar(panel_tabla, orient="vertical")

    columnas = ("ID", "Usuario", "Correo", "Rol", "Último Acceso", "Estado")
    tabla_usuarios = ttk.Treeview(
        panel_tabla, columns=columnas, show="headings", yscrollcommand=scroll_y.set
    )
    scroll_y.config(command=tabla_usuarios.yview)

    anchos = (40, 130, 180, 110, 110, 80)
    for encabezado, ancho in zip(columnas, anchos):
        tabla_usuarios.heading(encabezado, text=encabezado)
        tabla_usuarios.column(encabezado, width=ancho, anchor="center")

    tabla_usuarios.tag_configure("par", background="#f2f2f2")
    tabla_usuarios.tag_configure("impar", background="#ffffff")
    tabla_usuarios.bind("<<TreeviewSelect>>", seleccionar_fila)

    scroll_y.pack(side="right", fill="y")
    tabla_usuarios.pack(fill="both", expand=True)

    cargar_roles()
    cargar_usuarios()

def hashear_clave(texto_claro):
    """Genera el hash SHA-256 (32 bytes) que se guarda en Usuarios.Clave."""
    return hashlib.sha256(texto_claro.encode("utf-8")).digest()


def cargar_roles():
    """Llena el combobox de roles consultando la tabla Roles."""
    global roles_dict
    conexion = None
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("SELECT IdRol, NombreRol FROM Roles ORDER BY NombreRol")
        filas = cursor.fetchall()
        roles_dict = {row[1]: row[0] for row in filas}
        combo_rol["values"] = list(roles_dict.keys())
    except Exception as error:
        messagebox.showerror("Error", f"No se pudieron cargar los roles:\n{error}")
    finally:
        if conexion:
            conexion.close()


def cargar_usuarios():
    """Consulta todos los usuarios y refresca la tabla."""
    tabla_usuarios.delete(*tabla_usuarios.get_children())
    conexion = None
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT u.IdUsuario, u.Usuario, u.Correo, r.NombreRol,
                   u.UltimoAcceso,
                   CASE WHEN u.Estado = 1 THEN 'Activo' ELSE 'Inactivo' END
            FROM Usuarios u
            INNER JOIN Roles r ON u.IdRol = r.IdRol
            ORDER BY u.IdUsuario
        """)
        filas = cursor.fetchall()
        for indice, row in enumerate(filas):
            etiqueta = "par" if indice % 2 == 0 else "impar"
            valores = (row[0], row[1], row[2] or "", row[3], row[4], row[5])
            tabla_usuarios.insert("", tk.END, values=valores, tags=(etiqueta,))
    except Exception as error:
        messagebox.showerror("Error", f"No se pudieron cargar los usuarios:\n{error}")
    finally:
        if conexion:
            conexion.close()


def limpiar_campos():
    global id_usuario_seleccionado
    id_usuario_seleccionado = None
    entry_usuario.delete(0, tk.END)
    entry_correo.delete(0, tk.END)
    entry_clave.delete(0, tk.END)
    combo_rol.set("")
    var_estado.set(1)
    tabla_usuarios.selection_remove(tabla_usuarios.selection())


def seleccionar_fila(_event=None):
    """Al elegir una fila de la tabla, carga sus datos en el formulario."""
    global id_usuario_seleccionado
    seleccion = tabla_usuarios.selection()
    if not seleccion:
        return

    valores = tabla_usuarios.item(seleccion[0], "values")
    id_usuario_seleccionado = valores[0]

    entry_usuario.delete(0, tk.END)
    entry_usuario.insert(0, valores[1])

    entry_correo.delete(0, tk.END)
    entry_correo.insert(0, valores[2])

    entry_clave.delete(0, tk.END)  # la contraseña nunca se muestra

    combo_rol.set(valores[3])
    var_estado.set(1 if valores[5] == "Activo" else 0)


def validar_campos(requiere_clave):
    usuario = entry_usuario.get().strip()
    rol = combo_rol.get().strip()
    clave = entry_clave.get().strip()

    if not usuario:
        messagebox.showwarning("Usuarios", "El campo Usuario es obligatorio.")
        return False
    if not rol or rol not in roles_dict:
        messagebox.showwarning("Usuarios", "Seleccione un rol válido.")
        return False
    if requiere_clave and not clave:
        messagebox.showwarning("Usuarios", "La contraseña es obligatoria.")
        return False
    return True


def agregar_usuario():
    if not validar_campos(requiere_clave=True):
        return

    usuario = entry_usuario.get().strip()
    correo = entry_correo.get().strip() or None
    id_rol = roles_dict[combo_rol.get().strip()]
    clave_hash = hashear_clave(entry_clave.get().strip())
    estado = var_estado.get()

    conexion = None
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO Usuarios (IdRol, Usuario, Correo, Clave, Estado)
            VALUES (?, ?, ?, ?, ?)
            """,
            (id_rol, usuario, correo, clave_hash, estado),
        )
        conexion.commit()
        messagebox.showinfo("Usuarios", "Usuario agregado correctamente.")
        limpiar_campos()
        cargar_usuarios()
    except Exception as error:
        messagebox.showerror("Error", f"No se pudo agregar el usuario:\n{error}")
    finally:
        if conexion:
            conexion.close()


def actualizar_usuario():
    if id_usuario_seleccionado is None:
        messagebox.showwarning("Usuarios", "Seleccione un usuario de la tabla.")
        return
    if not validar_campos(requiere_clave=False):
        return

    usuario = entry_usuario.get().strip()
    correo = entry_correo.get().strip() or None
    id_rol = roles_dict[combo_rol.get().strip()]
    estado = var_estado.get()
    clave_texto = entry_clave.get().strip()

    conexion = None
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        if clave_texto:
            cursor.execute(
                """
                UPDATE Usuarios
                SET IdRol = ?, Usuario = ?, Correo = ?, Clave = ?, Estado = ?
                WHERE IdUsuario = ?
                """,
                (id_rol, usuario, correo, hashear_clave(clave_texto), estado,
                 id_usuario_seleccionado),
            )
        else:
            cursor.execute(
                """
                UPDATE Usuarios
                SET IdRol = ?, Usuario = ?, Correo = ?, Estado = ?
                WHERE IdUsuario = ?
                """,
                (id_rol, usuario, correo, estado, id_usuario_seleccionado),
            )
        conexion.commit()
        messagebox.showinfo("Usuarios", "Usuario actualizado correctamente.")
        limpiar_campos()
        cargar_usuarios()
    except Exception as error:
        messagebox.showerror("Error", f"No se pudo actualizar el usuario:\n{error}")
    finally:
        if conexion:
            conexion.close()


def eliminar_usuario():
    if id_usuario_seleccionado is None:
        messagebox.showwarning("Usuarios", "Seleccione un usuario de la tabla.")
        return

    confirmar = messagebox.askyesno(
        "Usuarios",
        "¿Seguro que desea eliminar este usuario? Esta acción no se puede deshacer."
    )
    if not confirmar:
        return

    conexion = None
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM Usuarios WHERE IdUsuario = ?", (id_usuario_seleccionado,))
        conexion.commit()
        messagebox.showinfo("Usuarios", "Usuario eliminado correctamente.")
        limpiar_campos()
        cargar_usuarios()
    except Exception as error:
        messagebox.showerror("Error", f"No se pudo eliminar el usuario:\n{error}")
    finally:
        if conexion:
            conexion.close()


# if __name__ == "__main__":
#     root = tk.Tk()
#     root.withdraw()
#     abrir_usuarios()
#     root.mainloop()