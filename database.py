import mssql_python

SERVER = r"DESKTOP-C8QLULS"
DATABASE = "AdministracionTerrenos"

def conectar_bd():
    cadena_conexion = (
        f"Server={SERVER};"
        f"Database={DATABASE};"
        "Trusted_Connection=yes;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    return mssql_python.connect(cadena_conexion)