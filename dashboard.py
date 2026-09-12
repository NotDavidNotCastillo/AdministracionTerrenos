import tkinter as tk
from tkinter import ttk, messagebox
from database import conectar_bd

# ============================================================
# VENTANA PRINCIPAL DEL DASHBOARD
# ============================================================

class DashboardWindow:
    def __init__(self, root, usuario: dict, on_logout=None):
        self.root = root
        self.usuario = usuario
        self.on_logout = on_logout

        self.root.title("Dashboard - Administracion de Terrenos")
        self.root.geometry("1000x650")
        self.root.minsize(900, 600)

        self.modulos = {}   # nombre -> frame
        self.botones = {}   # nombre -> boton
        self.modulo_activo = None

        self._construir_ui()
        self._registrar_modulos()
        self.mostrar_modulo("inicio")

        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)

    # --------------------------------------------------------
    # CONSTRUCCION DE LA INTERFAZ
    # --------------------------------------------------------
    def _construir_ui(self):
        # -------- Encabezado --------
        header = ttk.Frame(self.root, padding=(10, 8))
        header.pack(fill="x")

        ttk.Label(
            header,
            text="Sistema de Administracion de Terrenos",
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left")

        info_frame = ttk.Frame(header)
        info_frame.pack(side="right")
        ttk.Label(
            info_frame,
            text=f"{self.usuario['NombreCompleto']} ({self.usuario['NombreRol']})",
            font=("Segoe UI", 10, "italic"),
        ).pack(anchor="e")
        ttk.Button(info_frame, text="Cerrar Sesion", command=self.cerrar_sesion).pack(
            anchor="e", pady=(3, 0)
        )

        ttk.Separator(self.root, orient="horizontal").pack(fill="x")

        # -------- Contenedor principal --------
        contenedor = ttk.Frame(self.root)
        contenedor.pack(fill="both", expand=True)

        # -------- Menu lateral --------
        self.menu_frame = ttk.Frame(contenedor, width=210, padding=10)
        self.menu_frame.pack(side="left", fill="y")
        self.menu_frame.pack_propagate(False)

        ttk.Label(
            self.menu_frame, text="Modulos", font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 10))

        ttk.Separator(contenedor, orient="vertical").pack(side="left", fill="y")

        # -------- Area de contenido --------
        self.area_contenido = ttk.Frame(contenedor, padding=15)
        self.area_contenido.pack(side="left", fill="both", expand=True)

        # -------- Barra de estado --------
        self.status_var = tk.StringVar(value="Listo.")
        status = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w",
            padding=(5, 3),
        )
        status.pack(fill="x", side="bottom")

    # --------------------------------------------------------
    # REGISTRO DE MODULOS (ESCALABLE)
    # --------------------------------------------------------
    def _registrar_modulos(self):
        """
        Aqui se registran todos los modulos del sistema.
        Para agregar uno nuevo solo debes:
          1. Crear una clase ModuloXxx(ttk.Frame) mas abajo.
          2. Registrarla aqui con self.registrar_modulo(nombre, clase, titulo).
        """
        self.registrar_modulo("inicio", ModuloInicio, "Inicio")
        self.registrar_modulo("clientes", ModuloClientes, "Clientes")
        self.registrar_modulo("proyectos", ModuloProyectos, "Proyectos")
        self.registrar_modulo("lotes", ModuloLotes, "Lotes")
        self.registrar_modulo("contratos", ModuloContratos, "Contratos")

    def registrar_modulo(self, nombre: str, clase_modulo, titulo: str):
        """Crea el frame del modulo y su boton en el menu."""
        frame = clase_modulo(
            self.area_contenido,
            usuario=self.usuario,
            dashboard=self,
        )
        frame.grid(row=0, column=0, sticky="nsew")
        self.modulos[nombre] = frame

        boton = ttk.Button(
            self.menu_frame,
            text=titulo,
            width=25,
            command=lambda n=nombre: self.mostrar_modulo(n),
        )
        boton.pack(fill="x", pady=3)
        self.botones[nombre] = boton

        # Permitir que el grid del area de contenido se expanda
        self.area_contenido.grid_rowconfigure(0, weight=1)
        self.area_contenido.grid_columnconfigure(0, weight=1)

    # --------------------------------------------------------
    # NAVEGACION
    # --------------------------------------------------------
    def mostrar_modulo(self, nombre: str):
        if nombre not in self.modulos:
            return

        frame = self.modulos[nombre]
        frame.tkraise()
        self.modulo_activo = nombre
        self.status_var.set(f"Modulo activo: {nombre.capitalize()}")

        # Si el modulo tiene un metodo on_show, lo ejecutamos para refrescar datos
        if hasattr(frame, "on_show"):
            try:
                frame.on_show()
            except Exception as e:
                self.status_var.set(f"Error al refrescar {nombre}: {e}")

    # --------------------------------------------------------
    # CIERRE DE SESION
    # --------------------------------------------------------
    def cerrar_sesion(self):
        if not messagebox.askyesno("Cerrar sesion", "Desea cerrar la sesion?"):
            return
        self.root.destroy()
        if self.on_logout:
            self.on_logout()

    def cerrar_ventana(self):
        if messagebox.askyesno("Salir", "Desea salir del sistema?"):
            self.root.destroy()
            if self.on_logout:
                self.on_logout()


