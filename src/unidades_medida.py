from .conexion import get_cursor

def crear_unidad(nombre: str):
    with get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO unidades_medida (nombre) VALUES (%s) RETURNING id;",
            (nombre,)
        )
        return cur.fetchone()

def obtener_todas_las_unidades():
    with get_cursor() as cur:
        cur.execute("SELECT * FROM unidades_medida ORDER BY nombre;")
        return cur.fetchall()

def actualizar_unidad(id_unidad: int, nuevo_nombre: str):
    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE unidades_medida SET nombre = %s WHERE id = %s;",
            (nuevo_nombre, id_unidad)
        )
        return cur.rowcount > 0

def eliminar_unidad(id_unidad: int):
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM unidades_medida WHERE id = %s;", (id_unidad,))
        return cur.rowcount > 0
    
def obtener_factor_base(id_unidad: int):
    with get_cursor() as cur:
        cur.execute("SELECT factor_base FROM unidades_medida WHERE id = %s;", (id_unidad,))
        resultado = cur.fetchone()
        if resultado:
            return resultado['factor_base']
        return None