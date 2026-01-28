import pandas as pd 
from decimal import Decimal
from datetime import date
from . import productos
from . import recetas
from . import produccion
from . import ventas  
from . import movimientos_inventario
from . import unidades_medida

def registrar_venta_logica(id_producto: int, cantidad: float, precio_unitario: float, descuento: float = 0, fecha_personalizada=None):
    fecha_final = fecha_personalizada if fecha_personalizada else date.today()
    
    try:
        cantidad_decimal = Decimal(str(cantidad))
        precio_decimal = Decimal(str(precio_unitario))
        descuento_decimal = Decimal(str(descuento))
        producto_info = productos.obtener_producto_por_id(id_producto)
        if not producto_info:
            raise Exception(f"Producto ID {id_producto} no encontrado.")
        id_nueva_venta = ventas.registrar_venta(
            id_producto, 
            cantidad_decimal, 
            precio_decimal, 
            descuento_decimal,
            fecha_final 
        )
        
        if not id_nueva_venta:
            raise Exception("No se pudo registrar la venta en la tabla 'ventas'.")

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
        
        print(f"✅ Venta registrada con ID: {id_nueva_venta} (Fecha: {fecha_final}) y stock actualizado.")
        return True
        
    except Exception as e:
        print(f"❌ Error en registrar_venta_logica: {e}")
        return False
    
# Asegúrate de importar esto arriba
import pandas as pd
from datetime import date
from . import ventas
from . import productos
from . import produccion 

def procesar_ventas_excel(ruta_archivo: str, fila_inicio: int = 1, fecha_venta_str: str = None):
    fecha_final = fecha_venta_str if fecha_venta_str else date.today()
    print(f"ℹ️ Iniciando carga desde: {ruta_archivo}")
    
    try:
        # 1. LEER EXCEL (Converters es vital para mantener los '0' iniciales como texto)
        df = pd.read_excel(ruta_archivo, header=4, converters={'CLAVE': str}) 
        df = df.dropna(subset=['CLAVE'])
        
        # --- FASE 1: VALIDACIÓN (Escaneo sin guardar) ---
        mapa_cache = {} 
        
        for index, row in df.iterrows():
            fila_log = df.index.get_loc(index) + 1 
            
            # Limpieza idéntica a la fase de guardado
            clave_raw = str(row['CLAVE'])
            if clave_raw.lower() == 'nan' or clave_raw.strip() == '':
                continue
            
            # MAGIA DE LOS CEROS: Quita espacios y ceros a la izquierda (0123 -> 123)
            clave_sr = clave_raw.strip().lstrip('0')
            if not clave_sr: clave_sr = "0"

            if clave_sr in mapa_cache: continue

            # Buscamos en BD
            id_prod = productos.obtener_producto_por_codigo_sr(clave_sr)
            
            # SI NO EXISTE: DETENER Y AVISAR AL FRONTEND
            if not id_prod:
                print(f"❌ ALERTA: Producto faltante fila {fila_log}: '{clave_sr}'")
                return {
                    "exito": False,
                    "error": f"Producto nuevo detectado: {clave_sr}", 
                    "producto_faltante": clave_sr,  # JS usa esto para abrir el modal
                    "descripcion_sugerida": str(row['DESCRIPCION']).strip(),
                    "fila": fila_log,
                    "filas_procesadas_exitosamente": 0
                }
            
            mapa_cache[clave_sr] = id_prod

        # --- FASE 2: VERIFICAR FECHA ---
        if fila_inicio == 1 and ventas.verificar_existencia_ventas_fecha(fecha_final):
            return {
                "exito": False, 
                "error": f"Ya existen ventas registradas para el día {fecha_final}. Elimínalas antes de recargar."
            }
        # --- FASE 3: GUARDADO ---
        exitos = 0
        fallos = 0
        
        for index, row in df.iterrows():
            try:
                clave_sr = str(row['CLAVE']).strip().lstrip('0')
                if not clave_sr: clave_sr = "0"
                if clave_sr not in mapa_cache: continue # Seguridad extra

                id_prod = mapa_cache[clave_sr]
                cantidad = row['CANTIDAD']
                precio = row['PRECIO']
                descuento = row.get('Descuento', 0)
                
                if registrar_venta_logica(id_prod, cantidad, precio, descuento, fecha_venta_str):
                    exitos += 1
                else:
                    fallos += 1
            except Exception as e:
                print(f"⚠️ Error fila {index}: {e}")
                fallos += 1
        
        return {
            "exito": True, 
            "mensaje": f"Proceso terminado. {exitos} ventas guardadas.",
            "total_registros": exitos
        }

    except Exception as e:
        return {"exito": False, "error": f"Error leyendo Excel: {str(e)}"}

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

def registrar_merma_logica(id_producto: int, cantidad: float, unidad_id: int, observaciones: str, fecha_personalizada=None):
    try:
        factor = unidades_medida.obtener_factor_base(unidad_id)
        if factor is None:
            raise Exception(f"Unidad ID {unidad_id} no encontrada.")
        cantidad_decimal = Decimal(str(cantidad))
        factor_decimal = Decimal(factor)
        cantidad_base = cantidad_decimal * factor_decimal
        nuevo_mov = movimientos_inventario.registrar_movimiento(
            id_producto, 'Merma', cantidad_decimal, unidad_id, observaciones, fecha=fecha_personalizada
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

def registrar_produccion_simple(id_producto: int, cantidad: float, unidad_id: int, unidad_nombre: str = 'unidades', observaciones: str = "Producción interna", fecha_personalizada=None):
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
        produccion.registrar_produccion(id_producto, cantidad_decimal, unidad_id, observaciones, fecha=fecha_personalizada)
        print(f"✅ Producción simple registrada. Stock de [ID: {id_producto}] aumentado en {cantidad_base} unidades base (equivale a {cantidad_decimal} {unidad_nombre}).")
        return True
        
    except Exception as e:
        print(f"❌ Error en registrar_produccion_simple: {e}")
        return False