# ============================================================
# MODULO BASE (para reutilizar)
# ============================================================
class ModuloBase(ttk.Frame):
    """
    Clase base para todos los modulos del dashboard.
    Provee: titulo, conexion, helpers de tabla y barra de estado.
    """
    titulo = "Modulo"

    def __init__(self, parent, usuario: dict, dashboard: "DashboardWindow"):
        super().__init__(parent, padding=10)
        self.usuario = usuario
        self.dashboard = dashboard
        self._construir_encabezado()

    def _construir_encabezado(self):
        ttk.Label(
            self, text=self.titulo, font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", pady=(0, 10))

    # ---- Helpers ----
    def conectar(self):
        return conectar_bd()

    def set_status(self, texto: str):
        if self.dashboard:
            self.dashboard.status_var.set(texto)

    def crear_tabla(self, columnas: list, anchos: list = None):
        """
        Crea un Treeview con scroll vertical.
        columnas: lista de nombres de columna.
        Retorna el treeview.
        """
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(frame, columns=columnas, show="headings")
        for i, col in enumerate(columnas):
            tree.heading(col, text=col)
            ancho = anchos[i] if anchos and i < len(anchos) else 120
            tree.column(col, width=ancho, anchor="w")

        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)

        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tree


# ============================================================
# MODULO: INICIO
# ============================================================
class ModuloInicio(ModuloBase):
    titulo = "Panel de Inicio"

    def __init__(self, parent, usuario, dashboard):
        super().__init__(parent, usuario, dashboard)

        bienvenida = ttk.LabelFrame(self, text="Bienvenido", padding=15)
        bienvenida.pack(fill="x", pady=10)

        ttk.Label(
            bienvenida,
            text=f"Usuario: {usuario['NombreCompleto']}",
            font=("Segoe UI", 11),
        ).pack(anchor="w")
        ttk.Label(
            bienvenida,
            text=f"Rol: {usuario['NombreRol']}",
            font=("Segoe UI", 11),
        ).pack(anchor="w")
        ttk.Label(
            bienvenida,
            text=f"Correo: {usuario['Correo']}",
            font=("Segoe UI", 11),
        ).pack(anchor="w")

        stats = ttk.LabelFrame(self, text="Resumen del sistema", padding=15)
        stats.pack(fill="both", expand=True, pady=10)

        self.lbl_stats = ttk.Label(stats, text="Cargando...", font=("Consolas", 10))
        self.lbl_stats.pack(anchor="w")

        self.on_show()

    def on_show(self):
        try:
            conn = self.conectar()
            cur = conn.cursor()
            resumen = {}
            for etiqueta, sql in [
                ("Clientes", "SELECT COUNT(*) FROM dbo.Clientes WHERE Activo = 1"),
                ("Proyectos", "SELECT COUNT(*) FROM dbo.Proyectos"),
                ("Terrenos", "SELECT COUNT(*) FROM dbo.Terrenos"),
                ("Lotes", "SELECT COUNT(*) FROM dbo.Lotes"),
                ("Contratos", "SELECT COUNT(*) FROM dbo.Contratos"),
                ("Reservaciones", "SELECT COUNT(*) FROM dbo.Reservaciones"),
            ]:
                cur.execute(sql)
                resumen[etiqueta] = cur.fetchone()[0]

            cur.close()
            conn.close()

            texto = "\n".join(f"{k:.<25}{v:>6}" for k, v in resumen.items())
            self.lbl_stats.config(text=texto)
        except Exception as e:
            self.lbl_stats.config(text=f"Error: {e}")


