# src/familias.py
from .conexion import get_cursor

def crear_familia(nombre: str, descripcion: str = None):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO familias (nombre, descripcion)
            VALUES (%s, %s)
            RETURNING id_familia;
            """,
            (nombre, descripcion)
        )
        return cur.fetchone()

def obtener_todas_las_familias():
    with get_cursor() as cur:
        cur.execute("SELECT * FROM familias ORDER BY nombre;")
        return cur.fetchall()

def actualizar_familia(id_familia: int, nombre: str, descripcion: str):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            UPDATE familias
            SET nombre = %s, descripcion = %s
            WHERE id_familia = %s;
            """,
            (nombre, descripcion, id_familia)
        )
        return cur.rowcount > 0

def eliminar_familia(id_familia: int):
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM familias WHERE id_familia = %s;", (id_familia,))
        return cur.rowcount > 0