# test_connection.py
from src.conexion import get_cursor

def main():
    with get_cursor() as cur:
        cur.execute("SELECT current_database() AS db;")
        print("Conectado a:", cur.fetchone()["db"])
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;")
        tables = cur.fetchall()
        if tables:
            print("Tablas en public:")
            for t in tables:
                print("-", t["table_name"])
        else:
            print("No hay tablas en el esquema public (aún).")

if __name__ == "__main__":
    main()
