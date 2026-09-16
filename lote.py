from database import conectar_bd
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date


def abrir_lote(usuario=None):
    global ventana_lote, tabla_lote
    rol_de_usuario = usuario.get("NombreRol") if usuario else None
    nombre_usuario = usuario.get("NombreUsuario") if usuario else "Sistema"

    try:
        if ventana_lote.winfo_exists():
            ventana_lote.lift()
            ventana_lote.focus_force()
            return
    except (NameError, tk.TclError):
        pass

    ventana_lote = tk.Toplevel()
    ventana_lote.geometry("1100x600")
    ventana_lote.title("Gestión de Lotes")
    ventana_lote.resizable(False, False)

    # ---------------- Encabezado / Búsqueda ----------------
    frame_top = tk.Frame(ventana_lote)
    frame_top.pack(fill="x", padx=10, pady=(10, 5))

    tk.Label(frame_top, text="Gestión de Lotes",
             font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=8,
                                              sticky="w", pady=(0, 8))

    tk.Label(frame_top, text="Buscar:").grid(row=1, column=0, padx=3, sticky="e")
    entry_buscar = tk.Entry(frame_top, width=20)
    entry_buscar.grid(row=1, column=1, padx=3)

    tk.Label(frame_top, text="Proyecto:").grid(row=1, column=2, padx=3, sticky="e")
    combo_proyecto = ttk.Combobox(frame_top, width=22, state="readonly")
    combo_proyecto.grid(row=1, column=3, padx=3)

    tk.Label(frame_top, text="Estado:").grid(row=1, column=4, padx=3, sticky="e")
    combo_estado = ttk.Combobox(
        frame_top, width=15, state="readonly",
        values=["Todos", "Disponible", "Reservado", "Vendido", "Entregado"]
    )
    combo_estado.current(0)
    combo_estado.grid(row=1, column=5, padx=3)

    btn_buscar = tk.Button(frame_top, text="Buscar", width=10)
    btn_buscar.grid(row=1, column=6, padx=3)
    btn_mostrar = tk.Button(frame_top, text="Mostrar todos", width=12)
    btn_mostrar.grid(row=1, column=7, padx=3)

    # ---------------- Tabla ----------------
    frame_tabla = tk.Frame(ventana_lote)
    frame_tabla.pack(fill="both", expand=True, padx=10)

    columnas = ("IdLote", "Proyecto", "Terreno", "NumeroLote", "Area", "Precio",
                "FechaEditado", "EditarPor", "Estado")
    tabla_lote = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=15)
    for c in columnas:
        tabla_lote.heading(c, text=c)
        tabla_lote.column(c, width=110, anchor="center")
    tabla_lote.column("IdLote", width=55, anchor="center")
    tabla_lote.column("NumeroLote", width=90, anchor="center")

    scroll = ttk.Scrollbar(frame_tabla, orient="vertical", command=tabla_lote.yview)
    tabla_lote.configure(yscrollcommand=scroll.set)
    tabla_lote.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    # ---------------- Botones inferiores ----------------
    frame_btn = tk.Frame(ventana_lote)
    frame_btn.pack(fill="x", padx=10, pady=10)

    btn_agregar = tk.Button(frame_btn, text="Agregar", width=14)
    btn_editar = tk.Button(frame_btn, text="Editar", width=14)
    btn_estado = tk.Button(frame_btn, text="Cambiar estado", width=14)
    btn_cerrar = tk.Button(frame_btn, text="Cerrar", width=12,
                           command=ventana_lote.destroy)
    btn_agregar.pack(side="left", padx=4)
    btn_editar.pack(side="left", padx=4)
    btn_estado.pack(side="left", padx=4)
    btn_cerrar.pack(side="right", padx=4)

    # =========================================================
    #                 FUNCIONES INTERNAS
    # =========================================================
    def cargar_proyectos():
        try:
            con = conectar_bd()
            cur = con.cursor()
            cur.execute("SELECT IdProyecto, NombreProyecto FROM Proyectos ORDER BY NombreProyecto")
            datos = cur.fetchall()
            con.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar proyectos:\n{e}")
            datos = []
        combo_proyecto["values"] = ["Todos"] + [f"{d[0]} - {d[1]}" for d in datos]
        combo_proyecto.current(0)

    def cargar_lotes(filtro="", id_proyecto=None, estado=None):
        for i in tabla_lote.get_children():
            tabla_lote.delete(i)
        try:
            con = conectar_bd()
            cur = con.cursor()
            sql = """
                SELECT l.IdLote, p.NombreProyecto, t.NombreTerreno,
                       l.NumeroLote, l.Area, l.Precio,
                       l.FechaEditado, l.EditarPor, l.Estado
                FROM Lotes l
                INNER JOIN Terrenos t ON l.IdTerreno = t.IdTerreno
                INNER JOIN Proyectos p ON t.IdProyecto = p.IdProyecto
                WHERE 1=1
            """
            params = []

            if filtro:
                sql += " AND ( l.NumeroLote LIKE ? OR t.NombreTerreno LIKE ? OR p.NombreProyecto LIKE ? )"
                params += [f"%{filtro}%", f"%{filtro}%", f"%{filtro}%"]

            if id_proyecto:
                sql += " AND p.IdProyecto = ? "
                params.append(id_proyecto)

            if estado and estado != "Todos":
                sql += " AND l.Estado = ? "
                params.append(estado)
            sql += " ORDER BY l.IdLote"
            cur.execute(sql, params)
            for fila in cur.fetchall():
                tabla_lote.insert("", "end", values=fila)
            con.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar lotes:\n{e}")

    def accion_buscar():
        id_proy = None
        if combo_proyecto.get() and combo_proyecto.get() != "Todos":
            id_proy = int(combo_proyecto.get().split(" - ")[0])
        
        cargar_lotes(entry_buscar.get().strip(), id_proy, combo_estado.get())

    def accion_mostrar_todos():
        entry_buscar.delete(0, tk.END)
        combo_proyecto.current(0)
        combo_estado.current(0)
        cargar_lotes()

    def obtener_terrenos():
        try:
            con = conectar_bd()
            cur = con.cursor()
            cur.execute("""
                SELECT t.IdTerreno, t.NombreTerreno, t.AreaTotal,
                       t.IdProyecto, p.NombreProyecto
                FROM Terrenos t
                INNER JOIN Proyectos p ON t.IdProyecto = p.IdProyecto
                ORDER BY p.NombreProyecto, t.NombreTerreno
            """)
            d = cur.fetchall()
            con.close()
            return d
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar terrenos:\n{e}")
            return []

    def validar_area(id_terreno, area_nueva, id_lote_excluir=None):
        """Verifica que la suma de áreas de lotes no supere el área del terreno."""
        try:
            con = conectar_bd()
            cur = con.cursor()
            cur.execute("SELECT AreaTotal FROM Terrenos WHERE IdTerreno = ?", (id_terreno,))
            row = cur.fetchone()
            if not row:
                con.close()
                return False, "El terreno seleccionado no existe."
            area_total = float(row[0])

            sql = "SELECT ISNULL(SUM(Area),0) FROM Lotes WHERE IdTerreno = ?"
            params = [id_terreno]
            if id_lote_excluir is not None:
                sql += " AND IdLote <> ?"
                params.append(id_lote_excluir)
            cur.execute(sql, params)
            area_usada = float(cur.fetchone()[0])
            con.close()

            if area_usada + float(area_nueva) > area_total:
                return False, (f"El área excede el total del terreno.\n"
                               f"Área del terreno: {area_total}\n"
                               f"Área ya usada: {area_usada}\n"
                               f"Disponible: {area_total - area_usada}")
            return True, ""
        except Exception as e:
            return False, f"Error al validar área: {e}"

    def formulario_lote(lote=None):
        """lote = tupla de la fila seleccionada (None para agregar)."""
        win = tk.Toplevel(ventana_lote)
        win.title("Editar Lote" if lote else "Registrar Lote")
        win.geometry("420x420")
        win.resizable(False, False)
        win.grab_set()

        terrenos = obtener_terrenos()

        tk.Label(win, text="Terreno:").grid(row=0, column=0, padx=8, pady=6, sticky="e")
        combo_t = ttk.Combobox(win, width=35, state="readonly",
                               values=[f"{t[0]} - {t[4]} / {t[1]} (Área {t[2]})" for t in terrenos])
        combo_t.grid(row=0, column=1, padx=8, pady=6)

        tk.Label(win, text="Número de lote:").grid(row=1, column=0, padx=8, pady=6, sticky="e")
        entry_num = tk.Entry(win, width=35)
        entry_num.grid(row=1, column=1, padx=8, pady=6)

        tk.Label(win, text="Área:").grid(row=2, column=0, padx=8, pady=6, sticky="e")
        entry_area = tk.Entry(win, width=35)
        entry_area.grid(row=2, column=1, padx=8, pady=6)

        tk.Label(win, text="Precio:").grid(row=3, column=0, padx=8, pady=6, sticky="e")
        entry_precio = tk.Entry(win, width=35)
        entry_precio.grid(row=3, column=1, padx=8, pady=6)

        tk.Label(win, text="Estado:").grid(row=4, column=0, padx=8, pady=6, sticky="e")
        combo_e = ttk.Combobox(win, width=32, state="readonly",
                               values=["Disponible", "Reservado", "Vendido", "Entregado"])
        combo_e.grid(row=4, column=1, padx=8, pady=6)

        if lote:
            # lote = (IdLote, Proyecto, Terreno, NumeroLote, Area, Precio, FechaEditado, EditarPor, Estado)
            id_lote = lote[0]
            try:
                con = conectar_bd()
                cur = con.cursor()
                cur.execute("SELECT IdTerreno FROM Lotes WHERE IdLote=?", (id_lote,))
                id_terr = cur.fetchone()[0]
                con.close()
                for i, t in enumerate(terrenos):
                    if t[0] == id_terr:
                        combo_t.current(i)
                        break
            except Exception:
                pass
            entry_num.insert(0, lote[3])
            entry_area.insert(0, str(lote[4]))
            entry_precio.insert(0, str(lote[5]))
            combo_e.set(lote[8])

        def guardar():
            if not combo_t.get():
                messagebox.showwarning("Aviso", "Seleccione un terreno.")
                return
            try:
                id_terreno = int(combo_t.get().split(" - ")[0])
                numero = entry_num.get().strip()
                area = float(entry_area.get())
                precio = float(entry_precio.get())
                estado = combo_e.get()
                if not numero or not estado:
                    raise ValueError("Complete todos los campos.")
            except ValueError as e:
                messagebox.showwarning("Datos inválidos", str(e))
                return

            id_excluir = lote[0] if lote else None
            ok, msg = validar_area(id_terreno, area, id_excluir)
            if not ok:
                messagebox.showerror("Área excedida", msg)
                return

            try:
                con = conectar_bd()
                cur = con.cursor()
                if lote:
                    cur.execute("""
                        UPDATE Lotes
                        SET IdTerreno=?, NumeroLote=?, Area=?, Precio=?,
                            FechaEditado=?, EditarPor=?, Estado=?
                        WHERE IdLote=?
                    """, (id_terreno, numero, area, precio,
                          date.today(), nombre_usuario, estado, lote[0]))
                else:
                    cur.execute("""
                        INSERT INTO Lotes
                            (IdTerreno, NumeroLote, Area, Precio,
                             FechaEditado, EditarPor, Estado)
                        VALUES ( ? , ? , ? , ? , ? , ? , ? )
                    """, (id_terreno, numero, area, precio,
                          date.today(), nombre_usuario, estado))
                con.commit()
                con.close()
                messagebox.showinfo("Éxito", "Lote guardado correctamente.")
                win.destroy()
                cargar_lotes()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

        tk.Button(win, text="Guardar", width=12, command=guardar).grid(
            row=5, column=0, padx=8, pady=15)
        tk.Button(win, text="Cancelar", width=12, command=win.destroy).grid(
            row=5, column=1, padx=8, pady=15, sticky="e")

    def accion_agregar():
        formulario_lote(None)

    def accion_editar():
        sel = tabla_lote.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccione un lote.")
            return
        valores = tabla_lote.item(sel[0], "values")
        formulario_lote(valores)

    def accion_cambiar_estado():
        sel = tabla_lote.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccione un lote.")
            return
        valores = tabla_lote.item(sel[0], "values")
        win = tk.Toplevel(ventana_lote)
        win.title("Cambiar estado")
        win.geometry("300x160")
        win.grab_set()
        tk.Label(win, text=f"Lote: {valores[3]}",
                 font=("Arial", 11, "bold")).pack(pady=8)
        combo = ttk.Combobox(win, state="readonly",
                             values=["Disponible", "Reservado", "Vendido", "Entregado"])
        combo.set(valores[8])
        combo.pack(pady=5)

        def aplicar():
            try:
                con = conectar_bd()
                cur = con.cursor()
                cur.execute("""
                    UPDATE Lotes SET Estado=?, FechaEditado=?, EditarPor=?
                    WHERE IdLote=?
                """, (combo.get(), date.today(), nombre_usuario, valores[0]))
                con.commit()
                con.close()
                win.destroy()
                cargar_lotes()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cambiar el estado:\n{e}")

        tk.Button(win, text="Aplicar", command=aplicar).pack(pady=10)

    # ---------------- Enlaces ----------------
    btn_buscar.config(command=accion_buscar)
    btn_mostrar.config(command=accion_mostrar_todos)
    btn_agregar.config(command=accion_agregar)
    btn_editar.config(command=accion_editar)
    btn_estado.config(command=accion_cambiar_estado)

    # Carga inicial
    cargar_proyectos()
    cargar_lotes()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    abrir_lote()
    root.mainloop()