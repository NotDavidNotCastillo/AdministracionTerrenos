from database import conectar_bd
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date


def abrir_contrato(usuario=None, datos_reservacion=None):
    global ventana_contrato, tabla_contrato
    rol_de_usuario = usuario.get("NombreRol") if usuario else None
    nombre_usuario = usuario.get("NombreUsuario") if usuario else "Sistema"

    try:
        if ventana_contrato.winfo_exists():
            ventana_contrato.lift()
            ventana_contrato.focus_force()
            return
    except (NameError, tk.TclError):
        pass

    ventana_contrato = tk.Toplevel()
    ventana_contrato.geometry("1100x600")
    ventana_contrato.title("Gestión de Contratos")
    ventana_contrato.resizable(False, False)

    # ---------------- Encabezado ----------------
    frame_top = tk.Frame(ventana_contrato)
    frame_top.pack(fill="x", padx=10, pady=(10, 5))

    tk.Label(frame_top, text="Gestión de Contratos",
             font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=8,
                                              sticky="w", pady=(0, 8))

    tk.Label(frame_top, text="Buscar:").grid(row=1, column=0, padx=3, sticky="e")
    entry_buscar = tk.Entry(frame_top, width=22)
    entry_buscar.grid(row=1, column=1, padx=3)

    tk.Label(frame_top, text="Tipo:").grid(row=1, column=2, padx=3, sticky="e")
    combo_tipo = ttk.Combobox(frame_top, width=15, state="readonly",
                              values=["Todos", "Contado", "Financiado"])
    combo_tipo.current(0)
    combo_tipo.grid(row=1, column=3, padx=3)

    btn_buscar = tk.Button(frame_top, text="Buscar", width=10)
    btn_buscar.grid(row=1, column=4, padx=3)
    btn_mostrar = tk.Button(frame_top, text="Mostrar todos", width=12)
    btn_mostrar.grid(row=1, column=5, padx=3)

    # ---------------- Tabla ----------------
    frame_tabla = tk.Frame(ventana_contrato)
    frame_tabla.pack(fill="both", expand=True, padx=10)

    columnas = ("IdContrato", "Cliente", "Lote", "FechaContrato", "FinContrato",
                "PrecioVenta", "TipoVenta", "Estado")
    tabla_contrato = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=15)
    for c in columnas:
        tabla_contrato.heading(c, text=c)
        tabla_contrato.column(c, width=130, anchor="center")
    tabla_contrato.column("IdContrato", width=80)

    scroll = ttk.Scrollbar(frame_tabla, orient="vertical", command=tabla_contrato.yview)
    tabla_contrato.configure(yscrollcommand=scroll.set)
    tabla_contrato.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    # ---------------- Botones ----------------
    frame_btn = tk.Frame(ventana_contrato)
    frame_btn.pack(fill="x", padx=10, pady=10)

    btn_agregar = tk.Button(frame_btn, text="Crear contrato", width=18)
    btn_cerrar = tk.Button(frame_btn, text="Cerrar", width=12,
                           command=ventana_contrato.destroy)
    btn_agregar.pack(side="left", padx=4)
    btn_cerrar.pack(side="right", padx=4)

    # =========================================================
    #                FUNCIONES INTERNAS
    # =========================================================
    def cargar_contratos(filtro="", tipo=None):
        for i in tabla_contrato.get_children():
            tabla_contrato.delete(i)
        try:
            con = conectar_bd()
            cur = con.cursor()
            sql = """
                SELECT co.IdContrato,
                       c.Nombre + ' ' + c.Apellido,
                       l.NumeroLote,
                       co.FechaContrato, co.FinContrato,
                       co.PrecioVenta, co.TipoVenta, co.Estado
                FROM Contratos co
                INNER JOIN Clientes c ON co.IdCliente = c.IdCliente
                INNER JOIN Lotes l ON co.IdLote = l.IdLote
                WHERE 1=1
            """
            params = []
            if filtro:
                sql += " AND (c.Nombre LIKE ? OR c.Apellido LIKE ? OR l.NumeroLote LIKE ?)"
                params += [f"%{filtro}%", f"%{filtro}%", f"%{filtro}%"]
            if tipo and tipo != "Todos":
                sql += " AND co.TipoVenta = ?"
                params.append(tipo)
            sql += " ORDER BY co.IdContrato DESC"
            cur.execute(sql, params)
            for f in cur.fetchall():
                tabla_contrato.insert("", "end", values=f)
            con.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar contratos:\n{e}")

    def accion_buscar():
        cargar_contratos(entry_buscar.get().strip(), combo_tipo.get())

    def accion_mostrar():
        entry_buscar.delete(0, tk.END)
        combo_tipo.current(0)
        cargar_contratos()

    def accion_crear():
        # Si viene desde reservación, no permitir cambiar cliente/lote
        from_res = datos_reservacion is not None

        clientes = []
        lotes = []
        if not from_res:
            con = conectar_bd()
            cur = con.cursor()
            cur.execute("SELECT IdCliente, Nombre+' '+Apellido, Identidad FROM Clientes WHERE Estado=1")
            clientes = cur.fetchall()
            cur.execute("""
                SELECT l.IdLote, l.NumeroLote, l.Precio, p.NombreProyecto, l.Estado
                FROM Lotes l
                INNER JOIN Terrenos t ON l.IdTerreno=t.IdTerreno
                INNER JOIN Proyectos p ON t.IdProyecto=p.IdProyecto
                WHERE l.Estado IN ('Disponible','Reservado')
                ORDER BY p.NombreProyecto, l.NumeroLote
            """)
            lotes = cur.fetchall()
            con.close()
        else:
            con = conectar_bd()
            cur = con.cursor()
            cur.execute("SELECT IdCliente, Nombre+' '+Apellido, Identidad FROM Clientes WHERE IdCliente=?",
                        (datos_reservacion["IdCliente"],))
            clientes = cur.fetchall()
            cur.execute("""
                SELECT l.IdLote, l.NumeroLote, l.Precio, p.NombreProyecto, l.Estado
                FROM Lotes l
                INNER JOIN Terrenos t ON l.IdTerreno=t.IdTerreno
                INNER JOIN Proyectos p ON t.IdProyecto=p.IdProyecto
                WHERE l.IdLote=?
            """, (datos_reservacion["IdLote"],))
            lotes = cur.fetchall()
            con.close()

        win = tk.Toplevel(ventana_contrato)
        win.title("Nuevo Contrato")
        win.geometry("460x420")
        win.grab_set()

        tk.Label(win, text="Cliente:").grid(row=0, column=0, padx=8, pady=8, sticky="e")
        combo_c = ttk.Combobox(win, width=40, state="readonly",
                               values=[f"{c[0]} - {c[1]} ({c[2]})" for c in clientes])
        combo_c.grid(row=0, column=1, padx=8, pady=8)
        if from_res and clientes:
            combo_c.current(0)
            combo_c.config(state="disabled")

        tk.Label(win, text="Lote:").grid(row=1, column=0, padx=8, pady=8, sticky="e")
        combo_l = ttk.Combobox(win, width=40, state="readonly",
                               values=[f"{l[0]} - {l[3]} / Lote {l[1]} (L {l[2]}) [{l[4]}]" for l in lotes])
        combo_l.grid(row=1, column=1, padx=8, pady=8)
        if from_res and lotes:
            combo_l.current(0)
            combo_l.config(state="disabled")

        tk.Label(win, text="Fecha contrato:").grid(row=2, column=0, padx=8, pady=8, sticky="e")
        entry_fc = tk.Entry(win, width=40)
        entry_fc.insert(0, str(date.today()))
        entry_fc.grid(row=2, column=1, padx=8, pady=8)

        tk.Label(win, text="Fin contrato:").grid(row=3, column=0, padx=8, pady=8, sticky="e")
        entry_ff = tk.Entry(win, width=40)
        entry_ff.insert(0, str(date.today()))
        entry_ff.grid(row=3, column=1, padx=8, pady=8)

        tk.Label(win, text="Precio venta:").grid(row=4, column=0, padx=8, pady=8, sticky="e")
        entry_precio = tk.Entry(win, width=40)
        entry_precio.grid(row=4, column=1, padx=8, pady=8)

        tk.Label(win, text="Tipo de venta:").grid(row=5, column=0, padx=8, pady=8, sticky="e")
        combo_tv = ttk.Combobox(win, width=38, state="readonly",
                                values=["Contado", "Financiado"])
        combo_tv.grid(row=5, column=1, padx=8, pady=8)

        def autocompletar_precio(_evt=None):
            try:
                idx = combo_l.current()
                if idx >= 0:
                    entry_precio.delete(0, tk.END)
                    entry_precio.insert(0, str(lotes[idx][2]))
            except Exception:
                pass
        combo_l.bind("<<ComboboxSelected>>", autocompletar_precio)
        if from_res and lotes:
            autocompletar_precio()

        def guardar():
            if not combo_c.get() or not combo_l.get() or not combo_tv.get():
                messagebox.showwarning("Aviso", "Complete todos los campos.")
                return
            try:
                id_cli = int(combo_c.get().split(" - ")[0])
                id_lote = int(combo_l.get().split(" - ")[0])
                precio = float(entry_precio.get())
                fc = entry_fc.get()
                ff = entry_ff.get()
                tipo = combo_tv.get()
            except ValueError:
                messagebox.showwarning("Aviso", "Verifique los datos.")
                return
            try:
                con = conectar_bd()
                cur = con.cursor()
                cur.execute("""
                    INSERT INTO Contratos (IdCliente, IdLote, FechaContrato,
                                           FinContrato, PrecioVenta, TipoVenta, Estado)
                    VALUES (?, ?, ?, ?, ?, ?, 'Activo')
                """, (id_cli, id_lote, fc, ff, precio, tipo))
                cur.execute("UPDATE Lotes SET Estado='Vendido' WHERE IdLote=?", (id_lote,))
                if from_res:
                    cur.execute("UPDATE Reservaciones SET Estado='Convertida' WHERE IdReservacion=?",
                                (datos_reservacion["IdReservacion"],))
                con.commit()
                con.close()
                messagebox.showinfo("Éxito", "Contrato creado correctamente.")
                win.destroy()
                cargar_contratos()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear el contrato:\n{e}")

        tk.Button(win, text="Guardar", width=12, command=guardar).grid(row=6, column=0, pady=15)
        tk.Button(win, text="Cancelar", width=12, command=win.destroy).grid(row=6, column=1, pady=15)

    btn_buscar.config(command=accion_buscar)
    btn_mostrar.config(command=accion_mostrar)
    btn_agregar.config(command=accion_crear)

    cargar_contratos()

    # Si viene desde reservación, abrir automáticamente el formulario
    if datos_reservacion:
        ventana_contrato.after(200, accion_crear)

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    abrir_contrato()
    root.mainloop()