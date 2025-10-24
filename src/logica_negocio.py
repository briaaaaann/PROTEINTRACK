from . import productos
from . import recetas
from . import produccion
from . import ventas
from . import movimientos_inventario

def registrar_venta_logica(id_producto: int, cantidad: float, precio_unitario: float, descuento: float = 0):

    try:
        # 1. Registrar venta
        nueva_venta = ventas.registrar_venta(id_producto, cantidad, precio_unitario, descuento)
        if not nueva_venta:
            raise Exception("No se pudo registrar la venta.")
        
        print(f"✅ Venta registrada con ID: {nueva_venta['id_venta']}")

        # 2. Descontar stock 
        if not productos.actualizar_stock(id_producto, -cantidad):
            raise Exception("No se pudo actualizar el stock.")
            
        print("✅ Stock del producto actualizado.")
        return True
        
    except Exception as e:
        print(f"❌ Error en registrar_venta_logica: {e}")
        return False

def registrar_compra_logica(id_producto: int, cantidad: float):

    try:
        if not productos.actualizar_stock(id_producto, cantidad):
            raise Exception("No se pudo actualizar el stock.")
        
        print(f"✅ Stock actualizado para el producto {id_producto}. Nuevo total sumado: {cantidad}")
        return True
        
    except Exception as e:
        print(f"❌ Error en registrar_compra_logica: {e}")
        return False

def registrar_merma_logica(id_producto: int, cantidad: float, unidad_id: int, observaciones: str):

    try:
        # 1. Registrar movimiento de merma
        nuevo_mov = movimientos_inventario.registrar_movimiento(
            id_producto, 'Merma', cantidad, unidad_id, observaciones
        )
        if not nuevo_mov:
            raise Exception("No se pudo registrar el movimiento de merma.")
            
        print(f"✅ Movimiento de merma registrado ID: {nuevo_mov['id_movimiento']}")
        
        # 2. Descontar stock
        if not productos.actualizar_stock(id_producto, -cantidad):
            raise Exception("No se pudo actualizar el stock por la merma.")
            
        print("✅ Stock del producto actualizado.")
        return True

    except Exception as e:
        print(f"❌ Error en registrar_merma_logica: {e}")
        return False

def registrar_produccion_de_platillo(id_producto_final: int, cantidad_producida: float, unidad_id: int):

    
    # 1. Obtener receta producto
    receta_data = recetas.obtener_receta_por_producto(id_producto_final)
    
    if not receta_data:
        print(f"❌ Error: No se encontró receta para el producto ID {id_producto_final}.")
        return False
    
    print(f"ℹ️ Iniciando producción de {cantidad_producida} x {receta_data['nombre']}...")
    
    # 2. Descontar ingrediente/insumo de stock
    try:
        for ingrediente in receta_data['ingredientes']:
            id_insumo = ingrediente['id_insumo']
            cantidad_necesaria = ingrediente['cantidad_estimada']
            cantidad_a_descontar = cantidad_necesaria * cantidad_producida
            
            print(f"--- Descontando {cantidad_a_descontar} de {ingrediente['nombre_insumo']}...")
            if not productos.actualizar_stock(id_insumo, -cantidad_a_descontar):
                raise Exception(f"No se pudo actualizar el stock para el insumo: {ingrediente['nombre_insumo']}")
        
        # 3. Aumentar stock del platillo final
        print(f"+++ Aumentando stock de {receta_data['nombre']} en {cantidad_producida}...")
        if not productos.actualizar_stock(id_producto_final, cantidad_producida):
             raise Exception("No se pudo actualizar el stock del producto final.")
        
        # 4. Registrar el evento en la tabla 'produccion'
        produccion.registrar_produccion(id_producto_final, cantidad_producida, unidad_id)
        
        print("✅ Producción registrada y stock actualizado con éxito.")
        return True

    except Exception as e:
        print(f"❌ Error crítico en registrar_produccion_de_platillo: {e}")
        print("ℹ️ Es posible que el inventario esté en un estado inconsistente. Se requiere revisión manual.")
        return False