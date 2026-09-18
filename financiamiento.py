from database import conectar_bd
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import calendar


def sumar_meses(fecha, meses):
    m = fecha.month - 1 + meses
    y = fecha.year + m // 12
    m = m % 12 + 1
    d = min(fecha.day, calendar.monthrange(y, m)[1])
    return date(y, m, d)


def abrir_financiamiento(usuario=None):
    global ventana_financiamiento, tabla_financiamiento
    rol_de_usuario = usuario.get("NombreRol") if usuario else None
    nombre_usuario = usuario.get("NombreUsuario") if usuario else "Sistema"

    try:
        if ventana_financiamiento.winfo_exists():
            ventana_financiamiento.lift()
            ventana_financiamiento.focus_force()
            return
    except (NameError, tk.TclError):
        pass

    ventana_financiamiento = tk.Toplevel()
    ventana_financiamiento.geometry("1100x600")
    ventana_financiamiento.title("Gestión de Financiamientos")
    ventana_financiamiento.resizable(False, False)

    # ---------------- Encabezado ----------------
    frame_top = tk.Frame(ventana_financiamiento)
    frame_top.pack(fill="x", padx=10, pady=(10, 5))

    tk.Label(frame_top, text="Gestión de Financiamientos",
             font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=8,
                                              sticky="w", pady=(0, 8))

    tk.Label(frame_top, text="Buscar:").grid(row=1, column=0, padx=3, sticky="e")
    entry_buscar = tk.Entry(frame_top, width=22)
    entry_buscar.grid(row=1, column=1, padx=3)

    tk.Label(frame_top, text="Estado:").grid(row=1, column=2, padx=3, sticky="e")
    combo_estado = ttk.Combobox(frame_top, width=15, state="readonly",
                                values=["Todos", "Activo", "Cancelado", "Finalizado"])
    combo_estado.current(0)
    combo_estado.grid(row=1, column=3, padx=3)

    btn_buscar = tk.Button(frame_top, text="Buscar", width=10)
    btn_buscar.grid(row=1, column=4, padx=3)
    btn_mostrar = tk.Button(frame_top, text="Mostrar todos", width=12)
    btn_mostrar.grid(row=1, column=5, padx=3)

    # ---------------- Tabla ----------------
    frame_tabla = tk.Frame(ventana_financiamiento)
    frame_tabla.pack(fill="both", expand=True, padx=10)

    columnas = ("IdFinanciamiento", "IdContrato", "Cliente", "MontoFinanciado",
                "TasaInteres (%)", "PlazoMeses", "FechaInicio", "Estado")
    tabla_financiamiento = ttk.Treeview(frame_tabla, columns=columnas,
                                        show="headings", height=15)
    for c in columnas:
        tabla_financiamiento.heading(c, text=c)
        tabla_financiamiento.column(c, width=130, anchor="center")
    tabla_financiamiento.column("IdFinanciamiento", width=110)

    scroll = ttk.Scrollbar(frame_tabla, orient="vertical",
                           command=tabla_financiamiento.yview)
    tabla_financiamiento.configure(yscrollcommand=scroll.set)
    tabla_financiamiento.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    # ---------------- Botones ----------------
    frame_btn = tk.Frame(ventana_financiamiento)
    frame_btn.pack(fill="x", padx=10, pady=10)

    btn_agregar = tk.Button(frame_btn, text="Crear plan", width=16)
    btn_ver_cuotas = tk.Button(frame_btn, text="Ver cuotas", width=14)
    btn_cerrar = tk.Button(frame_btn, text="Cerrar", width=12,
                           command=ventana_financiamiento.destroy)
    btn_agregar.pack(side="left", padx=4)
    btn_ver_cuotas.pack(side="left", padx=4)
    btn_cerrar.pack(side="right", padx=4)

    # =========================================================
    #                FUNCIONES INTERNAS
    # =========================================================
    def cargar_financiamientos(filtro="", estado=None):
        for i in tabla_financiamiento.get_children():
            tabla_financiamiento.delete(i)
        try:
            con = conectar_bd()
            cur = con.cursor()
            sql = """
                SELECT f.IdFinanciamiento, f.IdContrato,
                       c.Nombre + ' ' + c.Apellido,
                       f.MontoFinanciado, f.TasaInteres, f.PlazoMeses,
                       f.FechaInicio, f.Estado
                FROM Financiamientos f
                INNER JOIN Contratos co ON f.IdContrato = co.IdContrato
                INNER JOIN Clientes c ON co.IdCliente = c.IdCliente
                WHERE 1=1
            """
            params = []
            if filtro:
                sql += " AND (c.Nombre LIKE ? OR c.Apellido LIKE ? OR CAST(f.IdContrato AS VARCHAR) LIKE ?)"
                params += [f"%{filtro}%", f"%{filtro}%", f"%{filtro}%"]
            if estado and estado != "Todos":
                sql += " AND f.Estado = ?"
                params.append(estado)
            sql += " ORDER BY f.IdFinanciamiento DESC"
            cur.execute(sql, params)
            for fila in cur.fetchall():
                tabla_financiamiento.insert("", "end", values=(
                    fila[0], # Id Financiamiento
                    fila[1], # Id contrato
                    fila[2], # Cliente
                    float(fila[3]) if fila[3] is not None else 0.0, # Monto Financiado
                    fila[4], # Tasa de Interes
                    fila[5], # Plazo de meses
                    fila[6].strftime("%Y-%m-%d")
                        if hasattr (fila[6], "strftime") else fila[6], # Fecha de Inicio
                    fila[7], # Estado
                ))
                print(fila)
            con.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar financiamientos:\n{e}")

    def accion_buscar():
        cargar_financiamientos(entry_buscar.get().strip(), combo_estado.get())

    def accion_mostrar():
        entry_buscar.delete(0, tk.END)
        combo_estado.current(0)
        cargar_financiamientos()

    def contratos_financiables():
        con = conectar_bd()
        cur = con.cursor()
        cur.execute("""
            SELECT co.IdContrato,
                   c.Nombre + ' ' + c.Apellido,
                   l.NumeroLote,
                   co.PrecioVenta
            FROM Contratos co
            INNER JOIN Clientes c ON co.IdCliente = c.IdCliente
            INNER JOIN Lotes l ON co.IdLote = l.IdLote
            LEFT JOIN Financiamientos f ON f.IdContrato = co.IdContrato
            WHERE co.TipoVenta = 'Financiado'
              AND f.IdFinanciamiento IS NULL
              AND co.Estado = 'Activo'
            ORDER BY co.IdContrato DESC
        """)
        d = cur.fetchall()
        con.close()
        return d

    def accion_crear():
        contratos = contratos_financiables()
        if not contratos:
            messagebox.showwarning(
                "Aviso",
                "No hay contratos del tipo 'Financiado' sin plan de financiamiento."
            )
            return

        win = tk.Toplevel(ventana_financiamiento)
        win.title("Nuevo Plan de Financiamiento")
        win.geometry("460x400")
        win.grab_set()

        tk.Label(win, text="Contrato:").grid(row=0, column=0, padx=8, pady=8, sticky="e")
        combo_co = ttk.Combobox(win, width=42, state="readonly",
                                values=[f"{c[0]} - {c[1]} (Lote {c[2]}, Precio L {c[3]})"
                                        for c in contratos])
        combo_co.grid(row=0, column=1, padx=8, pady=8)

        tk.Label(win, text="Monto financiado:").grid(row=1, column=0, padx=8, pady=8, sticky="e")
        entry_m = tk.Entry(win, width=42)
        entry_m.grid(row=1, column=1, padx=8, pady=8)

        tk.Label(win, text="Tasa de interés (% anual):").grid(row=2, column=0, padx=8, pady=8, sticky="e")
        entry_t = tk.Entry(win, width=42)
        entry_t.insert(0, "0")
        entry_t.grid(row=2, column=1, padx=8, pady=8)

        tk.Label(win, text="Plazo (meses):").grid(row=3, column=0, padx=8, pady=8, sticky="e")
        entry_p = tk.Entry(win, width=42)
        entry_p.grid(row=3, column=1, padx=8, pady=8)

        tk.Label(win, text="Fecha inicio:").grid(row=4, column=0, padx=8, pady=8, sticky="e")
        entry_f = tk.Entry(win, width=42)
        entry_f.insert(0, str(date.today()))
        entry_f.grid(row=4, column=1, padx=8, pady=8)

        def autocompletar(_evt=None):
            idx = combo_co.current()
            if idx >= 0:
                entry_m.delete(0, tk.END)
                entry_m.insert(0, str(contratos[idx][3]))
        combo_co.bind("<<ComboboxSelected>>", autocompletar)

        def guardar():
            if not combo_co.get():
                messagebox.showwarning("Aviso", "Seleccione un contrato.")
                return
            try:
                id_contrato = int(combo_co.get().split(" - ")[0])
                monto = float(entry_m.get())
                tasa = float(entry_t.get())
                plazo = int(entry_p.get())
                fecha_inicio = date.fromisoformat(entry_f.get())
                if monto <= 0 or plazo <= 0:
                    raise ValueError("Monto y plazo deben ser mayores a cero.")
            except ValueError as e:
                messagebox.showwarning("Datos inválidos", f"Verifique los datos.\n{e}")
                return

            # Cálculo de cuotas (sistema francés)
            i = (tasa / 100.0) / 12.0
            if i > 0:
                cuota = monto * i * (1 + i) ** plazo / ((1 + i) ** plazo - 1)
            else:
                cuota = monto / plazo
            cuota = round(cuota, 2)

            try:
                con = conectar_bd()
                cur = con.cursor()
                cur.execute("""
                    INSERT INTO Financiamientos
                        (IdContrato, MontoFinanciado, TasaInteres, PlazoMeses,
                         FechaInicio, Estado)
                    OUTPUT INSERTED.IdFinanciamiento
                    VALUES (?, ?, ?, ?, ?, 'Activo')
                """, (id_contrato, monto, tasa, plazo, fecha_inicio))

                id_fin = cur.fetchone()[0]

                for k in range(1, plazo + 1):
                    fv = sumar_meses(fecha_inicio, k)
                    cur.execute("""
                        INSERT INTO Cuotas
                            (IdFinanciamiento, NumeroCuota, FechaVencimiento,
                             Monto, Estado)
                        VALUES (?, ?, ?, ?, 'Pendiente')
                    """, (id_fin, k, fv, cuota))

                con.commit()
                con.close()
                messagebox.showinfo(
                    "Éxito",
                    f"Plan creado. Cuota mensual estimada: L {cuota}"
                )
                win.destroy()
                cargar_financiamientos()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear el plan:\n{e}")

        tk.Button(win, text="Guardar", width=12, command=guardar).grid(row=5, column=0, pady=15)
        tk.Button(win, text="Cancelar", width=12, command=win.destroy).grid(row=5, column=1, pady=15)

    def accion_ver_cuotas():
        sel = tabla_financiamiento.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccione un financiamiento.")
            return
        v = tabla_financiamiento.item(sel[0], "values")
        id_fin = v[0]

        win = tk.Toplevel(ventana_financiamiento)
        win.title(f"Cuotas del financiamiento #{id_fin}")
        win.geometry("700x450")

        cols = ("NumeroCuota", "FechaVencimiento", "Monto", "Estado")
        tv = ttk.Treeview(win, columns=cols, show="headings", height=15)
        for c in cols:
            tv.heading(c, text=c)
            tv.column(c, width=160, anchor="center")
        tv.pack(fill="both", expand=True, padx=10, pady=10)

        try:
            con = conectar_bd()
            cur = con.cursor()
            cur.execute("""
                SELECT NumeroCuota, FechaVencimiento, Monto, Estado
                FROM Cuotas WHERE IdFinanciamiento=?
                ORDER BY NumeroCuota
            """, (id_fin,))

            for f in cur.fetchall():
                numero_cuota, date_ven, monto, estado = f
                tv.insert("", "end", values=(
                    numero_cuota,
                    date_ven,
                    monto,
                    estado
                ))

            con.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar cuotas:\n{e}")

    btn_buscar.config(command=accion_buscar)
    btn_mostrar.config(command=accion_mostrar)
    btn_agregar.config(command=accion_crear)
    btn_ver_cuotas.config(command=accion_ver_cuotas)

    cargar_financiamientos()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    abrir_financiamiento()
    root.mainloop()