from database import conectar_bd # conexion a base de datos 
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from decimal import Decimal


# Variables globales 
ventana_reportes = None
tabla_reportes = None
combo_reporte = None
label_total = None
entry_filtro = None
filas_actuales = []  # guarda las filas ya formateadas para poder filtrarlas


def formatear_celda(valor):
    """Da formato de presentación a un valor proveniente de la BD."""
    if valor is None:
        return ""
    if isinstance(valor, (date, datetime)):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, Decimal):
        return f"L. {valor:,.2f}"
    return str(valor)


def generar_reporte():
    global filas_actuales

    nombre_reporte = combo_reporte.get()
    if not nombre_reporte:
        messagebox.showwarning("Reportes", "Seleccione un tipo de reporte.")
        return

    reporte = REPORTES[nombre_reporte]

    # Actualizar columnas de tabla segun el reporte 
    columnas = [c[0] for c in reporte["columnas"]]
    tabla_reportes["columns"] = columnas
    tabla_reportes["show"] = "headings"
    for encabezado, ancho in reporte["columnas"]:
        tabla_reportes.heading(encabezado, text=encabezado)
        tabla_reportes.column(encabezado, width=ancho, anchor="center")

    tabla_reportes.delete(*tabla_reportes.get_children())

    conexion = None
    try:
        conexion = conectar_bd()
        cursor = conexion.cursor()
        cursor.execute(reporte["query"])
        filas = cursor.fetchall()

        filas_actuales = []
        for row in filas:
            valores = [formatear_celda(row[i]) for i in range(len(columnas))]
            filas_actuales.append(valores)

        pintar_filas(filas_actuales)
        label_total.config(text=f"Total de registros: {len(filas_actuales)}")

    except Exception as error:
        messagebox.showerror("Error", f"No se pudo generar el reporte:\n{error}")
    finally:
        if conexion:
            conexion.close()


def pintar_filas(filas):
    tabla_reportes.delete(*tabla_reportes.get_children())
    for indice, valores in enumerate(filas):
        etiqueta = "par" if indice % 2 == 0 else "impar"
        tabla_reportes.insert("", tk.END, values=valores, tags=(etiqueta,))


def filtrar_tabla(*_):
    texto = entry_filtro.get().strip().lower()
    if not texto:
        pintar_filas(filas_actuales)
        return
    filtradas = [
        fila for fila in filas_actuales
        if any(texto in str(valor).lower() for valor in fila)
    ]
    pintar_filas(filtradas)
    label_total.config(text=f"Total de registros: {len(filtradas)}")


def abrir_reportes():
    global ventana_reportes, tabla_reportes, combo_reporte, label_total, entry_filtro

    try:
        if ventana_reportes is not None and ventana_reportes.winfo_exists():
            ventana_reportes.lift()
            ventana_reportes.focus_force()
            return
    except (NameError, AttributeError, tk.TclError):
        pass

    ventana_reportes = tk.Toplevel()
    ventana_reportes.title("LotesDB - Reportes")
    ventana_reportes.geometry("1000x600")
    ventana_reportes.resizable(False, False)

    #  Panel superior: selección de reporte 
    panel_superior = tk.Frame(ventana_reportes, padx=10, pady=10)
    panel_superior.pack(fill="x")

    tk.Label(panel_superior, text="Tipo de reporte:").grid(row=0, column=0, padx=(0, 5))
    combo_reporte = ttk.Combobox(
        panel_superior, values=list(REPORTES.keys()), state="readonly", width=25
    )
    combo_reporte.grid(row=0, column=1, padx=(0, 15))
    combo_reporte.current(0)

    tk.Button(panel_superior, text="Generar reporte", command=generar_reporte).grid(
        row=0, column=2, padx=(0, 15)
    )

    tk.Label(panel_superior, text="Buscar:").grid(row=0, column=3, padx=(0, 5))
    entry_filtro = tk.Entry(panel_superior, width=25)
    entry_filtro.grid(row=0, column=4)
    entry_filtro.bind("<KeyRelease>", filtrar_tabla)

    #  Panel central: tabla de resultados 
    panel_tabla = tk.Frame(ventana_reportes)
    panel_tabla.pack(fill="both", expand=True, padx=10, pady=(0, 5))

    scroll_y = ttk.Scrollbar(panel_tabla, orient="vertical")
    scroll_x = ttk.Scrollbar(panel_tabla, orient="horizontal")

    tabla_reportes = ttk.Treeview(
        panel_tabla,
        yscrollcommand=scroll_y.set,
        xscrollcommand=scroll_x.set,
    )
    scroll_y.config(command=tabla_reportes.yview)
    scroll_x.config(command=tabla_reportes.xview)

    tabla_reportes.tag_configure("par", background="#f2f2f2")
    tabla_reportes.tag_configure("impar", background="#ffffff")

    scroll_y.pack(side="right", fill="y")
    scroll_x.pack(side="bottom", fill="x")
    tabla_reportes.pack(fill="both", expand=True)

    # ---------------- Panel inferior: total y cerrar ----------------
    panel_inferior = tk.Frame(ventana_reportes, padx=10, pady=8)
    panel_inferior.pack(fill="x")

    label_total = tk.Label(panel_inferior, text="Total de registros: 0")
    label_total.pack(side="left")

    tk.Button(panel_inferior, text="Cerrar", command=ventana_reportes.destroy).pack(
        side="right"
    )

    # Generar el primer reporte (Clientes) automáticamente al abrir
    generar_reporte()

