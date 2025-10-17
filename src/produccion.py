from .conexion import get_cursor
from datetime import date

def registrar_produccion(id_producto: int, cantidad: float, unidad_id: int, observaciones: str = None):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO produccion (id_producto, cantidad, unidad, observaciones)
            VALUES (%s, %s, %s, %s)
            RETURNING id_produccion;
            """,
            (id_producto, cantidad, unidad_id, observaciones)
        )
        return cur.fetchone()

def obtener_produccion_por_rango_fecha(fecha_inicio: date, fecha_fin: date):
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM produccion WHERE fecha BETWEEN %s AND %s ORDER BY fecha DESC;",
            (fecha_inicio, fecha_fin)
        )
        return cur.fetchall()