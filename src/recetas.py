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
        cur.execute("SELECT * FROM recetas WHERE id_receta = %s;", (id_receta,))
        receta = cur.fetchone()
        if not receta:
            return None
            
        cur.execute(
            """
            SELECT p.nombre, dr.cantidad_estimada, um.nombre as unidad
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
    