REPORTES = {
    "Clientes": {
        "columnas": [
            ("ID", 40), ("Nombre", 110), ("Apellido", 110), ("Identidad", 130),
            ("Teléfono", 90), ("Correo", 160), ("Ciudad", 100), ("Estado", 80),
        ],
        "query": """
            SELECT c.IdCliente, c.Nombre, c.Apellido, c.Identidad, c.Telefono,
                   c.Correo, ci.NombreCiudad,
                   CASE WHEN c.Estado = 1 THEN 'Activo' ELSE 'Inactivo' END
            FROM Clientes c
            INNER JOIN Ciudades ci ON c.IdCiudad = ci.IdCiudad
            ORDER BY c.IdCliente
        """,
    },
    "Contratos": {
        "columnas": [
            ("ID", 40), ("Cliente", 160), ("Lote", 60), ("F. Contrato", 90),
            ("F. Fin", 90), ("Precio Venta", 100), ("Tipo Venta", 90), ("Estado", 80),
        ],
        "query": """
            SELECT co.IdContrato, cl.Nombre + ' ' + cl.Apellido, l.NumeroLote,
                   co.FechaContrato, co.FinContrato, co.PrecioVenta,
                   co.TipoVenta, co.Estado
            FROM Contratos co
            INNER JOIN Clientes cl ON co.IdCliente = cl.IdCliente
            INNER JOIN Lotes l ON co.IdLote = l.IdLote
            ORDER BY co.IdContrato
        """,
    },
    "Lotes": {
        "columnas": [
            ("ID", 40), ("Terreno", 110), ("Proyecto", 150), ("Lote", 60),
            ("Área", 80), ("Precio", 100), ("Estado", 90),
        ],
        "query": """
            SELECT l.IdLote, t.NombreTerreno, p.NombreProyecto, l.NumeroLote,
                   l.Area, l.Precio, l.Estado
            FROM Lotes l
            INNER JOIN Terrenos t ON l.IdTerreno = t.IdTerreno
            INNER JOIN Proyectos p ON t.IdProyecto = p.IdProyecto
            ORDER BY l.IdLote
        """,
    },
    "Cuotas pendientes": {
        "columnas": [
            ("ID", 40), ("Cliente", 160), ("Contrato", 70), ("# Cuota", 60),
            ("Vencimiento", 90), ("Monto", 90), ("Estado", 100),
        ],
        "query": """
            SELECT cu.IdCuota, cl.Nombre + ' ' + cl.Apellido, co.IdContrato,
                   cu.NumeroCuota, cu.FechaVencimiento, cu.Monto, cu.Estado
            FROM Cuotas cu
            INNER JOIN Financiamientos f ON cu.IdFinanciamiento = f.IdFinanciamiento
            INNER JOIN Contratos co ON f.IdContrato = co.IdContrato
            INNER JOIN Clientes cl ON co.IdCliente = cl.IdCliente
            WHERE cu.Estado <> 'Pagada'
            ORDER BY cu.FechaVencimiento
        """,
    },
    "Abonos": {
        "columnas": [
            ("ID", 40), ("Cliente", 160), ("# Cuota", 60), ("Fecha Abono", 90),
            ("Monto Abonado", 100),
        ],
        "query": """
            SELECT a.IdAbono, cl.Nombre + ' ' + cl.Apellido, cu.NumeroCuota,
                   a.FechaAbono, a.MontoAbonado
            FROM Abonos a
            INNER JOIN Cuotas cu ON a.IdCuota = cu.IdCuota
            INNER JOIN Financiamientos f ON cu.IdFinanciamiento = f.IdFinanciamiento
            INNER JOIN Contratos co ON f.IdContrato = co.IdContrato
            INNER JOIN Clientes cl ON co.IdCliente = cl.IdCliente
            ORDER BY a.FechaAbono DESC
        """,
    },
    "Reservaciones": {
        "columnas": [
            ("ID", 40), ("Cliente", 160), ("Lote", 60), ("F. Reservación", 100),
            ("Monto", 90), ("Estado", 90),
        ],
        "query": """
            SELECT r.IdReservacion, cl.Nombre + ' ' + cl.Apellido, l.NumeroLote,
                   r.FechaReservacion, r.MontoReserva, r.Estado
            FROM Reservaciones r
            INNER JOIN Clientes cl ON r.IdCliente = cl.IdCliente
            INNER JOIN Lotes l ON r.IdLote = l.IdLote
            ORDER BY r.IdReservacion
        """,
    },
    "Proyectos": {
        "columnas": [
            ("ID", 40), ("Proyecto", 180), ("Ubicación", 150), ("F. Inicio", 90),
            ("F. Final", 90), ("Estado", 100),
        ],
        "query": """
            SELECT IdProyecto, NombreProyecto, Ubicacion, FechaInicio,
                   FechaFinal, Estado
            FROM Proyectos
            ORDER BY IdProyecto
        """,
    },
}



# if __name__ == "__main__":
#     root = tk.Tk()
#     root.withdraw()
#     abrir_reportes()
#     root.mainloop()