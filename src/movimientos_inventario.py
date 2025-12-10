from .conexion import get_cursor
from datetime import date

def registrar_movimiento(id_producto: int, tipo_salida: str, cantidad: float, unidad_id: int, observaciones: str = None, fecha: date = None):
    fecha_final = fecha if fecha else date.today()
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO movimientos_inventario (id_producto, tipo_salida, cantidad, unidad, observaciones, fecha)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id_movimiento;
            """,
            (id_producto, tipo_salida, cantidad, unidad_id, observaciones, fecha_final)
        )
        return cur.fetchone()

def obtener_movimientos_por_producto(id_producto: int):
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM movimientos_inventario WHERE id_producto = %s ORDER BY fecha DESC;",
            (id_producto,)
        )
        return cur.fetchall()