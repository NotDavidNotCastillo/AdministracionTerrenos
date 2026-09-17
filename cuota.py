from database import conectar_bd  # conexion a base de datos con mssql_python
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

ESTADOS_CUOTA = ["Pendiente", "Pagada", "Vencida", "Pago Parcial"]


def abrir_gestion_cuotas():
    global ventana_gest_cuota, tabla_gest_cuota

    try:
        if ventana_gest_cuota.winfo_exists():
            ventana_gest_cuota.lift()
            ventana_gest_cuota.focus_force()
            return
    except (NameError, tk.TclError):
        pass

    ventana_gest_cuota = tk.Toplevel()
    ventana_gest_cuota.geometry("1100x600")
    ventana_gest_cuota.title("Gestión de Lotes")
    ventana_gest_cuota.resizable(False, False)

    # ---------- Estado interno de la ventana ----------
    id_cliente_actual = {"id": None}

    # ================= FRAME BÚSQUEDA CLIENTE =================
    frame_busqueda = tk.LabelFrame(ventana_gest_cuota, text="Buscar Cliente por Identidad")
    frame_busqueda.pack(fill="x", padx=10, pady=8)

    tk.Label(frame_busqueda, text="Identidad:").grid(row=0, column=0, padx=5, pady=8, sticky="e")
    entry_identidad = tk.Entry(frame_busqueda, width=25)
    entry_identidad.grid(row=0, column=1, padx=5, pady=8, sticky="w")
    entry_identidad.bind("<Return>", lambda e: buscar_cliente())

    btn_buscar = tk.Button(frame_busqueda, text="Buscar", width=12, command=lambda: buscar_cliente())
    btn_buscar.grid(row=0, column=2, padx=10, pady=8)

    lbl_cliente_info = tk.Label(frame_busqueda, text="Cliente: -", font=("Segoe UI", 10, "bold"), fg="#1a5276")
    lbl_cliente_info.grid(row=0, column=3, padx=20, pady=8, sticky="w")

    # ================= FRAME FILTRO =================
    frame_filtro = tk.LabelFrame(ventana_gest_cuota, text="Filtrar Cuotas del Cliente")
    frame_filtro.pack(fill="x", padx=10, pady=4)

    tk.Label(frame_filtro, text="Estado:").grid(row=0, column=0, padx=5, pady=6, sticky="e")
    combo_filtro = ttk.Combobox(
        frame_filtro,
        values=["Todas"] + ESTADOS_CUOTA,
        state="readonly",
        width=20,
    )
    combo_filtro.set("Todas")
    combo_filtro.grid(row=0, column=1, padx=5, pady=6, sticky="w")
    combo_filtro.bind("<<ComboboxSelected>>", lambda e: cargar_cuotas())

    # ================= TABLA DE CUOTAS (CALENDARIO DE PAGO) =================
    frame_tabla = tk.Frame(ventana_gest_cuota)
    frame_tabla.pack(fill="both", expand=True, padx=10, pady=6)

    columnas = ("id_cuota", "num_cuota", "vencimiento", "monto", "estado", "contrato")
    tabla_gest_cuota = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=16)

    tabla_gest_cuota.heading("id_cuota", text="ID")
    tabla_gest_cuota.heading("num_cuota", text="N° Cuota")
    tabla_gest_cuota.heading("vencimiento", text="Fecha Vencimiento")
    tabla_gest_cuota.heading("monto", text="Monto")
    tabla_gest_cuota.heading("estado", text="Estado")
    tabla_gest_cuota.heading("contrato", text="Contrato")

    tabla_gest_cuota.column("id_cuota", width=50, anchor="center")
    tabla_gest_cuota.column("num_cuota", width=80, anchor="center")
    tabla_gest_cuota.column("vencimiento", width=140, anchor="center")
    tabla_gest_cuota.column("monto", width=120, anchor="e")
    tabla_gest_cuota.column("estado", width=120, anchor="center")
    tabla_gest_cuota.column("contrato", width=90, anchor="center")

    scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=tabla_gest_cuota.yview)
    tabla_gest_cuota.configure(yscrollcommand=scroll_y.set)
    tabla_gest_cuota.pack(side="left", fill="both", expand=True)
    scroll_y.pack(side="right", fill="y")

    tabla_gest_cuota.tag_configure("vencida", background="#f5b7b1")
    tabla_gest_cuota.tag_configure("pagada", background="#a9dfbf")
    tabla_gest_cuota.tag_configure("parcial", background="#fdebd0")

    tabla_gest_cuota.bind("<<TreeviewSelect>>", lambda e: seleccionar_cuota())

    # ================= FRAME EDICIÓN DE ESTADO =================
    frame_edicion = tk.LabelFrame(ventana_gest_cuota, text="Modificar Estado de la Cuota Seleccionada")
    frame_edicion.pack(fill="x", padx=10, pady=8)

    tk.Label(frame_edicion, text="Cuota seleccionada:").grid(row=0, column=0, padx=5, pady=8, sticky="e")
    lbl_cuota_sel = tk.Label(frame_edicion, text="Ninguna", fg="#7b241c", font=("Segoe UI", 9, "bold"))
    lbl_cuota_sel.grid(row=0, column=1, padx=5, pady=8, sticky="w")

    tk.Label(frame_edicion, text="Nuevo estado:").grid(row=0, column=2, padx=5, pady=8, sticky="e")
    combo_nuevo_estado = ttk.Combobox(frame_edicion, values=ESTADOS_CUOTA, state="readonly", width=18)
    combo_nuevo_estado.grid(row=0, column=3, padx=5, pady=8, sticky="w")

    btn_actualizar = tk.Button(
        frame_edicion, text="Actualizar Estado", width=18, bg="#2e86c1", fg="white",
        command=lambda: actualizar_estado(),
    )
    btn_actualizar.grid(row=0, column=4, padx=15, pady=8)

    btn_cerrar = tk.Button(ventana_gest_cuota, text="Cerrar", width=12, command=ventana_gest_cuota.destroy)
    btn_cerrar.pack(pady=4)

    # ================= FUNCIONES =================
    def buscar_cliente():
        identidad = entry_identidad.get().strip()
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
            id_cliente_actual["id"] = None
            lbl_cliente_info.config(text="Cliente: no encontrado", fg="#c0392b")
            for item in tabla_gest_cuota.get_children():
                tabla_gest_cuota.delete(item)
            messagebox.showinfo("Sin resultados", "No se encontró ningún cliente con esa identidad.")
            return

        id_cliente_actual["id"] = fila[0]
        lbl_cliente_info.config(text=f"Cliente: {fila[1]} {fila[2]}  (Identidad: {identidad})", fg="#1a5276")
        combo_filtro.set("Todas")
        cargar_cuotas()

    def cargar_cuotas():
        for item in tabla_gest_cuota.get_children():
            tabla_gest_cuota.delete(item)

        id_cliente = id_cliente_actual["id"]
        if id_cliente is None:
            return

        filtro = combo_filtro.get()

        query = """
            SELECT c.IdCuota, c.NumeroCuota, c.FechaVencimiento, c.Monto, c.Estado, ct.IdContrato
            FROM Cuotas c
            INNER JOIN Financiamientos f ON c.IdFinanciamiento = f.IdFinanciamiento
            INNER JOIN Contratos ct ON f.IdContrato = ct.IdContrato
            WHERE ct.IdCliente = ?
        """
        params = [id_cliente]

        if filtro != "Todas":
            query += " AND c.Estado = ?"
            params.append(filtro)

        query += " ORDER BY c.FechaVencimiento ASC"

        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            filas = cursor.fetchall()
            conn.close()
        except Exception as ex:
            messagebox.showerror("Error de conexión", f"No se pudieron cargar las cuotas:\n{ex}")
            return

        hoy = date.today()
        for f in filas:
            id_cuota, num_cuota, fecha_venc, monto, estado, id_contrato = f

            tag = ""
            if estado == "Pagada":
                tag = "pagada"
            elif estado == "Pago Parcial":
                tag = "parcial"
            elif estado == "Vencida" or (estado == "Pendiente" and fecha_venc and fecha_venc < hoy):
                tag = "vencida"

            tabla_gest_cuota.insert(
                "", "end",
                values=(id_cuota, num_cuota, fecha_venc, f"L. {monto:,.2f}", estado, id_contrato),
                tags=(tag,) if tag else (),
            )

        lbl_cuota_sel.config(text="Ninguna")
        combo_nuevo_estado.set("")

    def seleccionar_cuota():
        seleccion = tabla_gest_cuota.selection()
        if not seleccion:
            lbl_cuota_sel.config(text="Ninguna")
            combo_nuevo_estado.set("")
            return
        valores = tabla_gest_cuota.item(seleccion[0], "values")
        id_cuota, num_cuota, _, _, estado_actual, _ = valores
        lbl_cuota_sel.config(text=f"Cuota N° {num_cuota} (ID {id_cuota}) - Actual: {estado_actual}")
        combo_nuevo_estado.set(estado_actual)

    def actualizar_estado():
        seleccion = tabla_gest_cuota.selection()
        if not seleccion:
            messagebox.showwarning("Aviso", "Seleccione una cuota de la tabla.")
            return

        nuevo_estado = combo_nuevo_estado.get()
        if not nuevo_estado:
            messagebox.showwarning("Aviso", "Seleccione el nuevo estado.")
            return

        id_cuota = tabla_gest_cuota.item(seleccion[0], "values")[0]

        if not messagebox.askyesno("Confirmar", f"¿Cambiar el estado de la cuota #{id_cuota} a '{nuevo_estado}'?"):
            return

        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE Cuotas SET Estado = ? WHERE IdCuota = ?",
                (nuevo_estado, id_cuota),
            )
            conn.commit()
            conn.close()
        except Exception as ex:
            messagebox.showerror("Error de conexión", f"No se pudo actualizar la cuota:\n{ex}")
            return

        messagebox.showinfo("Éxito", "Estado de la cuota actualizado correctamente.")
        cargar_cuotas()

    entry_identidad.focus_set()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    abrir_gestion_cuotas()
    root.mainloop()