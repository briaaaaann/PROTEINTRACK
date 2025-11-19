from .conexion import get_cursor
from datetime import date

def generar_snapshot_diario():
    fecha_hoy = date.today()
    print(f"📸 Generando snapshot de inventario para el día: {fecha_hoy}")
    
    with get_cursor(commit=True) as cur:
        cur.execute("""
            SELECT id_producto, stock 
            FROM productos 
            WHERE es_registrable_produccion = TRUE AND activo = TRUE;
        """)
        productos_a_guardar = cur.fetchall()
        
        registrados = 0
        actualizados = 0
        
        for prod in productos_a_guardar:
            cur.execute("""
                INSERT INTO stock_diario (id_producto, fecha, stock_registrado)
                VALUES (%s, %s, %s)
                ON CONFLICT (id_producto, fecha) 
                DO UPDATE SET stock_registrado = EXCLUDED.stock_registrado;
            """, (prod['id_producto'], fecha_hoy, prod['stock']))
            registrados += 1

    print(f"✅ Snapshot completado. {registrados} productos registrados.")
    return {"fecha": str(fecha_hoy), "productos_procesados": registrados}

def obtener_historial_por_fecha(fecha_consulta: str):
    with get_cursor() as cur:
        cur.execute("""
            SELECT 
                p.nombre, 
                s.stock_registrado, 
                um.nombre as unidad_nombre,
                -- Cálculo opcional convertido a unidad base si hiciera falta
                CASE 
                    WHEN um.factor_base > 0 THEN s.stock_registrado / um.factor_base
                    ELSE 0 
                END AS stock_convertido
            FROM stock_diario s
            JOIN productos p ON s.id_producto = p.id_producto
            JOIN unidades_medida um ON p.unidad = um.id
            WHERE s.fecha = %s
            ORDER BY p.nombre;
        """, (fecha_consulta,))
        
        return cur.fetchall()