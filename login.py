import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
from dashboard import abrir_dashboard
from database import conectar_bd


# ============================================================
# UTILIDADES DE SEGURIDAD
# ============================================================
def hashear_clave(clave: str) -> bytes:
    """Genera un hash SHA-256 de la contrasena."""
    return hashlib.sha256(clave.encode("utf-8")).digest()


# ============================================================
# VENTANA DE LOGIN
# ============================================================
class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Inicio de Sesion - Administracion de Terrenos")
        self.root.geometry("420x320")
        self.root.resizable(False, False)

        self._construir_ui()

    def _construir_ui(self):
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="Sistema de Administracion de Terrenos",
            font=("Segoe UI", 12, "bold"),
        ).pack(pady=(0, 20))

        ttk.Label(frame, text="Usuario:").pack(anchor="w")
        self.entry_usuario = ttk.Entry(frame, width=40)
        self.entry_usuario.pack(pady=(0, 10))

        ttk.Label(frame, text="Contrasena:").pack(anchor="w")
        self.entry_clave = ttk.Entry(frame, width=40, show="*")
        self.entry_clave.pack(pady=(0, 20))

        self.entry_clave.bind("<Return>", lambda e: self.iniciar_sesion())
        self.entry_usuario.focus_set()

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")

        ttk.Button(
            btn_frame, text="Iniciar Sesion", command=self.iniciar_sesion
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ttk.Button(
            btn_frame, text="Salir", command=self.root.destroy
        ).pack(side="left", expand=True, fill="x", padx=(5, 0))


    def iniciar_sesion(self):
        usuario = self.entry_usuario.get().strip()
        clave = self.entry_clave.get().strip()

        if not usuario or not clave:
            messagebox.showwarning(
                "Campos vacios", "Debe ingresar usuario y contrasena."
            )
            return

        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            cursor.execute(
                """
                select u.IdUsuario,u.IdRol,u.Usuario,u.correo,r.NombreRol,u.Clave 
                    from Usuarios u
                inner join Roles r on r.IdRol = u.IdRol 
                where u.Usuario = ? and u.Estado = 1
                """,
                (usuario,),
            )
            fila = cursor.fetchone()

            if fila is None:
                messagebox.showerror("Error", "Usuario no encontrado o inactivo.")
                return

            id_usuario, id_rol, nombre_usuario, correo, nombre_rol, clave_hash = fila

            # Comparar hash
            clave_ingresada = hashear_clave(clave)
            clave_bd = bytes(clave_hash) if clave_hash is not None else b""

            if clave_ingresada != clave_bd:
                messagebox.showerror("Error", "Contrasena incorrecta.")
                return

            # Actualizar ultimo acceso
            cursor.execute(
                "UPDATE dbo.Usuarios SET UltimoAcceso = GETDATE() WHERE IdUsuario = ?",
                (id_usuario,),
            )
            conn.commit()
            cursor.close()
            conn.close()

            # Abrir dashboard
            self.root.withdraw()

            # id_usuario, id_rol, name_usuario, correo, nombre_rol, clave_hash

            ventana_dash = abrir_dashboard(usuario={
                "IdUsuario": id_usuario,
                "IdRol": id_rol,
                "NombreUsuario": nombre_usuario,
                "Correo": correo,
                "NombreRol": nombre_rol,
            })

            ventana_dash.protocol(
                "WM_DELETE_WINDOW",
                lambda: (ventana_dash.destroy(), self.cerrar_sesion())
                )

        except Exception as e:
            messagebox.showerror("Error de conexion", f"Detalle:\n{e}")

    def cerrar_sesion(self):
        """Callback llamado desde el dashboard al cerrar sesion."""
        self.root.deiconify()
        self.entry_clave.delete(0, tk.END)
        self.entry_usuario.focus_set()


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()