# ============================================================
# MODULO: CLIENTES (ejemplo funcional completo)
# ============================================================
class ModuloClientes(ModuloBase):
    titulo = "Gestion de Clientes"

    def __init__(self, parent, usuario, dashboard):
        super().__init__(parent, usuario, dashboard)

        # Barra de acciones
        barra = ttk.Frame(self)
        barra.pack(fill="x", pady=(0, 8))

        ttk.Label(barra, text="Buscar:").pack(side="left")
        self.entry_buscar = ttk.Entry(barra, width=30)
        self.entry_buscar.pack(side="left", padx=5)
        self.entry_buscar.bind("<Return>", lambda e: self.cargar())

        ttk.Button(barra, text="Buscar", command=self.cargar).pack(side="left", padx=2)
        ttk.Button(barra, text="Refrescar", command=self.cargar).pack(side="left", padx=2)

        # Tabla
        cols = ("Id", "Identidad", "Nombres", "Apellidos", "Telefono", "Correo", "Activo")
        self.tree = self.crear_tabla(cols, anchos=[50, 110, 130, 130, 100, 180, 60])

        self.on_show()

    def on_show(self):
        self.cargar()

    def cargar(self):
        filtro = self.entry_buscar.get().strip()
        try:
            conn = self.conectar()
            cur = conn.cursor()

            if filtro:
                like = f"%{filtro}%"
                cur.execute(
                    """
                    SELECT IdCliente, Identidad, Nombres, Apellidos,
                           Telefono, Correo, Activo
                    FROM dbo.Clientes
                    WHERE Identidad LIKE ? OR Nombres LIKE ? OR Apellidos LIKE ?
                    ORDER BY IdCliente DESC
                    """,
                    (like, like, like),
                )
            else:
                cur.execute(
                    """
                    SELECT TOP 200 IdCliente, Identidad, Nombres, Apellidos,
                           Telefono, Correo, Activo
                    FROM dbo.Clientes
                    ORDER BY IdCliente DESC
                    """
                )

            filas = cur.fetchall()
            cur.close()
            conn.close()

            # Limpiar tabla
            for item in self.tree.get_children():
                self.tree.delete(item)

            for f in filas:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        f[0], f[1], f[2], f[3],
                        f[4] or "", f[5] or "",
                        "Si" if f[6] else "No",
                    ),
                )

            self.set_status(f"Clientes cargados: {len(filas)}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los clientes:\n{e}")


