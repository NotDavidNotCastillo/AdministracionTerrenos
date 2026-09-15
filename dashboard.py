import tkinter as tk

from tkinter import messagebox
from database import conectar_bd

def abrir_dashboard(usuario=None):

    """Crea y muestra la ventana principal del sistema."""
    ventana = tk.Toplevel()
    ventana.title("DashBoard")
    ventana.geometry("700x600")
    ventana.resizable(True,True)    

    def salir():
      #  LoginWindow.cerrar_sesion()
       root.quit()

    
    titulo = tk.Label(ventana, text="Sistema de Gestion de Terrenos", font=("Arial",25,"bold"))
    titulo.pack (pady=(50,5))

    subtitulo = tk.Label(
        ventana, 
        text=f"Bienvenido, {usuario.get('NombreUsuario','')}" if usuario else "Bienvenido",
        font=("Arial",14)
    )
    subtitulo.pack(pady=(0,40))

    # ==========
    # Filas
    # ==========
    uno_fila = tk.Frame(ventana)
    uno_fila.pack(pady=8)

    dos_fila = tk.Frame(ventana)
    dos_fila.pack(pady=8)

    tres_fila = tk.Frame(ventana)
    tres_fila.pack(pady=8)

    cuatro_fila = tk.Frame(ventana)
    cuatro_fila.pack(pady=8)

    # ==============================
    # Botones dentro de las filas
    # ==============================
    cliente = tk.Button(uno_fila, 
              text="Clientes", 
              font=("Arial",13),
              width=25, height=2,
              activebackground='light gray'
            #   command=lambda: abrir_clientes(usuario)
              ).pack(side="left",padx=4)

    proyecto = tk.Button(uno_fila, 
              text="Proyectos", 
              font=("Arial",13),
              width=25, height=2,
              activebackground='light gray'
            #   command=lambda: abrir_ciudades(usuario)
              ).pack(side="right",padx=4)

    lotes = tk.Button(dos_fila, 
              text="Lotes", 
              font=("Arial",13),
              width=25, height=2, 
              activebackground='light gray'
            #   command=abrir_reportes
              ).pack(side="left",padx=4)
    
    reserva = tk.Button(dos_fila, 
                  text="Reservaciones", 
                  font=("Arial",13),
                  width=25, height=2,
                  activebackground='light gray'
                #   command=abrir_reportes
                  ).pack(side="right",padx=4)

    contrato = tk.Button(tres_fila, 
                  text="Contratos", 
                  font=("Arial",13),
                  width=25, height=2,
                  activebackground='light gray'
                #   command=abrir_reportes
                  ).pack(side="left",padx=4)
    
    financiamiento = tk.Button(tres_fila, 
                  text="Financiamiento", 
                  font=("Arial",13),
                  width=25, height=2,
                  activebackground='light gray'
                #   command=abrir_reportes
                  ).pack(side="right",padx=4)

    pago = tk.Button(cuatro_fila, 
                  text="Pagos", 
                  font=("Arial",13),
                  width=25, height=2,
                  activebackground='light gray'
                #   command=abrir_reportes
                  ).pack(side="left",padx=4)
    
    reporte = tk.Button(cuatro_fila, 
                  text="Reportes", 
                  font=("Arial",13),
                  width=25, height=2,
                  activebackground='light gray'
                #   command=abrir_reportes
                  ).pack(side="right",padx=4)

    cerrar = tk.Button(ventana, 
              text="Salir", 
              font=("Arial",13),
              width=25, height=2,
              activebackground='light gray',
              command=salir
              ).pack(pady=8,padx=4)

    return ventana


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    abrir_dashboard()
    root.mainloop()