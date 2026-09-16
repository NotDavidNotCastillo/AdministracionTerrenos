from database import conectar_bd
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date


def abrir_gestion_contratos(usuario=None, id_cliente=None, id_lote=None,
                             monto_reserva=0, id_reservacion_origen=None):
    global ventana_contratos, tabla_contratos
    rol_de_usuario = usuario.get("NombreRol") if usuario else None
    nombre_usuario = usuario.get("NombreUsuario") if usuario else "Sistema"

    try:
        if ventana_contratos.winfo_exists():
            ventana_contratos.lift()
            ventana_contratos.focus_force()
            return
    except (NameError, tk.TclError):
        pass

    ventana_contratos = tk.Toplevel()
    ventana_contratos.geometry("1100x600")
    ventana_contratos.title("Gestión de Contratos")
    ventana_contratos.resizable(False, False)

    def cargar_contratos(filtro=None, estado=None):
        for item in tabla_contratos.get_children():
            tabla_contratos.delete(item)
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            query = """
                SELECT CT.IdContrato,
                       C.Nombre + ' ' + C.Apellido AS Cliente,
                       P.NombreProyecto, L.NumeroLote,
                       CT.FechaContrato, CT.FinContrato,
                       CT.PrecioVenta, CT.TipoVenta, CT.Estado
                FROM Contratos CT
                INNER JOIN Clientes C ON CT.IdCliente = C.IdCliente
                INNER JOIN Lotes L ON CT.IdLote = L.IdLote
                INNER JOIN Terrenos T ON L.IdTerreno = T.IdTerreno
                INNER JOIN Proyectos P ON T.IdProyecto = P.IdProyecto
                WHERE 1 = 1
            """
            params = []
            if estado and estado != "Todos":
                query += " AND CT.Estado = ?"
                params.append(estado)
            if filtro:
                query += " AND (C.Nombre LIKE ? OR C.Apellido LIKE ? OR L.NumeroLote LIKE ?)"
                like = f"%{filtro}%"
                params.extend([like, like, like])
            query += " ORDER BY CT.IdContrato DESC"
            cursor.execute(query, params)
            for fila in cursor.fetchall():
                tabla_contratos.insert("", "end", values=fila)
            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar contratos: {e}")

    def accion_buscar():
        cargar_contratos(entrada_busqueda.get().strip() or None, combo_estado.get())

    def accion_mostrar_todos():
        entrada_busqueda.delete(0, "end")
        combo_estado.current(0)
        cargar_contratos()

    # ---------- Crear contrato ----------
    def accion_crear():
        form = tk.Toplevel(ventana_contratos)
        form.title("Crear Contrato")
        form.geometry("480x560")
        form.resizable(False, False)
        form.transient(ventana_contratos)
        form.grab_set()

        mapa_clientes = {}
        mapa_lotes = {}

        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute("SELECT IdCliente, Nombre, Apellido, Identidad FROM Clientes WHERE Estado = 1")
            for f in cursor.fetchall():
                mapa_clientes[f"{f[1]} {f[2]} ({f[3]})"] = f[0]

            if id_lote:
                # Venimos de una reservación: solo mostramos ese lote
                cursor.execute("""
                    SELECT L.IdLote, P.NombreProyecto, T.NombreTerreno, L.NumeroLote, L.Precio
                    FROM Lotes L
                    INNER JOIN Terrenos T ON L.IdTerreno = T.IdTerreno
                    INNER JOIN Proyectos P ON T.IdProyecto = P.IdProyecto
                    WHERE L.IdLote = ?
                """, (id_lote,))
            else:
                cursor.execute("""
                    SELECT L.IdLote, P.NombreProyecto, T.NombreTerreno, L.NumeroLote, L.Precio
                    FROM Lotes L
                    INNER JOIN Terrenos T ON L.IdTerreno = T.IdTerreno
                    INNER JOIN Proyectos P ON T.IdProyecto = P.IdProyecto
                    WHERE L.Estado IN ('Disponible', 'Reservado')
                    ORDER BY P.NombreProyecto, L.NumeroLote
                """)
            for f in cursor.fetchall():
                mapa_lotes[f"{f[1]} - {f[2]} - Lote {f[3]} (L. {f[4]:,.2f})"] = (f[0], f[4])
            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos: {e}")

        # Cliente
        tk.Label(form, text="Cliente:").pack(anchor="w", padx=15, pady=(15, 0))
        combo_cliente = ttk.Combobox(form, values=list(mapa_clientes.keys()),
                                     state="readonly", width=55)
        combo_cliente.pack(padx=15, pady=5, fill="x")
        if id_cliente:
            for etiqueta, cid in mapa_clientes.items():
                if cid == id_cliente:
                    combo_cliente.set(etiqueta)
                    break

        # Lote
        tk.Label(form, text="Lote:").pack(anchor="w", padx=15, pady=(5, 0))
        combo_lote = ttk.Combobox(form, values=list(mapa_lotes.keys()),
                                  state="readonly", width=55)
        combo_lote.pack(padx=15, pady=5, fill="x")
        if id_lote:
            for etiqueta, (lid, _) in mapa_lotes.items():
                if lid == id_lote:
                    combo_lote.set(etiqueta)
                    break

        # Fecha contrato
        tk.Label(form, text="Fecha de contrato (YYYY-MM-DD):").pack(anchor="w", padx=15, pady=(5, 0))
        entry_fecha = tk.Entry(form, width=55)
        entry_fecha.insert(0, str(date.today()))
        entry_fecha.pack(padx=15, pady=5, fill="x")

        # Fin contrato
        tk.Label(form, text="Fecha fin de contrato (YYYY-MM-DD):").pack(anchor="w", padx=15, pady=(5, 0))
        entry_fin = tk.Entry(form, width=55)
        entry_fin.insert(0, str(date.today()))
        entry_fin.pack(padx=15, pady=5, fill="x")

        # Precio
        tk.Label(form, text="Precio de venta:").pack(anchor="w", padx=15, pady=(5, 0))
        entry_precio = tk.Entry(form, width=55)
        entry_precio.pack(padx=15, pady=5, fill="x")

        # Autocompletar precio y descontar reserva
        def al_seleccionar_lote(_event=None):
            datos = mapa_lotes.get(combo_lote.get())
            if datos:
                precio_base = datos[1]
                precio_final = max(precio_base - float(monto_reserva or 0), 0)
                entry_precio.delete(0, "end")
                entry_precio.insert(0, f"{precio_final:.2f}")
        combo_lote.bind("<<ComboboxSelected>>", al_seleccionar_lote)
        if id_lote:
            al_seleccionar_lote()

        # Tipo de venta
        tk.Label(form, text="Tipo de venta:").pack(anchor="w", padx=15, pady=(5, 0))
        combo_tipo = ttk.Combobox(form, values=["Contado", "Financiado"],
                                  state="readonly", width=52)
        combo_tipo.current(0)
        combo_tipo.pack(padx=15, pady=5, fill="x")

        def guardar():
            if not combo_cliente.get() or not combo_lote.get():
                messagebox.showwarning("Validación", "Seleccione cliente y lote.", parent=form)
                return
            try:
                fecha_c = date.fromisoformat(entry_fecha.get().strip())
                fecha_f = date.fromisoformat(entry_fin.get().strip())
                precio = float(entry_precio.get().strip())
            except ValueError:
                messagebox.showwarning("Validación", "Revise las fechas y el precio.", parent=form)
                return

            id_cliente_v = mapa_clientes[combo_cliente.get()]
            id_lote_v = mapa_lotes[combo_lote.get()][0]
            tipo = combo_tipo.get()

            try:
                conexion = conectar_bd()
                cursor = conexion.cursor()
                cursor.execute("""
                    INSERT INTO Contratos (IdCliente, IdLote, FechaContrato, FinContrato,
                                           PrecioVenta, TipoVenta, Estado)
                    OUTPUT INSERTED.IdContrato
                    VALUES (?, ?, ?, ?, ?, ?, 'Activo')
                """, (id_cliente_v, id_lote_v, fecha_c, fecha_f, precio, tipo))
                id_contrato_nuevo = cursor.fetchone()[0]

                # Actualizar estado del lote
                cursor.execute("""
                    UPDATE Lotes SET Estado = 'Vendido', FechaEditado = ?, EditarPor = ?
                    WHERE IdLote = ?
                """, (date.today(), nombre_usuario, id_lote_v))

                # Si viene de una reservación, marcarla como convertida
                if id_reservacion_origen:
                    cursor.execute("""
                        UPDATE Reservaciones SET Estado = 'Convertida'
                        WHERE IdReservacion = ?
                    """, (id_reservacion_origen,))

                conexion.commit()
                conexion.close()
                messagebox.showinfo("Éxito", f"Contrato #{id_contrato_nuevo} creado.", parent=form)
                form.destroy()
                cargar_contratos()

                # Si es financiado, abrir el módulo de financiamiento
                if tipo == "Financiado":
                    try:
                        import financiamiento
                        financiamiento.abrir_gestion_financiamientos(
                            usuario=usuario,
                            id_contrato=id_contrato_nuevo,
                            monto_sugerido=precio,
                        )
                    except Exception as e:
                        messagebox.showerror("Error", f"No se pudo abrir financiamiento: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear el contrato: {e}", parent=form)

        tk.Button(form, text="Guardar contrato", width=20, command=guardar).pack(pady=20)

    def accion_ver_financiamiento():
        sel = tabla_contratos.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccione un contrato.")
            return
        valores = tabla_contratos.item(sel[0])["values"]
        id_contrato = valores[0]
        tipo = valores[7]
        if tipo != "Financiado":
            messagebox.showinfo("Info", "Este contrato no es financiado.")
            return
        try:
            import financiamiento
            financiamiento.abrir_gestion_financiamientos(usuario=usuario, id_contrato=id_contrato)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir financiamiento: {e}")

    # ---------- UI ----------
    frame_busqueda = tk.Frame(ventana_contratos, pady=10)
    frame_busqueda.pack(fill="x", padx=10)

    tk.Label(frame_busqueda, text="Buscar:").pack(side="left")
    entrada_busqueda = tk.Entry(frame_busqueda, width=22)
    entrada_busqueda.pack(side="left", padx=5)

    tk.Label(frame_busqueda, text="Estado:").pack(side="left", padx=(10, 0))
    combo_estado = ttk.Combobox(frame_busqueda, state="readonly", width=15,
                                 values=["Todos", "Activo", "Cancelado", "Finalizado"])
    combo_estado.current(0)
    combo_estado.pack(side="left", padx=5)

    tk.Button(frame_busqueda, text="Buscar", command=accion_buscar).pack(side="left", padx=5)
    tk.Button(frame_busqueda, text="Mostrar todos", command=accion_mostrar_todos).pack(side="left", padx=5)

    frame_tabla = tk.Frame(ventana_contratos)
    frame_tabla.pack(fill="both", expand=True, padx=10)

    columnas = ("ID", "Cliente", "Proyecto", "N° Lote", "Fecha", "Fin",
                "Precio", "Tipo", "Estado")
    tabla_contratos = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
    for col in columnas:
        tabla_contratos.heading(col, text=col)
        tabla_contratos.column(col, width=115, anchor="center")
    tabla_contratos.pack(fill="both", expand=True)

    frame_botones = tk.Frame(ventana_contratos, pady=10)
    frame_botones.pack(fill="x", padx=10)

    tk.Button(frame_botones, text="Crear contrato", width=16, command=accion_crear).pack(side="left", padx=5)
    tk.Button(frame_botones, text="Ver financiamiento", width=16, command=accion_ver_financiamiento).pack(side="left", padx=5)
    tk.Button(frame_botones, text="Cerrar", width=15, command=ventana_contratos.destroy).pack(side="right", padx=5)

    cargar_contratos()