# ============================================================
# MODULO: PROYECTOS (placeholder listo para escalar)
# ============================================================
class ModuloProyectos(ModuloBase):
    titulo = "Gestion de Proyectos"

    def __init__(self, parent, usuario, dashboard):
        super().__init__(parent, usuario, dashboard)

        ttk.Button(self, text="Refrescar", command=self.cargar).pack(anchor="w", pady=5)

        cols = ("Id", "Codigo", "Nombre", "Municipio", "Estado", "FechaInicio")
        self.tree = self.crear_tabla(cols, anchos=[50, 100, 200, 150, 100, 100])

    def on_show(self):
        self.cargar()

    def cargar(self):
        try:
            conn = self.conectar()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT p.IdProyecto, p.CodigoProyecto, p.Nombre,
                       m.Nombre AS Municipio, p.Estado, p.FechaInicio
                FROM dbo.Proyectos p
                LEFT JOIN dbo.Municipios m ON p.IdMunicipio = m.IdMunicipio
                ORDER BY p.IdProyecto DESC
                """
            )
            filas = cur.fetchall()
            cur.close()
            conn.close()

            for item in self.tree.get_children():
                self.tree.delete(item)
            for f in filas:
                self.tree.insert(
                    "", "end",
                    values=(f[0], f[1], f[2], f[3] or "", f[4], f[5] or ""),
                )
            self.set_status(f"Proyectos cargados: {len(filas)}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los proyectos:\n{e}")


# ============================================================
# MODULO: LOTES
# ============================================================
class ModuloLotes(ModuloBase):
    titulo = "Gestion de Lotes"

    def __init__(self, parent, usuario, dashboard):
        super().__init__(parent, usuario, dashboard)

        ttk.Button(self, text="Refrescar", command=self.cargar).pack(anchor="w", pady=5)

        cols = ("Id", "Codigo", "Terreno", "Manzana", "Lote", "Area", "Precio", "Estado")
        self.tree = self.crear_tabla(
            cols, anchos=[50, 100, 150, 80, 70, 90, 110, 110]
        )

    def on_show(self):
        self.cargar()

    def cargar(self):
        try:
            conn = self.conectar()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT l.IdLote, l.CodigoLote, t.Nombre AS Terreno,
                       l.Manzana, l.NumeroLote, l.AreaLote, l.PrecioBase,
                       e.Nombre AS Estado
                FROM dbo.Lotes l
                INNER JOIN dbo.Terrenos t ON l.IdTerreno = t.IdTerreno
                INNER JOIN dbo.EstadosLote e ON l.IdEstadoLote = e.IdEstadoLote
                ORDER BY l.IdLote DESC
                """
            )
            filas = cur.fetchall()
            cur.close()
            conn.close()

            for item in self.tree.get_children():
                self.tree.delete(item)
            for f in filas:
                self.tree.insert(
                    "", "end",
                    values=(
                        f[0], f[1], f[2] or "", f[3] or "", f[4] or "",
                        f"{f[5]:,.2f}", f"{f[6]:,.2f}", f[7],
                    ),
                )
            self.set_status(f"Lotes cargados: {len(filas)}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los lotes:\n{e}")


# ============================================================
# MODULO: CONTRATOS
# ============================================================
class ModuloContratos(ModuloBase):
    titulo = "Gestion de Contratos"

    def __init__(self, parent, usuario, dashboard):
        super().__init__(parent, usuario, dashboard)

        ttk.Button(self, text="Refrescar", command=self.cargar).pack(anchor="w", pady=5)

        cols = ("Id", "Numero", "Cliente", "Lote", "Fecha", "Monto", "Estado")
        self.tree = self.crear_tabla(
            cols, anchos=[50, 120, 180, 120, 100, 110, 110]
        )

    def on_show(self):
        self.cargar()

    def cargar(self):
        try:
            conn = self.conectar()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT c.IdContrato, c.NumeroContrato,
                       (cl.Nombres + ' ' + cl.Apellidos) AS Cliente,
                       l.CodigoLote, c.FechaContrato, c.MontoTotal,
                       e.Nombre AS Estado
                FROM dbo.Contratos c
                INNER JOIN dbo.Clientes cl ON c.IdCliente = cl.IdCliente
                INNER JOIN dbo.Lotes l ON c.IdLote = l.IdLote
                INNER JOIN dbo.EstadosContrato e ON c.IdEstadoContrato = e.IdEstadoContrato
                ORDER BY c.IdContrato DESC
                """
            )
            filas = cur.fetchall()
            cur.close()
            conn.close()

            for item in self.tree.get_children():
                self.tree.delete(item)
            for f in filas:
                self.tree.insert(
                    "", "end",
                    values=(
                        f[0], f[1], f[2], f[3] or "", f[4] or "",
                        f"{f[5]:,.2f}", f[6],
                    ),
                )
            self.set_status(f"Contratos cargados: {len(filas)}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los contratos:\n{e}")


# ============================================================
# PRUEBA INDEPENDIENTE DEL DASHBOARD
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    usuario_prueba = {
        "IdUsuario": 1,
        "NombreUsuario": "admin",
        "NombreCompleto": "Administrador de Prueba",
        "Correo": "admin@local",
        "IdRol": 1,
        "NombreRol": "Administrador",
    }
    DashboardWindow(root, usuario=usuario_prueba)
    root.mainloop()