import pandas as pd 
from decimal import Decimal
from . import productos
from . import recetas
from . import produccion
from . import ventas
from . import movimientos_inventario
from . import unidades_medida

def registrar_venta_logica(id_producto: int, cantidad: float, precio_unitario: float, descuento: float = 0):

    try:
        cantidad_decimal = Decimal(str(cantidad))
        precio_decimal = Decimal(str(precio_unitario))
        descuento_decimal = Decimal(str(descuento))
        producto_info = productos.obtener_producto_por_id(id_producto)
        if not producto_info:
            raise Exception(f"Producto ID {id_producto} no encontrado.")
        if producto_info['es_producido']:
            print(f"ℹ️ Producto producido detectado (ID: {id_producto}). Registrando producción...")
            registrar_produccion_de_platillo(
                id_producto_final=id_producto,
                cantidad_producida=cantidad_decimal,
                unidad_id=producto_info['unidad'] 
            )
        else:
            print(f"ℹ️ Producto simple detectado (ID: {id_producto}). Actualizando stock...")
            if not productos.actualizar_stock(id_producto, -cantidad_decimal):
                raise Exception("No se pudo actualizar el stock del producto simple.")
        nueva_venta = ventas.registrar_venta(id_producto, cantidad_decimal, precio_decimal, descuento_decimal)
        if not nueva_venta:
            raise Exception("No se pudo registrar la venta en la tabla 'ventas'.")
        
        print(f"✅ Venta registrada con ID: {nueva_venta['id_venta']} y stock/insumos actualizados.")
        return True
        
    except Exception as e:
        print(f"❌ Error en registrar_venta_logica para ID {id_producto}: {e}")
        return False
def procesar_ventas_excel(ruta_archivo: str):
    """
    Lee un archivo Excel y procesa cada fila como una venta.
    """
    print(f"ℹ️ Iniciando carga de ventas desde: {ruta_archivo}")
    try:
        ruta_limpia = ruta_archivo.strip().strip('\'"')
        df = pd.read_excel(ruta_limpia)
        
        print(f"✅ Excel leído. {len(df)} filas encontradas. Procesando...")
        
        exitos = 0
        fallos = 0

        for index, row in df.iterrows():
            try:
                nombre_prod = row['Nombre Producto']
                familia_prod = row['Familia']
                cantidad = row['Cantidad']
                precio = row['Precio Unitario']
                descuento = row.get('Descuento', 0) 
                id_prod = productos.obtener_producto_por_nombre_y_familia(nombre_prod, familia_prod)
                
                if id_prod:
                    print(f"--- Fila {index+1}: Procesando '{nombre_prod}'...")
                    if registrar_venta_logica(id_prod, cantidad, precio, descuento):
                        exitos += 1
                    else:
                        fallos += 1
                else:
                    print(f"❌ ERROR Fila {index+1}: No se encontró producto con Nombre='{nombre_prod}' Y Familia='{familia_prod}'. Venta omitida.")
                    fallos += 1
            
            except Exception as e:
                print(f"❌ ERROR Fila {index+1}: No se pudo procesar. Detalle: {e}")
                fallos += 1
        
        print("\n--- 📊 Resumen de Carga ---")
        print(f"✅ Ventas procesadas con éxito: {exitos}")
        print(f"❌ Ventas con errores (omitidas): {fallos}")
        print("---------------------------")

    except FileNotFoundError:
        print(f"❌ ERROR: No se encontró el archivo en la ruta: {ruta_limpia}")
    except Exception as e:
        print(f"❌ ERROR crítico al leer el archivo Excel: {e}")


def registrar_compra_logica(id_producto: int, cantidad: float, unidad_id: int):
    try:
        factor = unidades_medida.obtener_factor_base(unidad_id)
        if factor is None:
            raise Exception(f"Unidad ID {unidad_id} no encontrada.")
        cantidad_decimal = Decimal(str(cantidad))
        factor_decimal = Decimal(factor) # El factor ya es Decimal
        cantidad_base = cantidad_decimal * factor_decimal
        if not productos.actualizar_stock(id_producto, cantidad_base):
            raise Exception("No se pudo actualizar el stock.")
        
        print(f"✅ Stock actualizado para el producto {id_producto}. Sumado: {cantidad_base} unidades base")
        return True
        
    except Exception as e:
        print(f"❌ Error en registrar_compra_logica: {e}")
        return False

