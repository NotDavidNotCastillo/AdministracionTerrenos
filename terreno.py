from database import conectar_bd  # sirve para conectarse a la base de datos y realizar las consultas
import tkinter as tk
from tkinter import ttk, messagebox

def abrir_terrenos(usuario=None):
    global ventana_terrenos, tabla_terrenos

    try:
        if ventana_terrenos.winfo_exists:
            ventana_terrenos.lift()
            ventana_terrenos.focus_force()
            return
    except (NameError, tk.TclError):
        pass

    ventana_terrenos = tk.Toplevel()
    ventana_terrenos.geometry("1200x600")
    ventana_terrenos.resizable(False, False)
    ventana_terrenos.title("Gestion de Terrenos")

    # ============ TÍTULO ============
    tk.Label(
        ventana_terrenos,
        text="Gestión de Terrenos",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=10)

    # ============ BARRA DE BÚSQUEDA ============
    frame_busqueda = tk.Frame(ventana_terrenos)
    frame_busqueda.pack(fill="x", padx=10, pady=5)

    tk.Label(frame_busqueda, text="Buscar:").pack(side="left", padx=(0, 5))
    entry_buscar = tk.Entry(frame_busqueda, width=30)
    entry_buscar.pack(side="left", padx=5)

    combo_filtro = ttk.Combobox(
        frame_busqueda,
        values=["Todos", "NombreTerreno", "Proyecto"],
        state="readonly",
        width=15
    )
    combo_filtro.current(0)
    combo_filtro.pack(side="left", padx=5)

    def buscar():
        texto = entry_buscar.get().strip()
        filtro = combo_filtro.get()
        cargar_terrenos(texto, filtro)

    def mostrar_todos():
        entry_buscar.delete(0, tk.END)
        combo_filtro.current(0)
        cargar_terrenos()

    tk.Button(frame_busqueda, text="Buscar", command=buscar).pack(side="left", padx=5)
    tk.Button(frame_busqueda, text="Mostrar todos", command=mostrar_todos).pack(side="left", padx=5)

    # ============ TABLA ============
    frame_tabla = tk.Frame(ventana_terrenos)
    frame_tabla.pack(fill="both", expand=True, padx=10, pady=10)

    columnas = ("ID", "NombreTerreno", "Proyecto", "AreaTotal", "CantidadLotes", "AreaLotes")
    tabla_terrenos = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=15)

    anchos = {
        "ID": 60,
        "NombreTerreno": 250,
        "Proyecto": 250,
        "AreaTotal": 130,
        "CantidadLotes": 130,
        "AreaLotes": 130,
    }

    for col in columnas:
        tabla_terrenos.heading(col, text=col)
        tabla_terrenos.column(col, width=anchos[col], anchor="center")

    scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=tabla_terrenos.yview)
    scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=tabla_terrenos.xview)
    tabla_terrenos.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

    tabla_terrenos.grid(row=0, column=0, sticky="nsew")
    scroll_y.grid(row=0, column=1, sticky="ns")
    scroll_x.grid(row=1, column=0, sticky="ew")

    frame_tabla.rowconfigure(0, weight=1)
    frame_tabla.columnconfigure(0, weight=1)

    # ============ BOTONES INFERIORES ============
    frame_botones = tk.Frame(ventana_terrenos)
    frame_botones.pack(fill="x", padx=10, pady=10)

    tk.Button(frame_botones, text="Agregar", width=15,
              command=lambda: agregar_terreno()).pack(side="left", padx=5)
    tk.Button(frame_botones, text="Editar", width=15,
              command=lambda: editar_terreno()).pack(side="left", padx=5)
    tk.Button(frame_botones, text="Ver estatus", width=15,
              command=lambda: ver_estatus()).pack(side="left", padx=5)
    tk.Button(frame_botones, text="Actualizar", width=15,
              command=lambda: cargar_terrenos()).pack(side="left", padx=5)
    tk.Button(frame_botones, text="Cerrar", width=15,
              command=ventana_terrenos.destroy).pack(side="right", padx=5)

    # ============ FUNCIONES INTERNAS ============

    def cargar_terrenos(texto="", filtro="Todos"):
        """Carga los terrenos desde la BD con el área total calculada."""
        for item in tabla_terrenos.get_children():
            tabla_terrenos.delete(item)

        try:
            conn = conectar_bd()
            cursor = conn.cursor()

            query = """
                SELECT
                    t.IdTerreno,
                    ISNULL(t.NombreTerreno, '(Sin nombre)') AS NombreTerreno,
                    p.NombreProyecto,
                    t.AreaTotal,
                    COUNT(l.IdLote) AS CantidadLotes,
                    ISNULL(SUM(l.Area), 0) AS AreaLotes
                FROM Terrenos t
                INNER JOIN Proyectos p ON t.IdProyecto = p.IdProyecto
                LEFT JOIN Lotes l ON l.IdTerreno = t.IdTerreno
                WHERE 1=1
            """
            params = []

            if texto:
                if filtro == "NombreTerreno":
                    query += " AND t.NombreTerreno LIKE ?"
                    params.append(f"%{texto}%")
                elif filtro == "Proyecto":
                    query += " AND p.NombreProyecto LIKE ?"
                    params.append(f"%{texto}%")
                else:  # Todos
                    query += " AND (t.NombreTerreno LIKE ? OR p.NombreProyecto LIKE ?)"
                    params.extend([f"%{texto}%", f"%{texto}%"])

            query += """
                GROUP BY t.IdTerreno, t.NombreTerreno, p.NombreProyecto, t.AreaTotal
                ORDER BY t.IdTerreno
            """

            cursor.execute(query, params)
            filas = cursor.fetchall()

            for fila in filas:
                id_t, nombre, proyecto, area_total, cant_lotes, area_lotes = fila
                tabla_terrenos.insert(
                    "", "end",
                    values=(
                        id_t,
                        nombre,
                        proyecto,
                        f"{area_total:,.2f} m²",
                        cant_lotes,
                        f"{area_lotes:,.2f} m²"
                    )
                )

            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los terrenos:\n{e}")

    def obtener_proyectos():
        """Devuelve lista de (IdProyecto, NombreProyecto)."""
        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("SELECT IdProyecto, NombreProyecto FROM Proyectos ORDER BY NombreProyecto")
            datos = cursor.fetchall()
            conn.close()
            return datos
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron obtener los proyectos:\n{e}")
            return []

    def agregar_terreno():
        """Abre una ventana para registrar un nuevo terreno y asignarlo a un proyecto."""
        ventana_add = tk.Toplevel(ventana_terrenos)
        ventana_add.title("Registrar Terreno")
        ventana_add.geometry("480x340")
        ventana_add.resizable(False, False)
        ventana_add.transient(ventana_terrenos)
        ventana_add.grab_set()

        tk.Label(ventana_add, text="Registrar nuevo terreno",
                 font=("Segoe UI", 13, "bold")).pack(pady=10)

        frame_form = tk.Frame(ventana_add)
        frame_form.pack(padx=20, pady=10, fill="both", expand=True)

        # Nombre del terreno
        tk.Label(frame_form, text="Nombre del terreno:").grid(row=0, column=0, sticky="w", pady=6)
        entry_nombre = tk.Entry(frame_form, width=30)
        entry_nombre.grid(row=0, column=1, pady=6, padx=5)

        # Proyecto (asignación)
        tk.Label(frame_form, text="Proyecto:").grid(row=1, column=0, sticky="w", pady=6)
        proyectos = obtener_proyectos()
        nombres_proyectos = [f"{p[0]} - {p[1]}" for p in proyectos] if proyectos else []
        combo_proyecto = ttk.Combobox(frame_form, values=nombres_proyectos,
                                      state="readonly", width=27)
        combo_proyecto.grid(row=1, column=1, pady=6, padx=5)
        if nombres_proyectos:
            combo_proyecto.current(0)

        # Área total
        tk.Label(frame_form, text="Área total (m²):").grid(row=2, column=0, sticky="w", pady=6)
        entry_area = tk.Entry(frame_form, width=30)
        entry_area.grid(row=2, column=1, pady=6, padx=5)

        def guardar():
            nombre = entry_nombre.get().strip()
            area_str = entry_area.get().strip()
            proyecto_sel = combo_proyecto.get()

            if not nombre:
                messagebox.showwarning("Aviso", "Debe ingresar el nombre del terreno.")
                return
            if not proyecto_sel:
                messagebox.showwarning("Aviso", "Debe seleccionar un proyecto.")
                return
            try:
                area = float(area_str)
                if area <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Aviso", "El área debe ser un número mayor a 0.")
                return

            id_proyecto = int(proyecto_sel.split(" - ")[0])

            try:
                conn = conectar_bd()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Terrenos (IdProyecto, NombreTerreno, AreaTotal)
                    VALUES (?, ?, ?)
                """, (id_proyecto, nombre, area))
                conn.commit()
                conn.close()

                messagebox.showinfo("Éxito", "Terreno registrado correctamente.")
                ventana_add.destroy()
                cargar_terrenos()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo registrar el terreno:\n{e}")

        frame_btn = tk.Frame(ventana_add)
        frame_btn.pack(pady=15)
        tk.Button(frame_btn, text="Guardar", width=12, command=guardar).pack(side="left", padx=8)
        tk.Button(frame_btn, text="Cancelar", width=12,
                  command=ventana_add.destroy).pack(side="left", padx=8)

    def editar_terreno():
        """Permite editar el nombre, proyecto y área total del terreno seleccionado."""
        seleccion = tabla_terrenos.selection()
        if not seleccion:
            messagebox.showwarning("Aviso", "Seleccione un terreno para editar.")
            return

        valores = tabla_terrenos.item(seleccion[0], "values")
        id_terreno = int(valores[0])

        # Traer datos actuales
        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT IdProyecto, ISNULL(NombreTerreno,''), AreaTotal
                FROM Terrenos WHERE IdTerreno = ?
            """, (id_terreno,))
            fila = cursor.fetchone()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener el terreno:\n{e}")
            return

        if not fila:
            messagebox.showerror("Error", "El terreno ya no existe.")
            return

        id_proyecto_actual, nombre_actual, area_actual = fila

        ventana_edit = tk.Toplevel(ventana_terrenos)
        ventana_edit.title("Editar Terreno")
        ventana_edit.geometry("480x340")
        ventana_edit.resizable(False, False)
        ventana_edit.transient(ventana_terrenos)
        ventana_edit.grab_set()

        tk.Label(ventana_edit, text=f"Editar terreno ID {id_terreno}",
                 font=("Segoe UI", 13, "bold")).pack(pady=10)

        frame_form = tk.Frame(ventana_edit)
        frame_form.pack(padx=20, pady=10, fill="both", expand=True)

        tk.Label(frame_form, text="Nombre del terreno:").grid(row=0, column=0, sticky="w", pady=6)
        entry_nombre = tk.Entry(frame_form, width=30)
        entry_nombre.insert(0, nombre_actual)
        entry_nombre.grid(row=0, column=1, pady=6, padx=5)

        tk.Label(frame_form, text="Proyecto:").grid(row=1, column=0, sticky="w", pady=6)
        proyectos = obtener_proyectos()
        nombres_proyectos = [f"{p[0]} - {p[1]}" for p in proyectos]
        combo_proyecto = ttk.Combobox(frame_form, values=nombres_proyectos,
                                      state="readonly", width=27)
        combo_proyecto.grid(row=1, column=1, pady=6, padx=5)
        for i, np in enumerate(nombres_proyectos):
            if np.startswith(f"{id_proyecto_actual} - "):
                combo_proyecto.current(i)
                break
        else:
            if nombres_proyectos:
                combo_proyecto.current(0)

        tk.Label(frame_form, text="Área total (m²):").grid(row=2, column=0, sticky="w", pady=6)
        entry_area = tk.Entry(frame_form, width=30)
        entry_area.insert(0, str(area_actual))
        entry_area.grid(row=2, column=1, pady=6, padx=5)

        def actualizar():
            nombre = entry_nombre.get().strip()
            area_str = entry_area.get().strip()
            proyecto_sel = combo_proyecto.get()

            if not nombre:
                messagebox.showwarning("Aviso", "Debe ingresar el nombre del terreno.")
                return
            if not proyecto_sel:
                messagebox.showwarning("Aviso", "Debe seleccionar un proyecto.")
                return
            try:
                area = float(area_str)
                if area <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Aviso", "El área debe ser un número mayor a 0.")
                return

            id_proyecto = int(proyecto_sel.split(" - ")[0])

            try:
                conn = conectar_bd()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE Terrenos
                    SET IdProyecto = ?, NombreTerreno = ?, AreaTotal = ?
                    WHERE IdTerreno = ?
                """, (id_proyecto, nombre, area, id_terreno))
                conn.commit()
                conn.close()

                messagebox.showinfo("Éxito", "Terreno actualizado correctamente.")
                ventana_edit.destroy()
                cargar_terrenos()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar el terreno:\n{e}")

        frame_btn = tk.Frame(ventana_edit)
        frame_btn.pack(pady=15)
        tk.Button(frame_btn, text="Guardar", width=12, command=actualizar).pack(side="left", padx=8)
        tk.Button(frame_btn, text="Cancelar", width=12,
                  command=ventana_edit.destroy).pack(side="left", padx=8)

    def ver_estatus():
        """Muestra el área total del terreno y el detalle de sus lotes."""
        seleccion = tabla_terrenos.selection()
        if not seleccion:
            messagebox.showwarning("Aviso", "Seleccione un terreno para ver su estatus.")
            return

        valores = tabla_terrenos.item(seleccion[0], "values")
        id_terreno = int(valores[0])

        try:
            conn = conectar_bd()
            cursor = conn.cursor()

            # Datos del terreno
            cursor.execute("""
                SELECT t.NombreTerreno, p.NombreProyecto, t.AreaTotal
                FROM Terrenos t
                INNER JOIN Proyectos p ON t.IdProyecto = p.IdProyecto
                WHERE t.IdTerreno = ?
            """, (id_terreno,))
            info = cursor.fetchone()

            if not info:
                conn.close()
                messagebox.showerror("Error", "El terreno ya no existe.")
                return

            nombre, proyecto, area_total = info

            # Detalle de lotes
            cursor.execute("""
                SELECT NumeroLote, Area, Precio, Estado
                FROM Lotes WHERE IdTerreno = ?
                ORDER BY NumeroLote
            """, (id_terreno,))
            lotes = cursor.fetchall()
            conn.close()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener la información:\n{e}")
            return

        ventana_est = tk.Toplevel(ventana_terrenos)
        ventana_est.title("Estatus del Terreno")
        ventana_est.geometry("720x480")
        ventana_est.transient(ventana_terrenos)
        ventana_est.grab_set()

        # Encabezado de información
        frame_info = tk.Frame(ventana_est)
        frame_info.pack(fill="x", padx=15, pady=10)

        tk.Label(frame_info, text=f"Terreno: {nombre}",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(frame_info, text=f"Proyecto: {proyecto}").pack(anchor="w")
        tk.Label(frame_info, text=f"Área total: {area_total:,.2f} m²",
                 font=("Segoe UI", 11, "bold"), fg="darkgreen").pack(anchor="w", pady=(5, 0))

        # Área ocupada por lotes
        area_lotes = sum(l[1] for l in lotes) if lotes else 0
        area_disponible = float(area_total) - float(area_lotes)

        tk.Label(frame_info,
                 text=f"Área ocupada por lotes: {area_lotes:,.2f} m²",
                 fg="darkred").pack(anchor="w")
        tk.Label(frame_info,
                 text=f"Área disponible: {area_disponible:,.2f} m²",
                 fg="blue").pack(anchor="w")

        # Tabla de lotes
        frame_lotes = tk.Frame(ventana_est)
        frame_lotes.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ("NumeroLote", "Area", "Precio", "Estado")
        tree = ttk.Treeview(frame_lotes, columns=cols, show="headings", height=10)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=150, anchor="center")

        for lote in lotes:
            tree.insert("", "end", values=(
                lote[0],
                f"{lote[1]:,.2f} m²",
                f"L. {lote[2]:,.2f}",
                lote[3]
            ))

        tree.pack(fill="both", expand=True)

        tk.Button(ventana_est, text="Cerrar", width=12,
                  command=ventana_est.destroy).pack(pady=10)

    # ============ CARGA INICIAL ============
    cargar_terrenos()