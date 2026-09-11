"""
Test file to verify the SQL Server connection using mssql_python.
"""

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


def test_conexion():
    print("=" * 60)
    print("Testing SQL Server connection...")
    print(f"Server:   {SERVER}")
    print(f"Database: {DATABASE}")
    print("=" * 60)

    try:
        conn = conectar_bd()
        print("[OK] Connection established successfully.")

        cursor = conn.cursor()

        # Verify server/database info
        cursor.execute("SELECT @@SERVERNAME, DB_NAME(), SUSER_NAME()")
        row = cursor.fetchone()
        print(f"[OK] Connected to server:   {row[0]}")
        print(f"[OK] Current database:      {row[1]}")
        print(f"[OK] Logged in as user:     {row[2]}")

        # Verify SQL Server version
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"[OK] SQL Server version:    {version.splitlines()[0]}")

        # List tables in the database
        cursor.execute(
            "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            "WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_SCHEMA, TABLE_NAME"
        )
        tables = cursor.fetchall()
        print(f"\n[OK] Found {len(tables)} table(s) in '{DATABASE}':")
        for schema, table in tables:
            print(f"     - {schema}.{table}")

        cursor.close()
        conn.close()
        print("\n[OK] Connection closed cleanly.")
        print("=" * 60)
        print("TEST PASSED")
        print("=" * 60)
        return True

    except mssql_python.Error as e:
        print(f"\n[FAIL] Database error: {e}")
        print("=" * 60)
        print("TEST FAILED")
        print("=" * 60)
        return False
    except Exception as e:
        print(f"\n[FAIL] Unexpected error: {type(e).__name__}: {e}")
        print("=" * 60)
        print("TEST FAILED")
        print("=" * 60)
        return False


if __name__ == "__main__":
    test_conexion()