def registrar_merma_logica(id_producto: int, cantidad: float, unidad_id: int, observaciones: str):
    try:
        factor = unidades_medida.obtener_factor_base(unidad_id)
        if factor is None:
            raise Exception(f"Unidad ID {unidad_id} no encontrada.")
        cantidad_decimal = Decimal(str(cantidad))
        factor_decimal = Decimal(factor)
        cantidad_base = cantidad_decimal * factor_decimal
        nuevo_mov = movimientos_inventario.registrar_movimiento(
            id_producto, 'Merma', cantidad_decimal, unidad_id, observaciones
        )
        if not nuevo_mov:
            raise Exception("No se pudo registrar el movimiento de merma.")
            
        print(f"✅ Movimiento de merma registrado ID: {nuevo_mov['id_movimiento']}")
        if not productos.actualizar_stock(id_producto, -cantidad_base): # <--- ¡EL CAMBIO CLAVE!
            raise Exception("No se pudo actualizar el stock por la merma.")
            
        print(f"✅ Stock del producto actualizado. (Descontado: {cantidad_base} unidades base)")
        return True

    except Exception as e:
        print(f"❌ Error en registrar_merma_logica: {e}")
        return False

def registrar_produccion_de_platillo(id_producto_final: int, cantidad_producida: float, unidad_id: int):
    receta_data = recetas.obtener_receta_por_producto(id_producto_final)
    if not receta_data:
        print(f"❌ Error: No se encontró receta para el producto ID {id_producto_final}.")
        return False
    
    try:
        cantidad_producida_decimal = Decimal(str(cantidad_producida))
        print(f"ℹ️ Iniciando producción de {cantidad_producida_decimal} x {receta_data['nombre']}...")
        
        for ingrediente in receta_data['ingredientes']:
            id_insumo = ingrediente['id_insumo']
            cantidad_necesaria = ingrediente['cantidad_estimada'] 
            cantidad_a_descontar = cantidad_necesaria * cantidad_producida_decimal
            
            print(f"--- Descontando {cantidad_a_descontar} de {ingrediente['nombre_insumo']}...")
            if not productos.actualizar_stock(id_insumo, -cantidad_a_descontar):
                raise Exception(f"No se pudo actualizar el stock para el insumo: {ingrediente['nombre_insumo']}")
        
        print(f"+++ Aumentando stock de {receta_data['nombre']} en {cantidad_producida_decimal}...")
        if not productos.actualizar_stock(id_producto_final, cantidad_producida_decimal):
             raise Exception("No se pudo actualizar el stock del producto final.")
        
        produccion.registrar_produccion(id_producto_final, cantidad_producida_decimal, unidad_id)
        
        print("✅ Producción registrada y stock actualizado con éxito.")
        return True

    except Exception as e:
        print(f"❌ Error crítico en registrar_produccion_de_platillo: {e}")
        print("ℹ️ Es posible que el inventario esté en un estado inconsistente. Se requiere revisión manual.")
        return False

def registrar_produccion_simple(id_producto: int, cantidad: float, unidad_id: int, observaciones: str = "Producción interna"):
    try:
        factor = unidades_medida.obtener_factor_base(unidad_id)
        if factor is None:
            raise Exception(f"Unidad ID {unidad_id} no encontrada.")
        cantidad_decimal = Decimal(str(cantidad))
        factor_decimal = Decimal(factor)
        cantidad_base = cantidad_decimal * factor_decimal 
        if not productos.actualizar_stock(id_producto, cantidad_base):
            raise Exception("No se pudo actualizar el stock del producto.")
        produccion.registrar_produccion(id_producto, cantidad_decimal, unidad_id, observaciones)
        print(f"✅ Producción simple registrada. Stock de [ID: {id_producto}] aumentado en {cantidad_base} unidades base (equivale a {cantidad_decimal} L).")
        return True
        
    except Exception as e:
        print(f"❌ Error en registrar_produccion_simple: {e}")
        return False