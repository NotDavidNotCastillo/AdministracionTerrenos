from database import conectar_bd
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date


def abrir_reservacion(usuario=None):
    global ventana_reservacion, tabla_reservacion
    rol_de_usuario = usuario.get("NombreRol") if usuario else None
    nombre_usuario = usuario.get("NombreUsuario") if usuario else "Sistema"

    try:
        if ventana_reservacion.winfo_exists():
            ventana_reservacion.lift()
            ventana_reservacion.focus_force()
            return
    except (NameError, tk.TclError):
        pass

    ventana_reservacion = tk.Toplevel()
    ventana_reservacion.geometry("1100x600")
    ventana_reservacion.title("Gestión de Reservaciones")
    ventana_reservacion.resizable(False, False)

    # ---------------- Encabezado ----------------
    frame_top = tk.Frame(ventana_reservacion)
    frame_top.pack(fill="x", padx=10, pady=(10, 5))

    tk.Label(frame_top, text="Gestión de Reservaciones",
             font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=8,
                                              sticky="w", pady=(0, 8))

    tk.Label(frame_top, text="Buscar:").grid(row=1, column=0, padx=3, sticky="e")
    entry_buscar = tk.Entry(frame_top, width=22)
    entry_buscar.grid(row=1, column=1, padx=3)

    tk.Label(frame_top, text="Estado:").grid(row=1, column=2, padx=3, sticky="e")
    combo_estado = ttk.Combobox(frame_top, width=15, state="readonly",
                                values=["Todos", "Activa", "Cancelada", "Convertida"])
    combo_estado.current(0)
    combo_estado.grid(row=1, column=3, padx=3)

    btn_buscar = tk.Button(frame_top, text="Buscar", width=10)
    btn_buscar.grid(row=1, column=4, padx=3)
    btn_mostrar = tk.Button(frame_top, text="Mostrar todos", width=12)
    btn_mostrar.grid(row=1, column=5, padx=3)

    # ---------------- Tabla ----------------
    frame_tabla = tk.Frame(ventana_reservacion)
    frame_tabla.pack(fill="both", expand=True, padx=10)

    columnas = ("IdReservacion", "Cliente", "Lote", "FechaReservacion",
                "MontoReserva", "Estado")
    tabla_reservacion = ttk.Treeview(frame_tabla, columns=columnas,
                                     show="headings", height=15)
    for c in columnas:
        tabla_reservacion.heading(c, text=c)
        tabla_reservacion.column(c, width=150, anchor="center")
    tabla_reservacion.column("IdReservacion", width=80)

    scroll = ttk.Scrollbar(frame_tabla, orient="vertical",
                           command=tabla_reservacion.yview)
    tabla_reservacion.configure(yscrollcommand=scroll.set)
    tabla_reservacion.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    # ---------------- Botones ----------------
    frame_btn = tk.Frame(ventana_reservacion)
    frame_btn.pack(fill="x", padx=10, pady=10)

    btn_agregar = tk.Button(frame_btn, text="Crear reservación", width=18)
    btn_cancelar = tk.Button(frame_btn, text="Cancelar reservación", width=18)
    btn_convertir = tk.Button(frame_btn, text="Convertir a contrato", width=20)
    btn_cerrar = tk.Button(frame_btn, text="Cerrar", width=12,
                           command=ventana_reservacion.destroy)
    btn_agregar.pack(side="left", padx=4)
    btn_cancelar.pack(side="left", padx=4)
    btn_convertir.pack(side="left", padx=4)
    btn_cerrar.pack(side="right", padx=4)

    # =========================================================
    #                FUNCIONES INTERNAS
    # =========================================================
    def cargar_reservaciones(filtro="", estado=None):
        for i in tabla_reservacion.get_children():
            tabla_reservacion.delete(i)
        try:
            con = conectar_bd()
            cur = con.cursor()
            sql = """
                SELECT r.IdReservacion,
                       c.Nombre + ' ' + c.Apellido AS Cliente,
                       l.NumeroLote,
                       r.FechaReservacion, r.MontoReserva, r.Estado
                FROM Reservaciones r
                INNER JOIN Clientes c ON r.IdCliente = c.IdCliente
                INNER JOIN Lotes l ON r.IdLote = l.IdLote
                WHERE 1=1
            """
            params = []
            if filtro:
                sql += " AND (c.Nombre LIKE ? OR c.Apellido LIKE ? OR l.NumeroLote LIKE ?)"
                params += [f"%{filtro}%", f"%{filtro}%", f"%{filtro}%"]
            if estado and estado != "Todos":
                sql += " AND r.Estado = ?"
                params.append(estado)
            sql += " ORDER BY r.IdReservacion DESC"
            cur.execute(sql, params)
            for fila in cur.fetchall():
                tabla_reservacion.insert("", "end", values=fila)
            con.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar reservaciones:\n{e}")

    def cargar_clientes():
        con = conectar_bd()
        cur = con.cursor()
        cur.execute("SELECT IdCliente, Nombre+' '+Apellido, Identidad FROM Clientes WHERE Estado=1 ORDER BY Nombre")
        d = cur.fetchall()
        con.close()
        return d

    def cargar_lotes_disponibles():
        con = conectar_bd()
        cur = con.cursor()
        cur.execute("""
            SELECT l.IdLote, l.NumeroLote, l.Precio, p.NombreProyecto
            FROM Lotes l
            INNER JOIN Terrenos t ON l.IdTerreno=t.IdTerreno
            INNER JOIN Proyectos p ON t.IdProyecto=p.IdProyecto
            WHERE l.Estado = 'Disponible'
            ORDER BY p.NombreProyecto, l.NumeroLote
        """)
        d = cur.fetchall()
        con.close()
        return d

    def accion_buscar():
        cargar_reservaciones(entry_buscar.get().strip(), combo_estado.get())

    def accion_mostrar():
        entry_buscar.delete(0, tk.END)
        combo_estado.current(0)
        cargar_reservaciones()

    def accion_crear():
        clientes = cargar_clientes()
        lotes = cargar_lotes_disponibles()
        if not clientes or not lotes:
            messagebox.showwarning("Aviso", "Debe haber clientes y lotes disponibles.")
            return

        win = tk.Toplevel(ventana_reservacion)
        win.title("Nueva Reservación")
        win.geometry("430x320")
        win.grab_set()

        tk.Label(win, text="Cliente:").grid(row=0, column=0, padx=8, pady=8, sticky="e")
        combo_c = ttk.Combobox(win, width=38, state="readonly",
                               values=[f"{c[0]} - {c[1]} ({c[2]})" for c in clientes])
        combo_c.grid(row=0, column=1, padx=8, pady=8)

        tk.Label(win, text="Lote:").grid(row=1, column=0, padx=8, pady=8, sticky="e")
        combo_l = ttk.Combobox(win, width=38, state="readonly",
                               values=[f"{l[0]} - {l[3]} / Lote {l[1]} (L {l[2]})" for l in lotes])
        combo_l.grid(row=1, column=1, padx=8, pady=8)

        tk.Label(win, text="Fecha reservación:").grid(row=2, column=0, padx=8, pady=8, sticky="e")
        entry_f = tk.Entry(win, width=38)
        entry_f.insert(0, str(date.today()))
        entry_f.grid(row=2, column=1, padx=8, pady=8)

        tk.Label(win, text="Monto reserva:").grid(row=3, column=0, padx=8, pady=8, sticky="e")
        entry_m = tk.Entry(win, width=38)
        entry_m.grid(row=3, column=1, padx=8, pady=8)

        def guardar():
            if not combo_c.get() or not combo_l.get():
                messagebox.showwarning("Aviso", "Seleccione cliente y lote.")
                return
            try:
                id_cli = int(combo_c.get().split(" - ")[0])
                id_lote = int(combo_l.get().split(" - ")[0])
                monto = float(entry_m.get())
                fecha = entry_f.get()
            except ValueError:
                messagebox.showwarning("Aviso", "Verifique los datos.")
                return
            try:
                con = conectar_bd()
                cur = con.cursor()
                cur.execute("""
                    INSERT INTO Reservaciones (IdCliente, IdLote, FechaReservacion,
                                               MontoReserva, Estado)
                    VALUES (?, ?, ?, ?, 'Activa')
                """, (id_cli, id_lote, fecha, monto))
                cur.execute("UPDATE Lotes SET Estado='Reservado' WHERE IdLote=?", (id_lote,))
                con.commit()
                con.close()
                messagebox.showinfo("Éxito", "Reservación creada.")
                win.destroy()
                cargar_reservaciones()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear:\n{e}")

        tk.Button(win, text="Guardar", width=12, command=guardar).grid(row=4, column=0, pady=15)
        tk.Button(win, text="Cancelar", width=12, command=win.destroy).grid(row=4, column=1, pady=15)

    def accion_cancelar():
        sel = tabla_reservacion.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccione una reservación.")
            return
        v = tabla_reservacion.item(sel[0], "values")
        if v[5] != "Activa":
            messagebox.showwarning("Aviso", "Solo se pueden cancelar reservaciones activas.")
            return
        if not messagebox.askyesno("Confirmar", "¿Cancelar esta reservación?"):
            return
        try:
            con = conectar_bd()
            cur = con.cursor()
            cur.execute("SELECT IdLote FROM Reservaciones WHERE IdReservacion=?", (v[0],))
            id_lote = cur.fetchone()[0]
            cur.execute("UPDATE Reservaciones SET Estado='Cancelada' WHERE IdReservacion=?", (v[0],))
            cur.execute("UPDATE Lotes SET Estado='Disponible' WHERE IdLote=?", (id_lote,))
            con.commit()
            con.close()
            cargar_reservaciones()
            messagebox.showinfo("Éxito", "Reservación cancelada.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cancelar:\n{e}")

    def accion_convertir():
        sel = tabla_reservacion.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccione una reservación.")
            return
        v = tabla_reservacion.item(sel[0], "values")
        if v[5] != "Activa":
            messagebox.showwarning("Aviso", "Solo se pueden convertir reservaciones activas.")
            return
        try:
            con = conectar_bd()
            cur = con.cursor()
            cur.execute("""
                SELECT IdCliente, IdLote FROM Reservaciones WHERE IdReservacion=?
            """, (v[0],))
            id_cliente, id_lote = cur.fetchone()
            con.close()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        # Importación local para evitar dependencia circular
        from contrato import abrir_contrato
        abrir_contrato(usuario, datos_reservacion={
            "IdReservacion": v[0],
            "IdCliente": id_cliente,
            "IdLote": id_lote,
            "MontoReserva": v[4],
        })
        cargar_reservaciones()

    # Enlaces
    btn_buscar.config(command=accion_buscar)
    btn_mostrar.config(command=accion_mostrar)
    btn_agregar.config(command=accion_crear)
    btn_cancelar.config(command=accion_cancelar)
    btn_convertir.config(command=accion_convertir)

    cargar_reservaciones()