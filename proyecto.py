from database import conectar_bd
import tkinter as tk
from tkinter import ttk, messagebox
import re

# Estados válidos según la columna [Estado] varchar(30) de Proyectos
ESTADOS_PROYECTO = ["En Proceso", "En Desarrollo", "Aprobado", "Concluido", "Liquidado"]


# ============================================================
# VENTANA PRINCIPAL
# ============================================================
def abrir_proyecto(usuario=None):
    global ventana_proyecto, tabla, nombre_usuario
    nombre_usuario = usuario.get("NombreUsuario") if usuario else "Sistema"

    try:
        if ventana_proyecto.winfo_exists():
            ventana_proyecto.lift()
            ventana_proyecto.focus_force()
            return
    except (NameError, tk.TclError):
        pass

    ventana_proyecto = tk.Toplevel()
    ventana_proyecto.geometry("1100x600")
    ventana_proyecto.title("Gestión de Proyectos")
    ventana_proyecto.resizable(False, False)

    tk.Label(ventana_proyecto, text="Gestión de Proyectos",
             font=("Arial", 22, "bold")).pack(pady=12)

    # -------- Marco de búsqueda --------
    marco_busqueda = tk.Frame(ventana_proyecto)
    marco_busqueda.pack(pady=5)

    tk.Label(marco_busqueda, text="Buscar:").pack(side="left", padx=5)
    entrada_busqueda = tk.Entry(marco_busqueda, width=28)
    entrada_busqueda.pack(side="left", padx=5)

    combo_busqueda = ttk.Combobox(
        marco_busqueda,
        values=["Todos", "Nombre", "Ubicación", "Estado",
                "Fecha Inicio", "Fecha Final"],
        state="readonly", width=18
    )
    combo_busqueda.set("Todos")
    combo_busqueda.pack(side="left", padx=5)

    tk.Button(marco_busqueda, text="Buscar", width=12,
              command=lambda: cargar_proyectos(entrada_busqueda.get(),
                                               combo_busqueda.get())
              ).pack(side="left", padx=5)
    tk.Button(marco_busqueda, text="Mostrar todos", width=14,
              command=lambda: (entrada_busqueda.delete(0, tk.END),
                               cargar_proyectos())
              ).pack(side="left", padx=5)

    # -------- Marco de tabla --------
    marco_tabla = tk.Frame(ventana_proyecto)
    marco_tabla.pack(fill="both", expand=True, padx=15, pady=10)

    columnas = ("idproyecto", "nombre", "ubicacion",
                "fecha_inicio", "fecha_final", "estado")
    tabla = ttk.Treeview(marco_tabla, columns=columnas,
                         show="headings", height=18)

    encabezados = {
        "idproyecto": "ID",
        "nombre": "Nombre del Proyecto",
        "ubicacion": "Ubicación",
        "fecha_inicio": "Fecha Inicio",
        "fecha_final": "Fecha Final",
        "estado": "Estado"
    }
    anchos = {
        "idproyecto": 60,
        "nombre": 280,
        "ubicacion": 250,
        "fecha_inicio": 120,
        "fecha_final": 120,
        "estado": 140
    }
    for col in columnas:
        tabla.heading(col, text=encabezados[col])
        tabla.column(col, width=anchos[col], anchor="center", stretch=False)

    tabla.pack(side="left", fill="both", expand=True)
    scroll_y = ttk.Scrollbar(marco_tabla, orient="vertical",
                             command=tabla.yview)
    scroll_y.pack(side="right", fill="y")
    tabla.configure(yscrollcommand=scroll_y.set)

    # -------- Marco de botones --------
    marco_botones = tk.Frame(ventana_proyecto)
    marco_botones.pack(pady=8)

    tk.Button(marco_botones, text="Agregar proyecto", width=17,
              command=agregar_proyecto).pack(side="left", padx=5)
    tk.Button(marco_botones, text="Editar proyecto", width=17,
              command=editar_proyecto).pack(side="left", padx=5)
    tk.Button(marco_botones, text="Cambiar estado", width=17,
              command=cambiar_estado).pack(side="left", padx=5)
    tk.Button(marco_botones, text="Actualizar", width=17,
              command=cargar_proyectos).pack(side="left", padx=5)
    tk.Button(marco_botones, text="Cerrar", width=17,
              command=ventana_proyecto.destroy).pack(side="left", padx=5)

    cargar_proyectos()


