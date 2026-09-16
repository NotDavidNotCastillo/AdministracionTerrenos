from database import conectar_bd
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date


def abrir_gestion_reservaciones(usuario=None):
    global ventana_reservaciones, tabla_reservaciones
    rol_de_usuario = usuario.get("NombreRol") if usuario else None
    nombre_usuario = usuario.get("NombreUsuario") if usuario else "Sistema"

    try:
        if ventana_reservaciones.winfo_exists():
            ventana_reservaciones.lift()
            ventana_reservaciones.focus_force()
            return
    except (NameError, tk.TclError):
        pass

    ventana_reservaciones = tk.Toplevel()
    ventana_reservaciones.geometry("1100x600")
    ventana_reservaciones.title("Gestión de Reservaciones")
    ventana_reservaciones.resizable(False, False)

    # ---------- Carga ----------
    def cargar_reservaciones(filtro=None, estado=None):
        for item in tabla_reservaciones.get_children():
            tabla_reservaciones.delete(item)
        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            query = """
                SELECT R.IdReservacion,
                       C.Nombre + ' ' + C.Apellido AS Cliente,
                       P.NombreProyecto, T.NombreTerreno, L.NumeroLote,
                       R.FechaReservacion, R.MontoReserva, R.Estado
                FROM Reservaciones R
                INNER JOIN Clientes C ON R.IdCliente = C.IdCliente
                INNER JOIN Lotes L ON R.IdLote = L.IdLote
                INNER JOIN Terrenos T ON L.IdTerreno = T.IdTerreno
                INNER JOIN Proyectos P ON T.IdProyecto = P.IdProyecto
                WHERE 1 = 1
            """
            params = []
            if estado and estado != "Todos":
                query += " AND R.Estado = ?"
                params.append(estado)
            if filtro:
                query += " AND (C.Nombre LIKE ? OR C.Apellido LIKE ? OR L.NumeroLote LIKE ?)"
                like = f"%{filtro}%"
                params.extend([like, like, like])
            query += " ORDER BY R.IdReservacion DESC"
            cursor.execute(query, params)
            for fila in cursor.fetchall():
                tabla_reservaciones.insert("", "end", values=fila)
            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar reservaciones: {e}")

    def accion_buscar():
        cargar_reservaciones(entrada_busqueda.get().strip() or None, combo_estado.get())

    def accion_mostrar_todos():
        entrada_busqueda.delete(0, "end")
        combo_estado.current(0)
        cargar_reservaciones()

    # ---------- Crear reservación ----------
    def accion_crear():
        form = tk.Toplevel(ventana_reservaciones)
        form.title("Crear Reservación")
        form.geometry("450x420")
        form.resizable(False, False)
        form.transient(ventana_reservaciones)
        form.grab_set()

        mapa_clientes = {}
        mapa_lotes = {}

        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute("SELECT IdCliente, Nombre, Apellido, Identidad FROM Clientes WHERE Estado = 1")
            for f in cursor.fetchall():
                mapa_clientes[f"{f[1]} {f[2]} ({f[3]})"] = f[0]
            cursor.execute("""
                SELECT L.IdLote, P.NombreProyecto, T.NombreTerreno, L.NumeroLote, L.Precio
                FROM Lotes L
                INNER JOIN Terrenos T ON L.IdTerreno = T.IdTerreno
                INNER JOIN Proyectos P ON T.IdProyecto = P.IdProyecto
                WHERE L.Estado = 'Disponible'
                ORDER BY P.NombreProyecto, L.NumeroLote
            """)
            for f in cursor.fetchall():
                mapa_lotes[f"{f[1]} - {f[2]} - Lote {f[3]} (L. {f[4]:,.2f})"] = (f[0], f[4])
            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos: {e}")

        tk.Label(form, text="Cliente:").pack(anchor="w", padx=15, pady=(15, 0))
        combo_cliente = ttk.Combobox(form, values=list(mapa_clientes.keys()),
                                     state="readonly", width=50)
        combo_cliente.pack(padx=15, pady=5, fill="x")

        tk.Label(form, text="Lote (solo disponibles):").pack(anchor="w", padx=15, pady=(5, 0))
        combo_lote = ttk.Combobox(form, values=list(mapa_lotes.keys()),
                                  state="readonly", width=50)
        combo_lote.pack(padx=15, pady=5, fill="x")

        tk.Label(form, text="Fecha de reservación (YYYY-MM-DD):").pack(anchor="w", padx=15, pady=(5, 0))
        entry_fecha = tk.Entry(form, width=50)
        entry_fecha.insert(0, str(date.today()))
        entry_fecha.pack(padx=15, pady=5, fill="x")

        tk.Label(form, text="Monto de reserva:").pack(anchor="w", padx=15, pady=(5, 0))
        entry_monto = tk.Entry(form, width=50)
        entry_monto.pack(padx=15, pady=5, fill="x")

        def guardar():
            if not combo_cliente.get() or not combo_lote.get():
                messagebox.showwarning("Validación", "Seleccione cliente y lote.", parent=form)
                return
            try:
                fecha = date.fromisoformat(entry_fecha.get().strip())
                monto = float(entry_monto.get().strip())
            except ValueError:
                messagebox.showwarning("Validación", "Fecha o monto inválidos.", parent=form)
                return

            id_cliente = mapa_clientes[combo_cliente.get()]
            id_lote = mapa_lotes[combo_lote.get()][0]

            try:
                conexion = conectar_bd()
                cursor = conexion.cursor()
                cursor.execute("""
                    INSERT INTO Reservaciones (IdCliente, IdLote, FechaReservacion,
                                               MontoReserva, Estado)
                    VALUES (?, ?, ?, ?, 'Activa')
                """, (id_cliente, id_lote, fecha, monto))
                cursor.execute("""
                    UPDATE Lotes SET Estado = 'Reservado', FechaEditado = ?, EditarPor = ?
                    WHERE IdLote = ?
                """, (date.today(), nombre_usuario, id_lote))
                conexion.commit()
                conexion.close()
                messagebox.showinfo("Éxito", "Reservación creada.", parent=form)
                form.destroy()
                cargar_reservaciones()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear: {e}", parent=form)

        tk.Button(form, text="Guardar", width=15, command=guardar).pack(pady=20)

    # ---------- Cancelar ----------
    def accion_cancelar():
        sel = tabla_reservaciones.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccione una reservación.")
            return
        valores = tabla_reservaciones.item(sel[0])["values"]
        id_reservacion = valores[0]
        estado_actual = valores[7]

        if estado_actual != "Activa":
            messagebox.showwarning("Aviso", "Solo se pueden cancelar reservaciones activas.")
            return
        if not messagebox.askyesno("Confirmar", f"¿Cancelar la reservación {id_reservacion}?"):
            return

        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute("SELECT IdLote FROM Reservaciones WHERE IdReservacion = ?", (id_reservacion,))
            id_lote = cursor.fetchone()[0]

            cursor.execute("UPDATE Reservaciones SET Estado = 'Cancelada' WHERE IdReservacion = ?",
                           (id_reservacion,))
            cursor.execute("""
                UPDATE Lotes SET Estado = 'Disponible', FechaEditado = ?, EditarPor = ?
                WHERE IdLote = ?
            """, (date.today(), nombre_usuario, id_lote))
            conexion.commit()
            conexion.close()
            messagebox.showinfo("Éxito", "Reservación cancelada.")
            cargar_reservaciones()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cancelar: {e}")

    # ---------- Convertir a contrato ----------
    def accion_convertir():
        sel = tabla_reservaciones.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccione una reservación.")
            return
        valores = tabla_reservaciones.item(sel[0])["values"]
        id_reservacion = valores[0]
        estado_actual = valores[7]
        if estado_actual != "Activa":
            messagebox.showwarning("Aviso", "Solo reservaciones activas pueden convertirse.")
            return

        try:
            conexion = conectar_bd()
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT IdCliente, IdLote, MontoReserva
                FROM Reservaciones WHERE IdReservacion = ?
            """, (id_reservacion,))
            id_cliente, id_lote, monto = cursor.fetchone()
            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")
            return

        # Abrimos el módulo de contratos
        try:
            import contrato
            contrato.abrir_gestion_contratos(
                usuario=usuario,
                id_cliente=id_cliente,
                id_lote=id_lote,
                monto_reserva=float(monto or 0),
                id_reservacion_origen=id_reservacion,
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir contratos: {e}")

    # ---------- UI ----------
    frame_busqueda = tk.Frame(ventana_reservaciones, pady=10)
    frame_busqueda.pack(fill="x", padx=10)

    tk.Label(frame_busqueda, text="Buscar:").pack(side="left")
    entrada_busqueda = tk.Entry(frame_busqueda, width=22)
    entrada_busqueda.pack(side="left", padx=5)

    tk.Label(frame_busqueda, text="Estado:").pack(side="left", padx=(10, 0))
    combo_estado = ttk.Combobox(frame_busqueda, state="readonly", width=15,
                                 values=["Todos", "Activa", "Cancelada", "Convertida"])
    combo_estado.current(0)
    combo_estado.pack(side="left", padx=5)

    tk.Button(frame_busqueda, text="Buscar", command=accion_buscar).pack(side="left", padx=5)
    tk.Button(frame_busqueda, text="Mostrar todos", command=accion_mostrar_todos).pack(side="left", padx=5)

    frame_tabla = tk.Frame(ventana_reservaciones)
    frame_tabla.pack(fill="both", expand=True, padx=10)

    columnas = ("ID", "Cliente", "Proyecto", "Terreno", "N° Lote",
                "Fecha", "Monto", "Estado")
    tabla_reservaciones = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
    for col in columnas:
        tabla_reservaciones.heading(col, text=col)
        tabla_reservaciones.column(col, width=130, anchor="center")
    tabla_reservaciones.pack(fill="both", expand=True)

    frame_botones = tk.Frame(ventana_reservaciones, pady=10)
    frame_botones.pack(fill="x", padx=10)

    tk.Button(frame_botones, text="Crear reservación", width=18, command=accion_crear).pack(side="left", padx=5)
    tk.Button(frame_botones, text="Cancelar reservación", width=18, command=accion_cancelar).pack(side="left", padx=5)
    tk.Button(frame_botones, text="Convertir a contrato", width=18, command=accion_convertir).pack(side="left", padx=5)
    tk.Button(frame_botones, text="Cerrar", width=15, command=ventana_reservaciones.destroy).pack(side="right", padx=5)

    cargar_reservaciones()