from database import conectar_bd
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date


def abrir_gestion_lotes(usuario=None):
    global ventana_lotes, tabla_lotes
    rol_de_usuario = usuario.get("NombreRol") if usuario else None
    nombre_usuario = usuario.get("NombreUsuario") if usuario else "Sistema"

    try:
        if ventana_lotes is not None and ventana_lotes.winfo_exists():
            ventana_lotes.lift()
            ventana_lotes.focus_force()
            return
    except (NameError, tk.TclError):
        pass

    ventana_lotes = tk.Toplevel()
    ventana_lotes.geometry("1100x600")
    ventana_lotes.title("Gestión de Lotes")
    ventana_lotes.resizable(False, False)

    mapa_proyectos = {}

    # ---------- Carga de combos ----------
    def cargar_combo_proyectos():
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute("SELECT IdProyecto, NombreProyecto FROM Proyectos ORDER BY NombreProyecto")
            filas = cursor.fetchall()
            conexion.close()
            valores = ["Todos"] + [f[1] for f in filas]
            combo_proyecto["values"] = valores
            if not combo_proyecto.get():
                combo_proyecto.current(0)
            mapa_proyectos.clear()
            for f in filas:
                mapa_proyectos[f[1]] = f[0]
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar proyectos: {e}")

    # ---------- Carga de lotes en tabla ----------
    def cargar_lotes(filtro=None, id_proyecto=None, estado=None):
        for item in tabla_lotes.get_children():
            tabla_lotes.delete(item)
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            query = """
                SELECT L.IdLote, P.NombreProyecto, T.NombreTerreno,
                       L.NumeroLote, L.Area, L.Precio, L.Estado
                FROM Lotes L
                INNER JOIN Terrenos T ON L.IdTerreno = T.IdTerreno
                INNER JOIN Proyectos P ON T.IdProyecto = P.IdProyecto
                WHERE 1 = 1
            """
            params = []
            if id_proyecto:
                query += " AND P.IdProyecto = ?"
                params.append(id_proyecto)
            if estado and estado != "Todos":
                query += " AND L.Estado = ?"
                params.append(estado)
            if filtro:
                query += (" AND (L.NumeroLote LIKE ? OR T.NombreTerreno LIKE ? "
                          "OR P.NombreProyecto LIKE ?)")
                like = f"%{filtro}%"
                params.extend([like, like, like])
            query += " ORDER BY L.IdLote DESC"
            cursor.execute(query, params)
            for fila in cursor.fetchall():
                tabla_lotes.insert("", "end", values=fila)
            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar lotes: {e}")

    # ---------- Acciones ----------
    def accion_buscar():
        texto = entrada_busqueda.get().strip()
        nombre_proy = combo_proyecto.get()
        id_proyecto = mapa_proyectos.get(nombre_proy) if nombre_proy and nombre_proy != "Todos" else None
        estado = combo_estado.get()
        cargar_lotes(texto or None, id_proyecto, estado)

    def accion_mostrar_todos():
        entrada_busqueda.delete(0, "end")
        combo_proyecto.current(0)
        combo_estado.current(0)
        cargar_lotes()

    # ---------- Formulario agregar / editar ----------
    def abrir_formulario_lote(id_lote=None):
        id_terreno_actual = None
        form = tk.Toplevel(ventana_lotes)
        form.title("Editar Lote" if id_lote else "Registrar Lote")
        form.geometry("420x420")
        form.resizable(False, False)
        form.transient(ventana_lotes)
        form.grab_set()

        # Combo terreno
        terrenos_valores = []
        mapa_terrenos = {}
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT T.IdTerreno, P.NombreProyecto, T.NombreTerreno
                FROM Terrenos T
                INNER JOIN Proyectos P ON T.IdProyecto = P.IdProyecto
                ORDER BY P.NombreProyecto, T.NombreTerreno
            """)
            for f in cursor.fetchall():
                etiqueta = f"{f[1]} - {f[2]}"
                terrenos_valores.append(etiqueta)
                mapa_terrenos[etiqueta] = f[0]
            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar terrenos: {e}")

        tk.Label(form, text="Terreno:").pack(anchor="w", padx=15, pady=(15, 0))
        combo_terreno = ttk.Combobox(form, values=terrenos_valores, state="readonly", width=45)
        combo_terreno.pack(padx=15, pady=5, fill="x")

        tk.Label(form, text="Número de lote:").pack(anchor="w", padx=15, pady=(5, 0))
        entry_numero = tk.Entry(form, width=45)
        entry_numero.pack(padx=15, pady=5, fill="x")

        tk.Label(form, text="Área (m²):").pack(anchor="w", padx=15, pady=(5, 0))
        entry_area = tk.Entry(form, width=45)
        entry_area.pack(padx=15, pady=5, fill="x")

        tk.Label(form, text="Precio:").pack(anchor="w", padx=15, pady=(5, 0))
        entry_precio = tk.Entry(form, width=45)
        entry_precio.pack(padx=15, pady=5, fill="x")

        tk.Label(form, text="Estado:").pack(anchor="w", padx=15, pady=(5, 0))
        combo_estado_form = ttk.Combobox(form, state="readonly", width=42,
                                          values=["Disponible", "Reservado", "Vendido", "Entregado"])
        combo_estado_form.current(0)
        combo_estado_form.pack(padx=15, pady=5, fill="x")

        # Si es edición, precargar
        if id_lote:
            try:
                conexion = conectar_bd()
                cursor = conexion.cursor()
                cursor.execute("""
                    SELECT IdTerreno, NumeroLote, Area, Precio, Estado
                    FROM Lotes WHERE IdLote = ?
                """, (id_lote,))
                fila = cursor.fetchone()
                conexion.close()
                if fila:
                    id_terreno_actual = fila[0]
                    for etiqueta, idt in mapa_terrenos.items():
                        if idt == id_terreno_actual:
                            combo_terreno.set(etiqueta)
                            break
                    entry_numero.insert(0, fila[1])
                    entry_area.insert(0, str(fila[2]))
                    entry_precio.insert(0, str(fila[3]))
                    combo_estado_form.set(fila[4])
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar lote: {e}")

        def guardar():
            terreno_sel = combo_terreno.get()
            numero = entry_numero.get().strip()
            area = entry_area.get().strip()
            precio = entry_precio.get().strip()
            estado = combo_estado_form.get()

            if not terreno_sel or not numero or not area or not precio:
                messagebox.showwarning("Validación", "Complete todos los campos.", parent=form)
                return
            try:
                area_v = float(area)
                precio_v = float(precio)
            except ValueError:
                messagebox.showwarning("Validación", "Área y Precio deben ser numéricos.", parent=form)
                return

            id_terreno = mapa_terrenos[terreno_sel]
            try:
                conexion = conectar_bd()
                cursor = conexion.cursor()
                if id_lote:
                    cursor.execute("""
                        UPDATE Lotes
                        SET IdTerreno = ?, NumeroLote = ?, Area = ?, Precio = ?,
                            FechaEditado = ?, EditarPor = ?, Estado = ?
                        WHERE IdLote = ?
                    """, (id_terreno, numero, area_v, precio_v,
                          date.today(), nombre_usuario, estado, id_lote))
                else:
                    cursor.execute("""
                        INSERT INTO Lotes (IdTerreno, NumeroLote, Area, Precio,
                                           FechaEditado, EditarPor, Estado)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (id_terreno, numero, area_v, precio_v,
                          date.today(), nombre_usuario, estado))
                conexion.commit()
                conexion.close()
                messagebox.showinfo("Éxito", "Lote guardado correctamente.", parent=form)
                form.destroy()
                cargar_lotes()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}", parent=form)

        tk.Button(form, text="Guardar", width=15, command=guardar).pack(pady=20)

    def accion_agregar():
        abrir_formulario_lote()

    def accion_editar():
        sel = tabla_lotes.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccione un lote para editar.")
            return
        id_lote = tabla_lotes.item(sel[0])["values"][0]
        abrir_formulario_lote(id_lote)

    def accion_cambiar_estado():
        sel = tabla_lotes.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccione un lote.")
            return
        valores = tabla_lotes.item(sel[0])["values"]
        id_lote, estado_actual = valores[0], valores[6]

        ventana_estado = tk.Toplevel(ventana_lotes)
        ventana_estado.title("Cambiar estado")
        ventana_estado.geometry("300x180")
        ventana_estado.transient(ventana_lotes)
        ventana_estado.grab_set()

        tk.Label(ventana_estado, text=f"Lote ID: {id_lote}\nEstado actual: {estado_actual}",
                 justify="center").pack(pady=15)

        combo_nuevo = ttk.Combobox(ventana_estado, state="readonly",
                                    values=["Disponible", "Reservado", "Vendido", "Entregado"])
        combo_nuevo.set(estado_actual)
        combo_nuevo.pack(pady=5)

        def aplicar():
            nuevo = combo_nuevo.get()
            if nuevo == estado_actual:
                ventana_estado.destroy()
                return
            try:
                conexion = conectar_bd()
                cursor = conexion.cursor()
                cursor.execute("""
                    UPDATE Lotes SET Estado = ?, FechaEditado = ?, EditarPor = ?
                    WHERE IdLote = ?
                """, (nuevo, date.today(), nombre_usuario, id_lote))
                conexion.commit()
                conexion.close()
                messagebox.showinfo("Éxito", "Estado actualizado.")
                ventana_estado.destroy()
                cargar_lotes()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar: {e}")

        tk.Button(ventana_estado, text="Aplicar", command=aplicar).pack(pady=15)

    # ---------- UI ----------
    frame_busqueda = tk.Frame(ventana_lotes, pady=10)
    frame_busqueda.pack(fill="x", padx=10)

    tk.Label(frame_busqueda, text="Buscar:").pack(side="left")
    entrada_busqueda = tk.Entry(frame_busqueda, width=20)
    entrada_busqueda.pack(side="left", padx=5)

    tk.Label(frame_busqueda, text="Proyecto:").pack(side="left", padx=(10, 0))
    combo_proyecto = ttk.Combobox(frame_busqueda, state="readonly", width=18)
    combo_proyecto.pack(side="left", padx=5)

    tk.Label(frame_busqueda, text="Estado:").pack(side="left", padx=(10, 0))
    combo_estado = ttk.Combobox(frame_busqueda, state="readonly", width=12,
                                 values=["Todos", "Disponible", "Reservado", "Vendido", "Entregado"])
    combo_estado.current(0)
    combo_estado.pack(side="left", padx=5)

    tk.Button(frame_busqueda, text="Buscar", command=accion_buscar).pack(side="left", padx=5)
    tk.Button(frame_busqueda, text="Mostrar todos", command=accion_mostrar_todos).pack(side="left", padx=5)

    frame_tabla = tk.Frame(ventana_lotes)
    frame_tabla.pack(fill="both", expand=True, padx=10)

    columnas = ("ID", "Proyecto", "Terreno", "N° Lote", "Área", "Precio", "Estado")
    tabla_lotes = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
    for col in columnas:
        tabla_lotes.heading(col, text=col)
        tabla_lotes.column(col, width=145, anchor="center")
    tabla_lotes.pack(fill="both", expand=True)

    frame_botones = tk.Frame(ventana_lotes, pady=10)
    frame_botones.pack(fill="x", padx=10)

    tk.Button(frame_botones, text="Agregar", width=15, command=accion_agregar).pack(side="left", padx=5)
    tk.Button(frame_botones, text="Editar", width=15, command=accion_editar).pack(side="left", padx=5)
    tk.Button(frame_botones, text="Cambiar estado", width=15, command=accion_cambiar_estado).pack(side="left", padx=5)
    tk.Button(frame_botones, text="Cerrar", width=15, command=ventana_lotes.destroy).pack(side="right", padx=5)

    cargar_combo_proyectos()
    cargar_lotes()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    abrir_gestion_lotes()
    root.mainloop()