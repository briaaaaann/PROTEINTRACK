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
            print(f"ℹ️ Producto producido detectado (ID: {id_producto}). Verificando receta...")
            
            exito_receta = registrar_produccion_de_platillo(
                id_producto_final=id_producto,
                cantidad_producida=cantidad_decimal,
                unidad_id=producto_info['unidad'] 
            )
            if not exito_receta:
                print(f"⚠️ No se encontró receta para ID {id_producto}. Se descontará stock del producto principal.")
                if not productos.actualizar_stock(id_producto, -cantidad_decimal):
                    raise Exception(f"No se encontró receta Y TAMPOCO se pudo actualizar el stock del producto {id_producto}.")

        else:
            print(f"ℹ️ Producto simple detectado (ID: {id_producto}). Actualizando stock...")
            if not productos.actualizar_stock(id_producto, -cantidad_decimal):
                raise Exception(f"No se pudo actualizar el stock del producto simple {id_producto}.")

        nueva_venta = ventas.registrar_venta(id_producto, cantidad_decimal, precio_decimal, descuento_decimal)
        if not nueva_venta:
            raise Exception("No se pudo registrar la venta en la tabla 'ventas'.")
        
        print(f"✅ Venta registrada con ID: {nueva_venta['id_venta']} y stock/insumos actualizados.")
        return True
        
    except Exception as e:
        print(f"❌ Error en registrar_venta_logica: {e}")
        return False
    
def procesar_ventas_excel(ruta_archivo: str, ui_crear_producto_callback): 
    print(f"ℹ️ Iniciando carga de ventas desde: {ruta_archivo}")
    try:
        ruta_limpia = ruta_archivo.strip().strip('\'"')
        df = pd.read_excel(ruta_limpia, header=4, dtype={'CLAVE': str}) 
        df = df.dropna(subset=['CLAVE'])
        
        print(f"✅ Excel leído. {len(df)} filas válidas encontradas. Procesando...")
        
        exitos = 0
        fallos = 0
        for index, row in df.iterrows():
            try:
                clave_sr = str(row['CLAVE']).split('.')[0]
                
                nombre_prod_log = row['DESCRIPCION'] 
                cantidad = row['CANTIDAD']
                precio = row['PRECIO']
                descuento = row.get('Descuento', 0) 

                id_prod = productos.obtener_producto_por_codigo_sr(clave_sr)
                
                if id_prod: 
                    print(f"--- Fila {index+1}: Procesando '{nombre_prod_log}' (CLAVE: {clave_sr}, ID: {id_prod})...")
                    if registrar_venta_logica(id_prod, cantidad, precio, descuento):
                        exitos += 1
                    else:
                        fallos += 1 
                
                else:
                    print(f"❌ ERROR Fila {index+1}: No se encontró producto con CLAVE='{clave_sr}' ('{nombre_prod_log}').")
                    print(f"⚠️  Se requiere intervención manual para registrar este producto.")
                    nuevo_id = ui_crear_producto_callback(clave_sr, nombre_prod_log, row)
                    
                    if nuevo_id:
                        print(f"✅ Producto '{nombre_prod_log}' (ID: {nuevo_id}) creado.")
                        print(f"--- Fila {index+1}: RE-Procesando '{nombre_prod_log}' (CLAVE: {clave_sr}, ID: {nuevo_id})...")
                        if registrar_venta_logica(nuevo_id, cantidad, precio, descuento):
                            exitos += 1
                        else:
                            fallos += 1
                    else:
                        print(f"🚫 Creación cancelada. Venta de '{nombre_prod_log}' OMITIDA.")
                        fallos += 1
            
            except KeyError as e:
                print(f"❌ ERROR Fila {index+1}: Falta la columna {e} en el Excel. Venta omitida.")
                fallos += 1
            except Exception as e:
                print(f"❌ ERROR Fila {index+1} ('{row.get('DESCRIPCION', 'N/A')}'): No se pudo procesar. Detalle: {e}")
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
        factor_decimal = Decimal(factor) 
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
        if not productos.actualizar_stock(id_producto, -cantidad_base): 
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
    cantidad_producida_decimal = Decimal(str(cantidad_producida))
    
    print(f"ℹ️ Iniciando consumo de insumos para {cantidad_producida_decimal} x {receta_data['nombre']}...")
    try:
        for ingrediente in receta_data['ingredientes']:
            id_insumo = ingrediente['id_insumo']
            cantidad_necesaria = ingrediente['cantidad_estimada'] 
            cantidad_a_descontar = cantidad_necesaria * cantidad_producida_decimal
            
            print(f"--- Descontando {cantidad_a_descontar} de {ingrediente['nombre_insumo']}...")
            if not productos.actualizar_stock(id_insumo, -cantidad_a_descontar):
                raise Exception(f"No se pudo actualizar el stock para el insumo: {ingrediente['nombre_insumo']}")
        produccion.registrar_produccion(
            id_producto_final, 
            cantidad_producida_decimal, 
            unidad_id, 
            "Venta-Consumo" 
        )
        
        print("✅ Insumos de receta descontados con éxito.")
        return True

    except Exception as e:
        print(f"❌ Error crítico en registrar_produccion_de_platillo: {e}")
        print("ℹ️ Es posible que el inventario esté en un estado inconsistente. Se requiere revisión manual.")
        return False

def registrar_produccion_simple(id_producto: int, cantidad: float, unidad_id: int, unidad_nombre: str = 'unidades', observaciones: str = "Producción interna"):
    try:
        factor = unidades_medida.obtener_factor_base(unidad_id)
        if factor is None:
            raise Exception(f"Unidad ID {unidad_id} no encontrada.")
        cantidad_decimal = Decimal(str(cantidad))
        factor_decimal = Decimal(factor)
        cantidad_base = cantidad_decimal * factor_decimal 
        receta_data = recetas.obtener_receta_por_producto(id_producto)
        if receta_data:
            print("ℹ️ Receta encontrada. Descontando insumos...")
            for ingrediente in receta_data['ingredientes']:
                id_insumo = ingrediente['id_insumo']
                cantidad_necesaria = ingrediente['cantidad_estimada'] 
                cantidad_a_descontar = cantidad_necesaria * cantidad_decimal
                print(f"--- Descontando {cantidad_a_descontar} de {ingrediente['nombre_insumo']}...")
                if not productos.actualizar_stock(id_insumo, -cantidad_a_descontar):
                    raise Exception(f"No se pudo actualizar el stock para el insumo: {ingrediente['nombre_insumo']}")
        else:
            print("ℹ️ No se encontró receta para este producto. Solo se sumará al stock.")
        if not productos.actualizar_stock(id_producto, cantidad_base):
            raise Exception("No se pudo actualizar el stock del producto final.")
        produccion.registrar_produccion(id_producto, cantidad_decimal, unidad_id, observaciones)
        print(f"✅ Producción simple registrada. Stock de [ID: {id_producto}] aumentado en {cantidad_base} unidades base (equivale a {cantidad_decimal} {unidad_nombre}).")
        return True
        
    except Exception as e:
        print(f"❌ Error en registrar_produccion_simple: {e}")
        return False