# ============================================================
# CARGA DE DATOS
# ============================================================
def cargar_proyectos(filtro="", criterio="Todos"):
    for fila in tabla.get_children():
        tabla.delete(fila)

    conexion = conectar_bd()
    if not conexion:
        messagebox.showerror("Error", "No se pudo conectar a la base de datos")
        return

    try:
        cursor = conexion.cursor()
        query = """
            SELECT IdProyecto, NombreProyecto, Ubicacion,
                   FechaInicio, FechaFinal, Estado
            FROM Proyectos
        """
        parametros = []

        if filtro and criterio != "Todos":
            mapa = {
                "Nombre": "NombreProyecto",
                "Ubicación": "Ubicacion",
                "Estado": "Estado",
                "Fecha Inicio": "CONVERT(varchar(10), FechaInicio, 103)",
                "Fecha Final": "CONVERT(varchar(10), FechaFinal, 103)"
            }
            columna = mapa.get(criterio, "NombreProyecto")
            query += f" WHERE {columna} LIKE ?"
            parametros.append(f"%{filtro}%")
        elif filtro:
            query += """ WHERE NombreProyecto LIKE ? OR Ubicacion LIKE ?
                         OR Estado LIKE ?"""
            parametros.extend([f"%{filtro}%"] * 3)

        query += " ORDER BY IdProyecto DESC"
        cursor.execute(query, parametros)

        for fila in cursor.fetchall():
            fi = fila[3].strftime("%d/%m/%Y") if fila[3] else ""
            ff = fila[4].strftime("%d/%m/%Y") if fila[4] else ""
            tabla.insert("", "end", values=(
                fila[0], fila[1], fila[2] or "", fi, ff, fila[5] or ""
            ))
    except Exception as e:
        messagebox.showerror("Error", f"Error al cargar proyectos:\n{e}")
    finally:
        conexion.close()


# ============================================================
# FORMULARIO (AGREGAR / EDITAR)
# ============================================================
def _formulario_proyecto(titulo, datos=None):
    """Abre una ventana modal para agregar o editar un proyecto.
    Retorna el diccionario con los datos si se guarda, o None."""
    ventana = tk.Toplevel()
    ventana.title(titulo)
    ventana.geometry("480x430")
    ventana.resizable(False, False)
    ventana.transient(ventana_proyecto)
    ventana.grab_set()

    resultado = {"ok": False}

    # --- Campos ---
    tk.Label(ventana, text="Nombre del Proyecto: *").pack(anchor="w", padx=25, pady=(15, 2))
    entry_nombre = tk.Entry(ventana, width=48)
    entry_nombre.pack(padx=25)

    tk.Label(ventana, text="Ubicación:").pack(anchor="w", padx=25, pady=(10, 2))
    entry_ubicacion = tk.Entry(ventana, width=48)
    entry_ubicacion.pack(padx=25)

    tk.Label(ventana, text="Fecha Inicio (dd/mm/aaaa):").pack(anchor="w", padx=25, pady=(10, 2))
    entry_fi = tk.Entry(ventana, width=48)
    entry_fi.pack(padx=25)

    tk.Label(ventana, text="Fecha Final (dd/mm/aaaa):").pack(anchor="w", padx=25, pady=(10, 2))
    entry_ff = tk.Entry(ventana, width=48)
    entry_ff.pack(padx=25)

    tk.Label(ventana, text="Estado:").pack(anchor="w", padx=25, pady=(10, 2))
    combo_estado = ttk.Combobox(ventana, values=ESTADOS_PROYECTO,
                                state="readonly", width=45)
    combo_estado.set("En Proceso")
    combo_estado.pack(padx=25)

    # --- Pre-cargar datos si es edición ---
    if datos:
        entry_nombre.insert(0, datos.get("nombre", ""))
        entry_ubicacion.insert(0, datos.get("ubicacion", ""))
        entry_fi.insert(0, datos.get("fecha_inicio", ""))
        entry_ff.insert(0, datos.get("fecha_final", ""))
        combo_estado.set(datos.get("estado", "En Proceso"))

    # --- Validación ---
    def guardar():
        nombre = entry_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Validación",
                                   "El nombre del proyecto es obligatorio.",
                                   parent=ventana)
            return

        # Validar fechas (solo si se ingresaron)
        patron = r"^\d{2}/\d{2}/\d{4}$"
        fi = entry_fi.get().strip()
        ff = entry_ff.get().strip()
        if fi and not re.match(patron, fi):
            messagebox.showwarning("Validación",
                                   "Fecha Inicio inválida. Use dd/mm/aaaa.",
                                   parent=ventana)
            return
        if ff and not re.match(patron, ff):
            messagebox.showwarning("Validación",
                                   "Fecha Final inválida. Use dd/mm/aaaa.",
                                   parent=ventana)
            return

        resultado.update({
            "ok": True,
            "nombre": nombre,
            "ubicacion": entry_ubicacion.get().strip(),
            "fecha_inicio": fi,
            "fecha_final": ff,
            "estado": combo_estado.get()
        })
        ventana.destroy()

    # --- Botones ---
    marco_btn = tk.Frame(ventana)
    marco_btn.pack(pady=20)
    tk.Button(marco_btn, text="Guardar", width=14, command=guardar).pack(side="left", padx=8)
    tk.Button(marco_btn, text="Cancelar", width=14,
              command=ventana.destroy).pack(side="left", padx=8)

    ventana.wait_window()
    return resultado if resultado["ok"] else None


