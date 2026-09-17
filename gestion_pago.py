from database import conectar_bd  # conexion a base de datos con mssql_python
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime


def abrir_gestion_pagos():
    global ventana_gest_pago, tabla_cuotas_pago, tabla_historial_pago

    try:
        if ventana_gest_pago.winfo_exists():
            ventana_gest_pago.lift()
            ventana_gest_pago.focus_force()
            return
    except (NameError, tk.TclError):
        pass

    ventana_gest_pago = tk.Toplevel()
    ventana_gest_pago.geometry("1150x680")
    ventana_gest_pago.title("Gestión de Pagos (Abonos)")
    ventana_gest_pago.resizable(False, False)

    # ---------- Estado interno de la ventana ----------
    id_cliente_pago = {"id": None}
    cuota_seleccionada = {"id": None, "monto": None, "saldo": None}

    # ================= FRAME BÚSQUEDA CLIENTE =================
    frame_busqueda_pago = tk.LabelFrame(ventana_gest_pago, text="Buscar Cliente por Identidad")
    frame_busqueda_pago.pack(fill="x", padx=10, pady=8)

    tk.Label(frame_busqueda_pago, text="Identidad:").grid(row=0, column=0, padx=5, pady=8, sticky="e")
    entry_identidad_pago = tk.Entry(frame_busqueda_pago, width=25)
    entry_identidad_pago.grid(row=0, column=1, padx=5, pady=8, sticky="w")
    entry_identidad_pago.bind("<Return>", lambda e: buscar_cliente_pago())

    btn_buscar_pago = tk.Button(frame_busqueda_pago, text="Buscar", width=12, command=lambda: buscar_cliente_pago())
    btn_buscar_pago.grid(row=0, column=2, padx=10, pady=8)

    lbl_cliente_pago_info = tk.Label(frame_busqueda_pago, text="Cliente: -")
    lbl_cliente_pago_info.grid(row=0, column=3, padx=20, pady=8, sticky="w")

    lbl_saldo_total = tk.Label(frame_busqueda_pago, text="Saldo total pendiente: L. 0.00")
    lbl_saldo_total.grid(row=0, column=4, padx=20, pady=8, sticky="w")

    # ================= TABLA DE CUOTAS Y SALDOS =================
    frame_saldos = tk.LabelFrame(ventana_gest_pago, text="Cuotas del Cliente y Saldo Pendiente")
    frame_saldos.pack(fill="both", expand=False, padx=10, pady=4)

    cols_saldo = ("id_cuota", "num_cuota", "vencimiento", "monto", "abonado", "saldo", "estado")
    tabla_cuotas_pago = ttk.Treeview(frame_saldos, columns=cols_saldo, show="headings", height=8)

    tabla_cuotas_pago.heading("id_cuota", text="ID")
    tabla_cuotas_pago.heading("num_cuota", text="N° Cuota")
    tabla_cuotas_pago.heading("vencimiento", text="Vencimiento")
    tabla_cuotas_pago.heading("monto", text="Monto Cuota")
    tabla_cuotas_pago.heading("abonado", text="Total Abonado")
    tabla_cuotas_pago.heading("saldo", text="Saldo")
    tabla_cuotas_pago.heading("estado", text="Estado")

    tabla_cuotas_pago.column("id_cuota", width=45, anchor="center")
    tabla_cuotas_pago.column("num_cuota", width=70, anchor="center")
    tabla_cuotas_pago.column("vencimiento", width=110, anchor="center")
    tabla_cuotas_pago.column("monto", width=110, anchor="e")
    tabla_cuotas_pago.column("abonado", width=110, anchor="e")
    tabla_cuotas_pago.column("saldo", width=110, anchor="e")
    tabla_cuotas_pago.column("estado", width=110, anchor="center")

    scroll_saldo = ttk.Scrollbar(frame_saldos, orient="vertical", command=tabla_cuotas_pago.yview)
    tabla_cuotas_pago.configure(yscrollcommand=scroll_saldo.set)
    tabla_cuotas_pago.pack(side="left", fill="both", expand=True)
    scroll_saldo.pack(side="right", fill="y")

    tabla_cuotas_pago.bind("<<TreeviewSelect>>", lambda e: seleccionar_cuota_pago())

    # ================= FRAME REGISTRAR PAGO =================
    frame_registro = tk.LabelFrame(ventana_gest_pago, text="Registrar Pago (Abono)")
    frame_registro.pack(fill="x", padx=10, pady=8)

    tk.Label(frame_registro, text="Cuota seleccionada:").grid(row=0, column=0, padx=5, pady=8, sticky="e")
    lbl_cuota_pago_sel = tk.Label(frame_registro, text="Ninguna")
    lbl_cuota_pago_sel.grid(row=0, column=1, padx=5, pady=8, sticky="w")

    tk.Label(frame_registro, text="Fecha del abono (AAAA-MM-DD):").grid(row=0, column=2, padx=5, pady=8, sticky="e")
    entry_fecha_abono = tk.Entry(frame_registro, width=14)
    entry_fecha_abono.insert(0, date.today().isoformat())
    entry_fecha_abono.grid(row=0, column=3, padx=5, pady=8, sticky="w")

    tk.Label(frame_registro, text="Monto abonado:").grid(row=0, column=4, padx=5, pady=8, sticky="e")
    entry_monto_abono = tk.Entry(frame_registro, width=14)
    entry_monto_abono.grid(row=0, column=5, padx=5, pady=8, sticky="w")

    btn_registrar_pago = tk.Button(
        frame_registro, text="Registrar Pago", width=16,
        command=lambda: registrar_pago(),
    )
    btn_registrar_pago.grid(row=0, column=6, padx=15, pady=8)

    # ================= HISTORIAL DE PAGOS =================
    frame_historial = tk.LabelFrame(ventana_gest_pago, text="Historial de Pagos del Cliente")
    frame_historial.pack(fill="both", expand=True, padx=10, pady=4)

    cols_hist = ("id_abono", "num_cuota", "fecha_abono", "monto_abonado", "estado")
    tabla_historial_pago = ttk.Treeview(frame_historial, columns=cols_hist, show="headings", height=10)

    tabla_historial_pago.heading("id_abono", text="ID Abono")
    tabla_historial_pago.heading("num_cuota", text="Cuota N°")
    tabla_historial_pago.heading("fecha_abono", text="Fecha de Pago")
    tabla_historial_pago.heading("monto_abonado", text="Monto Abonado")
    tabla_historial_pago.heading("estado", text="Estado")

    tabla_historial_pago.column("id_abono", width=90, anchor="center")
    tabla_historial_pago.column("num_cuota", width=90, anchor="center")
    tabla_historial_pago.column("fecha_abono", width=140, anchor="center")
    tabla_historial_pago.column("monto_abonado", width=140, anchor="e")
    tabla_historial_pago.column("estado", width=100, anchor="center")

    scroll_hist = ttk.Scrollbar(frame_historial, orient="vertical", command=tabla_historial_pago.yview)
    tabla_historial_pago.configure(yscrollcommand=scroll_hist.set)
    tabla_historial_pago.pack(side="left", fill="both", expand=True)
    scroll_hist.pack(side="right", fill="y")

    btn_cerrar_pago = tk.Button(ventana_gest_pago, text="Cerrar", width=12, command=ventana_gest_pago.destroy)
    btn_cerrar_pago.pack(pady=6)

    # ================= FUNCIONES =================
    def buscar_cliente_pago():
        identidad = entry_identidad_pago.get().strip()
        if not identidad:
            messagebox.showwarning("Aviso", "Ingrese un número de identidad.")
            return
        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT IdCliente, Nombre, Apellido FROM Clientes WHERE Identidad = ?",
                (identidad,),
            )
            fila = cursor.fetchone()
            conn.close()
        except Exception as ex:
            messagebox.showerror("Error de conexión", f"No se pudo consultar el cliente:\n{ex}")
            return

        if not fila:
            id_cliente_pago["id"] = None
            lbl_cliente_pago_info.config(text="Cliente: no encontrado")
            lbl_saldo_total.config(text="Saldo total pendiente: L. 0.00")
            limpiar_tablas_pago()
            messagebox.showinfo("Sin resultados", "No se encontró ningún cliente con esa identidad.")
            return

        id_cliente_pago["id"] = fila[0]
        lbl_cliente_pago_info.config(text=f"Cliente: {fila[1]} {fila[2]}  (Identidad: {identidad})")
        refrescar_pagos()

    def limpiar_tablas_pago():
        for item in tabla_cuotas_pago.get_children():
            tabla_cuotas_pago.delete(item)
        for item in tabla_historial_pago.get_children():
            tabla_historial_pago.delete(item)
        lbl_cuota_pago_sel.config(text="Ninguna")
        cuota_seleccionada["id"] = None
        cuota_seleccionada["monto"] = None
        cuota_seleccionada["saldo"] = None

    def refrescar_pagos():
        """Recarga la tabla de saldos por cuota y el historial completo de pagos del cliente."""
        id_cliente = id_cliente_pago["id"]
        limpiar_tablas_pago()
        if id_cliente is None:
            return

        query_saldos = """
            SELECT c.IdCuota, c.NumeroCuota, c.FechaVencimiento, c.Monto, c.Estado,
                   ISNULL((SELECT SUM(a.MontoAbonado) FROM Abonos a
                           WHERE a.IdCuota = c.IdCuota AND a.Estado = 1), 0) AS TotalAbonado
            FROM Cuotas c
            INNER JOIN Financiamientos f ON c.IdFinanciamiento = f.IdFinanciamiento
            INNER JOIN Contratos ct ON f.IdContrato = ct.IdContrato
            WHERE ct.IdCliente = ?
            ORDER BY c.FechaVencimiento ASC
        """

        query_historial = """
            SELECT a.IdAbono, c.NumeroCuota, a.FechaAbono, a.MontoAbonado, a.Estado
            FROM Abonos a
            INNER JOIN Cuotas c ON a.IdCuota = c.IdCuota
            INNER JOIN Financiamientos f ON c.IdFinanciamiento = f.IdFinanciamiento
            INNER JOIN Contratos ct ON f.IdContrato = ct.IdContrato
            WHERE ct.IdCliente = ?
            ORDER BY a.FechaAbono DESC, a.IdAbono DESC
        """

        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute(query_saldos, (id_cliente,))
            filas_saldo = cursor.fetchall()
            cursor.execute(query_historial, (id_cliente,))
            filas_hist = cursor.fetchall()
            conn.close()
        except Exception as ex:
            messagebox.showerror("Error de conexión", f"No se pudieron cargar los pagos:\n{ex}")
            return

        saldo_total = 0.0

        for f in filas_saldo:
            id_cuota, num_cuota, fecha_venc, monto, estado, total_abonado = f
            monto = float(monto)
            total_abonado = float(total_abonado)
            saldo = monto - total_abonado
            saldo_total += max(saldo, 0)

            tabla_cuotas_pago.insert(
                "", "end",
                values=(
                    id_cuota, num_cuota, fecha_venc,
                    f"L. {monto:,.2f}", f"L. {total_abonado:,.2f}", f"L. {saldo:,.2f}", estado,
                ),
            )

        lbl_saldo_total.config(text=f"Saldo total pendiente: L. {saldo_total:,.2f}")

        for h in filas_hist:
            id_abono, num_cuota, fecha_abono, monto_abonado, estado_abono = h
            estado_txt = "Activo" if estado_abono else "Anulado"
            tabla_historial_pago.insert(
                "", "end",
                values=(id_abono, num_cuota, fecha_abono, f"L. {float(monto_abonado):,.2f}", estado_txt),
            )

    def seleccionar_cuota_pago():
        seleccion = tabla_cuotas_pago.selection()
        if not seleccion:
            cuota_seleccionada["id"] = None
            lbl_cuota_pago_sel.config(text="Ninguna")
            return
        valores = tabla_cuotas_pago.item(seleccion[0], "values")
        id_cuota, num_cuota, _, monto_txt, _, saldo_txt, estado_actual = valores

        monto = float(str(monto_txt).replace("L. ", "").replace(",", ""))
        saldo = float(str(saldo_txt).replace("L. ", "").replace(",", ""))

        cuota_seleccionada["id"] = id_cuota
        cuota_seleccionada["monto"] = monto
        cuota_seleccionada["saldo"] = saldo

        lbl_cuota_pago_sel.config(
            text=f"Cuota N° {num_cuota} (ID {id_cuota}) - Estado: {estado_actual} - Saldo: L. {saldo:,.2f}"
        )
        entry_monto_abono.delete(0, tk.END)

    def calcular_nuevo_estado_cuota(monto_cuota, total_abonado, fecha_venc):
        if total_abonado >= monto_cuota:
            return "Pagada"
        if total_abonado > 0:
            return "Pago Parcial"
        if fecha_venc and fecha_venc < date.today():
            return "Vencida"
        return "Pendiente"

    def obtener_saldo_cuota(cursor, id_cuota):
        cursor.execute(
            "SELECT c.Monto, c.FechaVencimiento, "
            "ISNULL((SELECT SUM(a.MontoAbonado) FROM Abonos a WHERE a.IdCuota = c.IdCuota AND a.Estado = 1), 0) "
            "FROM Cuotas c WHERE c.IdCuota = ?",
            (id_cuota,),
        )
        monto_cuota, fecha_venc, total_abonado = cursor.fetchone()
        monto_cuota = float(monto_cuota)
        total_abonado = float(total_abonado)
        saldo = monto_cuota - total_abonado
        return monto_cuota, fecha_venc, total_abonado, saldo

    def aplicar_abono_a_cuota(cursor, id_cuota, monto_aplicar, fecha_abono):
        """Inserta el abono en la cuota indicada y recalcula/actualiza su estado."""
        cursor.execute(
            "INSERT INTO Abonos (IdCuota, FechaAbono, MontoAbonado, Estado) VALUES (?, ?, ?, 1)",
            (id_cuota, fecha_abono, monto_aplicar),
        )
        monto_cuota, fecha_venc, total_abonado, _ = obtener_saldo_cuota(cursor, id_cuota)
        nuevo_estado = calcular_nuevo_estado_cuota(monto_cuota, total_abonado, fecha_venc)
        cursor.execute(
            "UPDATE Cuotas SET Estado = ? WHERE IdCuota = ?",
            (nuevo_estado, id_cuota),
        )
        return nuevo_estado

    def registrar_pago():
        if cuota_seleccionada["id"] is None:
            messagebox.showwarning("Aviso", "Seleccione una cuota de la tabla de saldos.")
            return

        fecha_txt = entry_fecha_abono.get().strip()
        monto_txt = entry_monto_abono.get().strip()

        try:
            fecha_abono = datetime.strptime(fecha_txt, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Error", "La fecha debe tener el formato AAAA-MM-DD.")
            return

        try:
            monto_disponible = float(monto_txt)
            if monto_disponible <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Ingrese un monto abonado válido (mayor a 0).")
            return

        id_cuota_inicial = cuota_seleccionada["id"]

        try:
            conn = conectar_bd()
            cursor = conn.cursor()

            # Cuota inicial y datos de su financiamiento, para poder ubicar la(s) siguiente(s) cuota(s)
            cursor.execute(
                "SELECT IdFinanciamiento, NumeroCuota FROM Cuotas WHERE IdCuota = ?",
                (id_cuota_inicial,),
            )
            id_financiamiento, numero_cuota_inicial = cursor.fetchone()

            cursor.execute(
                "SELECT IdCuota, NumeroCuota FROM Cuotas "
                "WHERE IdFinanciamiento = ? AND NumeroCuota >= ? "
                "ORDER BY NumeroCuota ASC",
                (id_financiamiento, numero_cuota_inicial),
            )
            cuotas_disponibles = cursor.fetchall()

            detalle_aplicado = []
            ultima_cuota_id = id_cuota_inicial
            ultimo_num_cuota = numero_cuota_inicial

            for id_cuota, num_cuota in cuotas_disponibles:
                if monto_disponible <= 0:
                    break

                _, _, _, saldo_cuota = obtener_saldo_cuota(cursor, id_cuota)
                if saldo_cuota <= 0:
                    continue  # esta cuota ya está totalmente pagada

                monto_a_aplicar = min(monto_disponible, saldo_cuota)
                nuevo_estado = aplicar_abono_a_cuota(cursor, id_cuota, monto_a_aplicar, fecha_abono)

                detalle_aplicado.append((num_cuota, monto_a_aplicar, nuevo_estado))
                monto_disponible -= monto_a_aplicar
                ultima_cuota_id = id_cuota
                ultimo_num_cuota = num_cuota

            # Si sobra dinero y ya no hay más cuotas de este financiamiento por cubrir
            if monto_disponible > 0:
                aplicar_excedente = messagebox.askyesno(
                    "Excedente sin cuotas pendientes",
                    f"Ya no hay más cuotas pendientes en este financiamiento para aplicar "
                    f"el excedente de L. {monto_disponible:,.2f}.\n\n"
                    f"¿Desea registrarlo como abono adicional en la última cuota "
                    f"(N° {ultimo_num_cuota})?",
                )
                if aplicar_excedente:
                    nuevo_estado = aplicar_abono_a_cuota(cursor, ultima_cuota_id, monto_disponible, fecha_abono)
                    detalle_aplicado.append((ultimo_num_cuota, monto_disponible, nuevo_estado))
                    monto_disponible = 0

            conn.commit()
            conn.close()
        except Exception as ex:
            messagebox.showerror("Error de conexión", f"No se pudo registrar el pago:\n{ex}")
            return

        if not detalle_aplicado:
            messagebox.showwarning("Aviso", "No se aplicó ningún monto (la cuota ya estaba pagada).")
        else:
            lineas = "\n".join(
                f"- Cuota N° {num}: L. {monto:,.2f}  (Estado: {estado})"
                for num, monto, estado in detalle_aplicado
            )
            mensaje = f"Pago registrado y distribuido así:\n{lineas}"
            if monto_disponible > 0:
                mensaje += f"\n\nExcedente no aplicado: L. {monto_disponible:,.2f}"
            messagebox.showinfo("Pago registrado", mensaje)

        entry_monto_abono.delete(0, tk.END)
        entry_fecha_abono.delete(0, tk.END)
        entry_fecha_abono.insert(0, date.today().isoformat())
        refrescar_pagos()

    entry_identidad_pago.focus_set()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    abrir_gestion_pagos()
    root.mainloop()