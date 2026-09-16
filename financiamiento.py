from database import conectar_bd
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date


def _sumar_meses(fecha, meses):
    """Suma meses a una fecha, ajustando el día a 28 como máximo."""
    mes = fecha.month - 1 + meses
    anio = fecha.year + mes // 12
    mes = mes % 12 + 1
    dia = min(fecha.day, 28)
    return date(anio, mes, dia)


def abrir_gestion_financiamientos(usuario=None, id_contrato=None, monto_sugerido=None):
    global ventana_financiamientos, tabla_financiamientos
    rol_de_usuario = usuario.get("NombreRol") if usuario else None
    nombre_usuario = usuario.get("NombreUsuario") if usuario else "Sistema"

    try:
        if ventana_financiamientos.winfo_exists():
            ventana_financiamientos.lift()
            ventana_financiamientos.focus_force()
            return
    except (NameError, tk.TclError):
        pass

    ventana_financiamientos = tk.Toplevel()
    ventana_financiamientos.geometry("1100x600")
    ventana_financiamientos.title("Gestión de Financiamientos")
    ventana_financiamientos.resizable(False, False)

    # ---------- Carga ----------
    def cargar_financiamientos(filtro=None):
        for item in tabla_financiamientos.get_children():
            tabla_financiamientos.delete(item)
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            query = """
                SELECT F.IdFinanciamiento,
                       C.Nombre + ' ' + C.Apellido AS Cliente,
                       F.IdContrato, F.MontoFinanciado, F.TasaInteres,
                       F.PlazoMeses, F.FechaInicio, F.Estado
                FROM Financiamientos F
                INNER JOIN Contratos CT ON F.IdContrato = CT.IdContrato
                INNER JOIN Clientes C ON CT.IdCliente = C.IdCliente
                WHERE 1 = 1
            """
            params = []
            if id_contrato:
                query += " AND F.IdContrato = ?"
                params.append(id_contrato)
            if filtro:
                query += " AND (C.Nombre LIKE ? OR C.Apellido LIKE ? OR CAST(F.IdContrato AS VARCHAR) LIKE ?)"
                like = f"%{filtro}%"
                params.extend([like, like, like])
            query += " ORDER BY F.IdFinanciamiento DESC"
            cursor.execute(query, params)
            for fila in cursor.fetchall():
                tabla_financiamientos.insert("", "end", values=fila)
            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar financiamientos: {e}")

    def accion_buscar():
        cargar_financiamientos(entrada_busqueda.get().strip() or None)

    def accion_mostrar_todos():
        entrada_busqueda.delete(0, "end")
        cargar_financiamientos()

    # ---------- Crear plan ----------
    def accion_crear():
        form = tk.Toplevel(ventana_financiamientos)
        form.title("Crear Plan de Financiamiento")
        form.geometry("480x560")
        form.resizable(False, False)
        form.transient(ventana_financiamientos)
        form.grab_set()

        mapa_contratos = {}
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            if id_contrato:
                cursor.execute("""
                    SELECT CT.IdContrato, C.Nombre + ' ' + C.Apellido AS Cliente,
                           CT.PrecioVenta
                    FROM Contratos CT
                    INNER JOIN Clientes C ON CT.IdCliente = C.IdCliente
                    WHERE CT.IdContrato = ?
                """, (id_contrato,))
            else:
                cursor.execute("""
                    SELECT CT.IdContrato, C.Nombre + ' ' + C.Apellido AS Cliente,
                           CT.PrecioVenta
                    FROM Contratos CT
                    INNER JOIN Clientes C ON CT.IdCliente = C.IdCliente
                    WHERE CT.TipoVenta = 'Financiado'
                      AND CT.IdContrato NOT IN (SELECT IdContrato FROM Financiamientos)
                    ORDER BY CT.IdContrato DESC
                """)
            for f in cursor.fetchall():
                mapa_contratos[f"Contrato #{f[0]} - {f[1]} (L. {f[2]:,.2f})"] = (f[0], float(f[2]))
            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar contratos: {e}")

        tk.Label(form, text="Contrato:").pack(anchor="w", padx=15, pady=(15, 0))
        combo_contrato = ttk.Combobox(form, values=list(mapa_contratos.keys()),
                                      state="readonly", width=55)
        combo_contrato.pack(padx=15, pady=5, fill="x")
        if id_contrato:
            for etiqueta in mapa_contratos:
                if mapa_contratos[etiqueta][0] == id_contrato:
                    combo_contrato.set(etiqueta)
                    break

        tk.Label(form, text="Monto financiado:").pack(anchor="w", padx=15, pady=(5, 0))
        entry_monto = tk.Entry(form, width=55)
        entry_monto.pack(padx=15, pady=5, fill="x")

        def al_seleccionar_contrato(_e=None):
            datos = mapa_contratos.get(combo_contrato.get())
            if datos:
                entry_monto.delete(0, "end")
                entry_monto.insert(0, f"{datos[1]:.2f}")
        combo_contrato.bind("<<ComboboxSelected>>", al_seleccionar_contrato)
        if id_contrato:
            al_seleccionar_contrato()
        elif monto_sugerido:
            entry_monto.insert(0, f"{monto_sugerido:.2f}")

        tk.Label(form, text="Tasa de interés anual (%):").pack(anchor="w", padx=15, pady=(5, 0))
        entry_tasa = tk.Entry(form, width=55)
        entry_tasa.insert(0, "12")
        entry_tasa.pack(padx=15, pady=5, fill="x")

        tk.Label(form, text="Plazo (meses):").pack(anchor="w", padx=15, pady=(5, 0))
        entry_plazo = tk.Entry(form, width=55)
        entry_plazo.insert(0, "12")
        entry_plazo.pack(padx=15, pady=5, fill="x")

        tk.Label(form, text="Fecha de inicio (YYYY-MM-DD):").pack(anchor="w", padx=15, pady=(5, 0))
        entry_fecha = tk.Entry(form, width=55)
        entry_fecha.insert(0, str(date.today()))
        entry_fecha.pack(padx=15, pady=5, fill="x")

        def guardar():
            if not combo_contrato.get():
                messagebox.showwarning("Validación", "Seleccione un contrato.", parent=form)
                return
            try:
                monto = float(entry_monto.get().strip())
                tasa = float(entry_tasa.get().strip())
                plazo = int(entry_plazo.get().strip())
                fecha_inicio = date.fromisoformat(entry_fecha.get().strip())
            except ValueError:
                messagebox.showwarning("Validación", "Revise los datos ingresados.", parent=form)
                return
            if plazo <= 0 or monto <= 0:
                messagebox.showwarning("Validación", "Monto y plazo deben ser positivos.", parent=form)
                return

            id_ct = mapa_contratos[combo_contrato.get()][0]

            try:
                conexion = conectar_bd()
                cursor = conexion.cursor()
                cursor.execute("""
                    INSERT INTO Financiamientos
                        (IdContrato, MontoFinanciado, TasaInteres, PlazoMeses, FechaInicio, Estado)
                    OUTPUT INSERTED.IdFinanciamiento
                    VALUES (?, ?, ?, ?, ?, 'Activo')
                """, (id_ct, monto, tasa, plazo, fecha_inicio))
                id_fin = cursor.fetchone()[0]

                # ---- Generar cuotas (sistema de amortización francés) ----
                tasa_mensual = (tasa / 100.0) / 12.0
                if tasa_mensual > 0:
                    factor = (1 + tasa_mensual) ** plazo
                    cuota = monto * (tasa_mensual * factor) / (factor - 1)
                else:
                    cuota = monto / plazo
                cuota = round(cuota, 2)

                for i in range(1, plazo + 1):
                    fecha_venc = _sumar_meses(fecha_inicio, i)
                    cursor.execute("""
                        INSERT INTO Cuotas (IdFinanciamiento, NumeroCuota,
                                            FechaVencimiento, Monto, Estado)
                        VALUES (?, ?, ?, ?, 'Pendiente')
                    """, (id_fin, i, fecha_venc, cuota))

                conexion.commit()
                conexion.close()
                messagebox.showinfo(
                    "Éxito",
                    f"Financiamiento #{id_fin} creado.\n"
                    f"{plazo} cuotas de L. {cuota:,.2f}",
                    parent=form
                )
                form.destroy()
                cargar_financiamientos()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear: {e}", parent=form)

        tk.Button(form, text="Generar plan y cuotas", width=22, command=guardar).pack(pady=20)

    # ---------- Ver cuotas ----------
    def accion_ver_cuotas():
        sel = tabla_financiamientos.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccione un financiamiento.")
            return
        id_fin = tabla_financiamientos.item(sel[0])["values"][0]

        ventana_cuotas = tk.Toplevel(ventana_financiamientos)
        ventana_cuotas.title(f"Cuotas del financiamiento #{id_fin}")
        ventana_cuotas.geometry("700x450")
        ventana_cuotas.transient(ventana_financiamientos)

        cols = ("N°", "Vencimiento", "Monto", "Estado")
        tv = ttk.Treeview(ventana_cuotas, columns=cols, show="headings")
        for c in cols:
            tv.heading(c, text=c)
            tv.column(c, width=150, anchor="center")
        tv.pack(fill="both", expand=True, padx=10, pady=10)

        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT NumeroCuota, FechaVencimiento, Monto, Estado
                FROM Cuotas WHERE IdFinanciamiento = ?
                ORDER BY NumeroCuota
            """, (id_fin,))
            for f in cursor.fetchall():
                tv.insert("", "end", values=f)
            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar cuotas: {e}")

    # ---------- UI ----------
    frame_busqueda = tk.Frame(ventana_financiamientos, pady=10)
    frame_busqueda.pack(fill="x", padx=10)

    tk.Label(frame_busqueda, text="Buscar:").pack(side="left")
    entrada_busqueda = tk.Entry(frame_busqueda, width=25)
    entrada_busqueda.pack(side="left", padx=5)

    tk.Button(frame_busqueda, text="Buscar", command=accion_buscar).pack(side="left", padx=5)
    tk.Button(frame_busqueda, text="Mostrar todos", command=accion_mostrar_todos).pack(side="left", padx=5)

    frame_tabla = tk.Frame(ventana_financiamientos)
    frame_tabla.pack(fill="both", expand=True, padx=10)

    columnas = ("ID", "Cliente", "Contrato", "Monto", "Tasa %",
                "Plazo", "Fecha Inicio", "Estado")
    tabla_financiamientos = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
    for col in columnas:
        tabla_financiamientos.heading(col, text=col)
        tabla_financiamientos.column(col, width=125, anchor="center")
    tabla_financiamientos.pack(fill="both", expand=True)

    frame_botones = tk.Frame(ventana_financiamientos, pady=10)
    frame_botones.pack(fill="x", padx=10)

    tk.Button(frame_botones, text="Crear plan", width=16, command=accion_crear).pack(side="left", padx=5)
    tk.Button(frame_botones, text="Ver cuotas", width=16, command=accion_ver_cuotas).pack(side="left", padx=5)
    tk.Button(frame_botones, text="Cerrar", width=15, command=ventana_financiamientos.destroy).pack(side="right", padx=5)

    cargar_financiamientos()