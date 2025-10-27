from .conexion import get_cursor

def crear_producto(nombre: str, unidad_id: int, id_familia: int,  stock_inicial: float = 0, codigo_softrestaurante: int = None, es_producido: bool = False, es_vendido: bool = True, activo: bool = True):
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO productos (nombre, unidad, stock, codigo_softrestaurant, es_producido, es_vendido, activo, id_familia
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_producto;
            """,
            (nombre, unidad_id, stock_inicial, codigo_softrestaurante, es_producido, es_vendido, activo, id_familia)
        )
        id_creado = cur.fetchone()
        return id_creado

def obtener_producto_por_id(id_producto: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM productos WHERE id_producto = %s;", (id_producto,))
        return cur.fetchone()

def obtener_todos_los_productos(solo_activos: bool = True):
    with get_cursor() as cur:
        sql_query = "SELECT * FROM productos"
        if solo_activos:
            sql_query += " WHERE activo = TRUE"
        sql_query += " ORDER BY nombre;"
        
        cur.execute(sql_query)
        return cur.fetchall()

def actualizar_stock(id_producto: int, cantidad_a_sumar: float):
    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE productos SET stock = stock + %s WHERE id_producto = %s;",
            (cantidad_a_sumar, id_producto)
        )
        return cur.rowcount > 0

def desactivar_producto(id_producto: int):
    with get_cursor(commit=True) as cur:
        cur.execute("UPDATE productos SET activo = FALSE WHERE id_producto = %s;", (id_producto,))
        return cur.rowcount > 0

def obtener_producto_por_nombre_y_familia(nombre_producto: str, nombre_familia: str):
    """
    Busca un ID de producto usando su nombre y el nombre de su familia.
    Esto es clave para conectar el Excel con la base de datos.
    """
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT p.id_producto
            FROM productos p
            JOIN familias f ON p.id_familia = f.id_familia
            WHERE p.nombre = %s AND f.nombre = %s
            AND p.activo = TRUE;
            """,
            (nombre_producto, nombre_familia)
        )
        producto = cur.fetchone()
        
        if producto:
            return producto['id_producto']
        return None