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
    
def procesar_ventas_excel(ruta_archivo: str, fila_inicio: int = 1, fecha_venta_str: str = None):
    fecha_final = fecha_venta_str if fecha_venta_str else date.today()

    print(f"ℹ️ Iniciando carga de ventas API desde: {ruta_archivo} (Fecha: {fecha_venta_str})")
    
    try:
        # 1. LEER EXCEL
        # Forzamos header=4 como en tu código original
        df = pd.read_excel(ruta_archivo, header=4, converters={'CLAVE': str})
        df = df.dropna(subset=['CLAVE']) # Ignorar filas sin clave
        
        # --- FASE 1: VALIDACIÓN DE PRODUCTOS (MODO ESCÁNER) ---
        # Recorremos todo el Excel SIN guardar nada en la BD para ver si falta algo.
        
        mapa_cache_productos = {} # Guardamos los IDs aquí para no consultar la BD dos veces
        
        # Iteramos sobre el DataFrame original completo
        for index, row in df.iterrows():
            fila_log = df.index.get_loc(index) + 1 # Fila real del Excel (aprox)
            
            # Limpieza de clave idéntica a tu lógica original
            clave_raw = str(row['CLAVE'])
            if clave_raw.lower() == 'nan' or clave_raw == '':
                continue
            clave_sr = clave_raw.strip().lstrip('0') # Agregamos .strip() por seguridad
            nombre_prod_log = str(row['DESCRIPCION']).strip()
            
            # Si ya validamos este producto en una fila anterior, saltamos
            if clave_sr in mapa_cache_productos:
                continue

            # Buscamos en BD
            id_prod = productos.obtener_producto_por_codigo_sr(clave_sr)
            
            if not id_prod:
                # ¡ERROR ENCONTRADO!
                # Como no hemos guardado nada, devolvemos el error limpio.
                print(f"❌ ERROR Fila {fila_log}: No se encontró producto con CLAVE='{clave_sr}'")
                return {
                    "exito": False,
                    "error": "Producto no encontrado",
                    "filas_procesadas_exitosamente": 0, # Cero porque no guardamos nada aún
                    "fila_excel": fila_log, 
                    "clave_faltante": clave_sr,
                    "nombre_producto": nombre_prod_log,
                    "familia_grupo": row.get('GRUPO', 'N/A')
                }
            
            # Si existe, lo guardamos en caché para usarlo en la FASE 2
            mapa_cache_productos[clave_sr] = id_prod

        # --- FASE 2: VALIDACIÓN DE FECHA ---
        # Solo verificamos la fecha si sabemos que TODOS los productos existen.
        if ventas.verificar_existencia_ventas_fecha(fecha_final):
            return {
                "exito": False, 
                "error": f"Verifica la fecha: Ya existen ventas registradas para el día {fecha_final}. Si hubo un error previo, borra las ventas parciales en el historial."
            }

        # --- FASE 3: GUARDADO TRANSACCIONAL ---
        # Si llegamos aquí, el Excel es perfecto y la fecha está libre. Guardamos todo.
        
        exitos = 0
        fallos = 0
        
        for index, row in df.iterrows():
            fila_log = df.index.get_loc(index) + 1
            
            try:
                # Recuperamos datos limpios
                clave_sr = str(row['CLAVE']).split('.')[0].strip()
                nombre_prod_log = str(row['DESCRIPCION']).strip()
                cantidad = row['CANTIDAD']
                precio = row['PRECIO']
                descuento = row.get('Descuento', 0)
                
                # Obtenemos el ID directo de la memoria (ya sabemos que existe)
                id_prod = mapa_cache_productos[clave_sr]
                
                print(f"--- Fila {fila_log}: Procesando '{nombre_prod_log}'...")
                
                # Llamamos a tu función de registro
                if registrar_venta_logica(id_prod, cantidad, precio, descuento, fecha_venta_str):
                    exitos += 1
                else:
                    print(f"⚠️ Alerta: registrar_venta_logica devolvió False en fila {fila_log}")
                    fallos += 1
                    
            except Exception as e:
                print(f"❌ ERROR Fila {fila_log}: {e}")
                fallos += 1
        
        # FIN DEL PROCESO
        if fallos > 0:
             return {
                "exito": True, # Ponemos True parcial para que no bloquee, o False si prefieres ser estricto
                "mensaje": f"Proceso terminado. Éxitos: {exitos}, Errores de lógica: {fallos}",
                "filas_procesadas_exitosamente": exitos,
                "filas_omitidas_por_error_interno": fallos
            }

        return {
            "exito": True,
            "mensaje": "Archivo procesado completamente",
            "filas_procesadas_exitosamente": exitos,
            "filas_omitidas_por_error_interno": 0
        }

    except Exception as e:
        return {"exito": False, "error": f"ERROR crítico al leer Excel: {str(e)}"}

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