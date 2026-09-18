import tkinter as tk
from database import conectar_bd
from cliente import abrir_clientes
from proyecto import abrir_proyecto
from terreno import abrir_terrenos
from lote import abrir_lote
from reservacion import abrir_reservacion
from contrato import abrir_contrato
from financiamiento import abrir_financiamiento
from gestion_pago import abrir_gestion_pagos
from cuota import abrir_gestion_cuotas
from reporte import abrir_reportes
from gestionar_usuarios import abrir_usuarios

def abrir_dashboard(usuario=None):

    """Crea y muestra la ventana principal del sistema."""
    ventana = tk.Toplevel()
    ventana.title("DashBoard")
    ventana.geometry("700x600")
    ventana.resizable(True,True)

    user = usuario.get("NombreRol") if usuario else "Sistema"

    print(user)

    # print(usuario.get("NombreUsuario"))

    def salir():
      #  LoginWindow.cerrar_sesion()
       ventana.quit()

    
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

    cinco_fila = tk.Frame(ventana)
    cinco_fila.pack(pady=8)

    seis_fila = tk.Frame(ventana)
    seis_fila.pack(pady=8)

    # ==============================
    # Botones dentro de las filas
    cliente = tk.Button(uno_fila, 
              text="Clientes", 
              font=("Arial",13),
              width=25, height=2,
              activebackground='light gray',
              command=lambda: abrir_clientes(usuario),
              ).pack(side="left",padx=4)

    proyecto = tk.Button(uno_fila, 
              text="Proyectos", 
              font=("Arial",13),
              width=25, height=2,
              activebackground='light gray',
              command=lambda: abrir_proyecto(usuario),
              ).pack(side="right",padx=4)

    lotes = tk.Button(dos_fila, 
              text="Lotes", 
              font=("Arial",13),
              width=25, height=2, 
              activebackground='light gray',
              command=lambda: abrir_lote(usuario=usuario)
              ).pack(side="left",padx=4)
    
    terrenos = tk.Button(dos_fila, 
              text="Terrenos", 
              font=("Arial",13),
              width=25, height=2, 
              activebackground='light gray',
              command=lambda: abrir_terrenos(usuario=usuario),
              ).pack(side="right",padx=4)
    
    reserva = tk.Button(tres_fila, 
                  text="Reservaciones", 
                  font=("Arial",13),
                  width=25, height=2,
                  activebackground='light gray',
                  command=lambda: abrir_reservacion(usuario=usuario)
                  ).pack(side="right",padx=4)

    contrato = tk.Button(tres_fila, 
                  text="Contratos", 
                  font=("Arial",13),
                  width=25, height=2,
                  activebackground='light gray',
                  command=lambda: abrir_contrato(usuario=usuario)
                  ).pack(side="left",padx=4)

    gestion_pago = tk.Button(cuatro_fila, 
                  text="Realizar Pagos", 
                  font=("Arial",13),
                  width=25, height=2,
                  activebackground='light gray',
                  command=lambda: abrir_gestion_pagos()
                  ).pack(side="left",padx=4)

    cuotas = tk.Button(cuatro_fila, 
                  text="Revisar Cuotas", 
                  font=("Arial",13),
                  width=25, height=2,
                  activebackground='light gray',
                  command=lambda: abrir_gestion_cuotas()
                  ).pack(side="right",padx=4)

    financiamiento = tk.Button(cinco_fila, 
                  text="Financiamiento", 
                  font=("Arial",13),
                  width=25, height=2,
                  activebackground='light gray',
                  command=lambda: abrir_financiamiento(usuario=usuario)
                  ).pack(side="right",padx=4)

    reporte = tk.Button(cinco_fila, 
                  text="Reportes", 
                  font=("Arial",13),
                  width=25, height=2,
                  activebackground='light gray',
                  command=lambda: abrir_reportes()
                  )

    gestionar_usuarios = tk.Button(seis_fila,
                             text="Usuarios",
                             font=("Arial",13),
                             width=25,height=2,
                             activebackground='light gray',
                             command = lambda: abrir_usuarios()
                             )

    cerrar = tk.Button(seis_fila, 
              text="Salir", 
              font=("Arial",13),
              width=25, height=2,
              background="#ff5151",
              activebackground="#fab1b1",
              command=salir
              ).pack(side="right",padx=4) #side='right',padx=4

    estado = ""

    estado = "normal" if user == "administrador" else "disabled"

    reporte.config(state=estado)
    gestionar_usuarios.config(state=estado)

    reporte.pack(side="left",padx=4)
    gestionar_usuarios.pack(side="left",padx=4)

    return ventana


# if __name__ == "__main__":
#     root = tk.Tk()
#     root.withdraw()
#     abrir_dashboard()
#     root.mainloop()