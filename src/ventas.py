from .conexion import get_cursor
from datetime import date

def registrar_venta(id_producto: int, cantidad: float, precio_unitario: float, descuento: float = 0):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO ventas (id_producto, cantidad, precio_unitario, descuento)
            VALUES (%s, %s, %s, %s)
            RETURNING id_venta;
            """,
            (id_producto, cantidad, precio_unitario, descuento)
        )
        return cur.fetchone()

def obtener_venta_por_id(id_venta: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM ventas WHERE id_venta = %s;", (id_venta,))
        return cur.fetchone()

def obtener_ventas_por_fecha(fecha_inicio: date, fecha_fin: date):
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM ventas WHERE fecha BETWEEN %s AND %s ORDER BY fecha DESC;",
            (fecha_inicio, fecha_fin)
        )
        return cur.fetchall()