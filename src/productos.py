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
        sql_query = """
            SELECT 
                p.id_producto, 
                p.nombre, 
                p.stock AS stock_base,  -- Stock en Gramos/Mililitros
                um.nombre AS unidad_nombre,
                um.factor_base,
                -- Calculamos el stock en la unidad legible (Litros/Kilos)
                (p.stock / um.factor_base) AS stock_convertido
            FROM productos p
            JOIN unidades_medida um ON p.unidad = um.id
        """
        if solo_activos:
            sql_query += " WHERE p.activo = TRUE"
        sql_query += " ORDER BY p.nombre;"
        
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

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT p.id_producto
            FROM productos p
            JOIN familias f ON p.id_familia = f.id_familia
            WHERE 
                -- Clave: 1. UPPER, 2. REPLACE, 3. unaccent
                unaccent(REPLACE(UPPER(p.nombre), 'Ñ', 'N')) = unaccent(REPLACE(UPPER(%s), 'Ñ', 'N'))
                AND 
                unaccent(REPLACE(UPPER(f.nombre), 'Ñ', 'N')) = unaccent(REPLACE(UPPER(%s), 'Ñ', 'N'))
            AND p.activo = TRUE;
            """,
            (nombre_producto, nombre_familia)
        )
        producto = cur.fetchone()
        
        if producto:
            return producto['id_producto']
        return None
    
def obtener_producto_por_codigo_sr(codigo_sr: str):
    """
    Busca un ID de producto usando su 'codigo_softrestaurant'.
    (Versión corregida que ignora filas con códigos no numéricos en la BD)
    """
    with get_cursor() as cur:
        try:
            # El 'codigo_sr' viene de logica_negocio.py como un string limpio (ej. '7036')
            
            cur.execute(
                """
                SELECT id_producto
                FROM productos 
                WHERE 
                    -- --- INICIO DE LA CORRECCIÓN ---
                    -- 1. Revisa que el código en la BD contenga SÓLO números.
                    -- Esto ignora automáticamente valores '' o NULL o 'ABC'
                    codigo_softrestaurant ~ '^[0-9]+$'
                    
                    -- 2. SOLO SI ES NUMÉRICO, intenta convertirlo y compararlo.
                    AND CAST(codigo_softrestaurant AS INTEGER) = CAST(%s AS INTEGER)
                    -- --- FIN DE LA CORRECCIÓN ---
                AND activo = TRUE;
                """,
                (codigo_sr,) 
            )
            
            producto = cur.fetchone()
            
            if producto:
                return producto['id_producto']
            return None
        
        except Exception as e:
            # Si algo aun así falla, lo reportará.
            print(f"⚠️ ADVERTENCIA: Error al buscar código {codigo_sr}. Detalle: {e}")
            return None