def _convertir_fecha(fecha_str):
    """Convierte dd/mm/aaaa a aaaa-mm-dd para SQL. Devuelve None si vacío."""
    if not fecha_str:
        return None
    d, m, a = fecha_str.split("/")
    return f"{a}-{m}-{d}"


# ============================================================
# AGREGAR
# ============================================================
def agregar_proyecto():
    datos = _formulario_proyecto("Agregar Proyecto")
    if not datos:
        return

    conexion = conectar_bd()
    if not conexion:
        messagebox.showerror("Error", "No se pudo conectar a la base de datos")
        return

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO Proyectos
                (NombreProyecto, Ubicacion, FechaInicio, FechaFinal, Estado)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datos["nombre"],
            datos["ubicacion"] or None,
            _convertir_fecha(datos["fecha_inicio"]),
            _convertir_fecha(datos["fecha_final"]),
            datos["estado"]
        ))
        conexion.commit()
        messagebox.showinfo("Éxito", "Proyecto agregado correctamente.")
        cargar_proyectos()
    except Exception as e:
        conexion.rollback()
        messagebox.showerror("Error", f"No se pudo agregar el proyecto:\n{e}")
    finally:
        conexion.close()


# ============================================================
# EDITAR
# ============================================================
def editar_proyecto():
    seleccion = tabla.selection()
    if not seleccion:
        messagebox.showwarning("Aviso", "Seleccione un proyecto para editar.")
        return

    valores = tabla.item(seleccion[0], "values")
    id_proyecto = valores[0]

    datos_actuales = {
        "nombre": valores[1],
        "ubicacion": valores[2],
        "fecha_inicio": valores[3],
        "fecha_final": valores[4],
        "estado": valores[5]
    }

    datos = _formulario_proyecto("Editar Proyecto", datos_actuales)
    if not datos:
        return

    conexion = conectar_bd()
    if not conexion:
        messagebox.showerror("Error", "No se pudo conectar a la base de datos")
        return

    try:
        cursor = conexion.cursor()
        cursor.execute("""
            UPDATE Proyectos
               SET NombreProyecto = ?,
                   Ubicacion      = ?,
                   FechaInicio    = ?,
                   FechaFinal     = ?,
                   Estado         = ?
             WHERE IdProyecto    = ?
        """, (
            datos["nombre"],
            datos["ubicacion"] or None,
            _convertir_fecha(datos["fecha_inicio"]),
            _convertir_fecha(datos["fecha_final"]),
            datos["estado"],
            id_proyecto
        ))
        conexion.commit()
        messagebox.showinfo("Éxito", "Proyecto actualizado correctamente.")
        cargar_proyectos()
    except Exception as e:
        conexion.rollback()
        messagebox.showerror("Error", f"No se pudo actualizar el proyecto:\n{e}")
    finally:
        conexion.close()


# ============================================================
# CAMBIAR ESTADO (rápido desde combobox)
# ============================================================
def cambiar_estado():
    seleccion = tabla.selection()
    if not seleccion:
        messagebox.showwarning("Aviso", "Seleccione un proyecto.")
        return

    valores = tabla.item(seleccion[0], "values")
    id_proyecto = valores[0]
    estado_actual = valores[5]

    # Ventana emergente con combobox de estados
    ventana = tk.Toplevel()
    ventana.title("Cambiar Estado")
    ventana.geometry("380x180")
    ventana.resizable(False, False)
    ventana.transient(ventana_proyecto)
    ventana.grab_set()

    tk.Label(ventana, text=f"Proyecto: {valores[1]}",
             font=("Arial", 11, "bold")).pack(pady=(15, 5))
    tk.Label(ventana, text="Nuevo Estado:").pack()

    combo = ttk.Combobox(ventana, values=ESTADOS_PROYECTO,
                         state="readonly", width=25)
    combo.set(estado_actual if estado_actual in ESTADOS_PROYECTO else "En Proceso")
    combo.pack(pady=8)

    def aplicar():
        nuevo = combo.get()
        conexion = conectar_bd()
        if not conexion:
            messagebox.showerror("Error", "No se pudo conectar a la base de datos")
            return
        try:
            cursor = conexion.cursor()
            cursor.execute(
                "UPDATE Proyectos SET Estado = ? WHERE IdProyecto = ?",
                (nuevo, id_proyecto)
            )
            conexion.commit()
            messagebox.showinfo("Éxito", "Estado actualizado correctamente.")
            ventana.destroy()
            cargar_proyectos()
        except Exception as e:
            conexion.rollback()
            messagebox.showerror("Error", f"No se pudo actualizar el estado:\n{e}")
        finally:
            conexion.close()

    marco = tk.Frame(ventana)
    marco.pack(pady=10)
    tk.Button(marco, text="Aplicar", width=12, command=aplicar).pack(side="left", padx=6)
    tk.Button(marco, text="Cancelar", width=12,
              command=ventana.destroy).pack(side="left", padx=6)



if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    abrir_proyecto()
    root.mainloop()