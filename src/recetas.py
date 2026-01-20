from .conexion import get_cursor
from typing import List, Dict

def crear_receta(id_producto_final: int, nombre: str, ingredientes: List[Dict]):
    with get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO recetas (id_producto_final, nombre) VALUES (%s, %s) RETURNING id_receta;",
            (id_producto_final, nombre)
        )
        id_receta = cur.fetchone()['id_receta']

        for ingrediente in ingredientes:
            cur.execute(
                """
                INSERT INTO detalle_receta (id_receta, id_insumo, cantidad_estimada, unidad)
                VALUES (%s, %s, %s, %s);
                """,
                (id_receta, ingrediente['id_insumo'], ingrediente['cantidad'], ingrediente['unidad_id'])
            )
        return {'id_receta': id_receta}

def obtener_receta_completa(id_receta: int):
    with get_cursor() as cur:
        # 1. Datos generales de la receta
        cur.execute("SELECT * FROM recetas WHERE id_receta = %s;", (id_receta,))
        receta = cur.fetchone()
        
        if not receta:
            return None
            
        # 2. Lista de ingredientes (AGREGAMOS dr.id_insumo)
        cur.execute(
            """
            SELECT 
                dr.id_insumo,   -- IMPORTANTE: Necesitamos el ID para el select
                p.nombre, 
                dr.cantidad_estimada, 
                um.nombre as unidad
            FROM detalle_receta dr
            JOIN productos p ON dr.id_insumo = p.id_producto
            JOIN unidades_medida um ON dr.unidad = um.id
            WHERE dr.id_receta = %s;
            """,
            (id_receta,)
        )
        receta['ingredientes'] = cur.fetchall()
        
        return receta

def eliminar_receta(id_receta: int):
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM recetas WHERE id_receta = %s;", (id_receta,))
        return cur.rowcount > 0
    
def obtener_receta_por_producto(id_producto_final: int):
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM recetas WHERE id_producto_final = %s ORDER BY fecha_creacion DESC LIMIT 1;", 
            (id_producto_final,)
        )
        receta = cur.fetchone()
        
        if not receta:
            return None 
            
        id_receta = receta['id_receta']
        cur.execute(
            """
            SELECT p.nombre as nombre_insumo, dr.id_insumo, dr.cantidad_estimada, um.nombre as unidad
            FROM detalle_receta dr
            JOIN productos p ON dr.id_insumo = p.id_producto
            JOIN unidades_medida um ON dr.unidad = um.id
            WHERE dr.id_receta = %s;
            """,
            (id_receta,)
        )
        receta['ingredientes'] = cur.fetchall()
        return receta

def actualizar_receta(id_receta: int, id_producto_final: int, nombre: str, ingredientes: list):
    with get_cursor(commit=True) as cur:
        cur.execute("""
            UPDATE recetas 
            SET nombre = %s, id_producto_final = %s
            WHERE id_receta = %s
        """, (nombre, id_producto_final, id_receta))

        cur.execute("DELETE FROM detalle_receta WHERE id_receta = %s", (id_receta,))
        if ingredientes:
            query_ingredientes = """
                INSERT INTO detalle_receta (id_receta, id_insumo, cantidad_estimada, unidad)
                VALUES (%s, %s, %s, %s)
            """
            datos_ingredientes = [
                (id_receta, ing['id_insumo'], ing['cantidad'], ing['unidad_id'])
                for ing in ingredientes
            ]
            cur.executemany(query_ingredientes, datos_ingredientes)
            
        return True

def obtener_todas_las_recetas_con_producto():
    with get_cursor() as cur:
        # Usamos COALESCE y STRING_AGG para evitar errores si hay nulos
        cur.execute(
            """
            SELECT 
                r.id_receta, 
                r.nombre, 
                r.id_producto_final, 
                p.nombre as nombre_producto,
                COALESCE(
                    STRING_AGG(
                        CONCAT(pi.nombre, ' (', CAST(dr.cantidad_estimada AS TEXT), ' ', um.nombre, ')'), 
                        ', '
                    ), 
                    'Sin ingredientes'
                ) as lista_ingredientes
            FROM recetas r
            LEFT JOIN productos p ON r.id_producto_final = p.id_producto
            LEFT JOIN detalle_receta dr ON r.id_receta = dr.id_receta
            LEFT JOIN productos pi ON dr.id_insumo = pi.id_producto
            LEFT JOIN unidades_medida um ON dr.unidad = um.id
            GROUP BY r.id_receta, r.nombre, p.nombre, p.id_producto
            ORDER BY r.nombre ASC;
            """
        )
        return cur.fetchall()