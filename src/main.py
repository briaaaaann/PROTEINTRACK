import sys
from pprint import pprint
from . import logica_negocio
from . import productos
from . import unidades_medida
from . import recetas
from . import familias

def _mostrar_productos_disponibles(con_stock: bool = False):

    print("\n--- 📦 Productos Disponibles ---")
    lista = productos.obtener_todos_los_productos(solo_activos=True)
    if not lista:
        print("ℹ️ No hay productos registrados.")
        return False
    
    if con_stock:
        pprint([f"ID: {p['id_producto']} | {p['nombre']} (Stock: {p['stock']})" for p in lista])
    else:
        pprint([f"ID: {p['id_producto']} | {p['nombre']}" for p in lista])
    return True

def _mostrar_unidades():

    print("\n--- 📏 Unidades de Medida ---")
    lista = unidades_medida.obtener_todas_las_unidades()
    if not lista:
        print("ℹ️ No hay unidades registradas.")
        return False
    pprint([f"ID: {u['id']} | {u['nombre']}" for u in lista])
    return True

def _mostrar_familias():
    print("\n--- 👪 Familias Disponibles ---")
    # Llama al CRUD de familias para obtener los datos
    lista = familias.obtener_todas_las_familias()
    if not lista:
        print("❌ No hay familias registradas. Debe crear familias primero.")
        return False

    pprint([f"ID: {f['id_familia']} | {f['nombre']}" for f in lista])
    return True

def _capturar_ingredientes():

    ingredientes = []
    while True:
        print("\n--- Añadiendo Ingrediente ---")
        if not _mostrar_productos_disponibles():
            print("❌ No puede agregar ingredientes si no hay productos.")
            return []
            
        id_insumo_str = input("ID del producto/insumo (o 'fin' para terminar): ")
        if id_insumo_str.lower() == 'fin':
            break
            
        try:
            id_insumo = int(id_insumo_str)
            cantidad = float(input(f"Cantidad estimada del insumo (ID {id_insumo}): "))
            
            if not _mostrar_unidades():
                continue
            unidad_id = int(input(f"ID de la unidad de medida para este insumo: "))
            
            ingredientes.append({
                'id_insumo': id_insumo,
                'cantidad': cantidad,
                'unidad_id': unidad_id
            })
            print(f"✅ Ingrediente (ID {id_insumo}) agregado.")
            
        except (ValueError, TypeError):
            print("❌ Error: Ingrese un número válido.")
            
    return ingredientes

# --- INTERFAZ DE USUARIO (UI) PARA OPERACIONES ---

def registrar_venta_ui():
    print("\n--- 💵 Registrar Venta ---")
    try:
        if not _mostrar_productos_disponibles(con_stock=True):
            return # Salir si no hay productos
            
        id_prod = int(input("ID del producto vendido: "))
        cantidad = float(input("Cantidad vendida: "))
        precio = float(input("Precio unitario: "))
        logica_negocio.registrar_venta_logica(id_prod, cantidad, precio)
        
    except (ValueError, TypeError):
        print("❌ Error de entrada: Ingrese un valor numérico válido.")

def registrar_produccion_ui():
    """Interfaz para capturar datos y registrar una PRODUCCIÓN."""
    print("\n--- 🍳 Registrar Producción de Platillo ---")
    try:
        if not _mostrar_productos_disponibles():
            return
            
        id_prod = int(input("ID del platillo (producto final) a producir: "))
        cantidad = float(input("Cantidad a producir: "))
        
        if not _mostrar_unidades():
            return
        unidad_id = int(input("ID de la unidad de medida (para el platillo): "))
        logica_negocio.registrar_produccion_de_platillo(id_prod, cantidad, unidad_id)

    except (ValueError, TypeError):
        print("❌ Error de entrada: Ingrese un valor numérico válido.")

def registrar_compra_ui():
    """Interfaz para registrar una COMPRA (entrada de insumo)."""
    print("\n--- 🚚 Registrar Compra (Entrada de Insumo) ---")
    try:
        if not _mostrar_productos_disponibles(con_stock=True):
            return
        id_prod = int(input("ID del producto/insumo comprado: "))
        cantidad = float(input("Cantidad comprada (positiva): "))
        logica_negocio.registrar_compra_logica(id_prod, cantidad)
        
    except (ValueError, TypeError):
        print("❌ Error de entrada: Ingrese un valor numérico válido.")

def registrar_merma_ui():
    """Interfaz para registrar una MERMA (pérdida)."""
    print("\n--- 🗑️ Registrar Merma (Desperdicio) ---")
    try:
        if not _mostrar_productos_disponibles(con_stock=True):
            return
            
        id_prod = int(input("ID del producto/insumo perdido: "))
        cantidad = float(input("Cantidad perdida (positiva): "))
        
        if not _mostrar_unidades():
            return
        unidad_id = int(input("ID de la unidad de medida: "))
        obs = input("Observaciones (causa de la merma): ")
        
        # ¡Llamada única a la lógica de negocio!
        logica_negocio.registrar_merma_logica(id_prod, cantidad, unidad_id, obs)
        
    except (ValueError, TypeError):
        print("❌ Error de entrada: Ingrese un valor numérico válido.")

# --- INTERFAZ DE USUARIO (UI) PARA GESTIÓN DE CATÁLOGOS ---

def gestionar_productos_ui():

    while True:
        print("\n--- 📦 Gestión de Catálogo de Productos ---")
        print("1. Crear nuevo producto")
        print("2. Ver todos los productos")
        print("3. Desactivar un producto")
        print("4. Volver al menú principal")
        
        opcion = input("Seleccione: ")
        try:
            if opcion == '1':
                nombre = input("Nombre del producto: ")
                if not _mostrar_unidades(): continue
                unidad_id = int(input("ID de la unidad de medida: "))
                if not _mostrar_familias(): continue
                id_familia = int(input("ID de la familia del producto: "))
                stock = float(input("Stock inicial: "))
                es_prod = input("¿Es un platillo producido? (s/n): ").lower() == 's'
                es_vend = input("¿Es un producto vendible? (s/n): ").lower() == 's'
                nuevo = productos.crear_producto(nombre = nombre, unidad_id = unidad_id, id_familia = id_familia, stock_inicial = stock, es_producido = es_prod, es_vendido = es_vend)
                print(f"✅ Producto creado con éxito. ID: {nuevo['id_producto']}")
            
            elif opcion == '2':
                _mostrar_productos_disponibles(con_stock=True)

            elif opcion == '3':
                id_prod = int(input("ID del producto a desactivar: "))
                if productos.desactivar_producto(id_prod):
                    print("✅ Producto desactivado.")
                else:
                    print("❌ Error: No se encontró el producto.")
            
            elif opcion == '4':
                break
            else:
                print("❌ Opción no válida.")
        except (ValueError, TypeError):
            print("❌ Error de entrada: Ingrese un valor numérico válido.")

def gestionar_recetas_ui():
    while True:
        print("\n--- 🍲 Gestión de Recetas ---")
        print("1. Crear nueva receta")
        print("2. Ver detalle de receta")
        print("3. Volver al menú principal")
        
        opcion = input("Seleccione: ")
        try:
            if opcion == '1':
                if not _mostrar_productos_disponibles(): continue
                id_prod_final = int(input("ID del producto final (platillo) para esta receta: "))
                nombre_receta = input("Nombre de la receta (ej. 'Ensalada César v1'): ")
                
                ingredientes = _capturar_ingredientes()
                
                if ingredientes:
                    nueva = recetas.crear_receta(id_prod_final, nombre_receta, ingredientes)
                    print(f"✅ Receta creada con éxito. ID: {nueva['id_receta']}")
                else:
                    print("ℹ️ No se agregaron ingredientes. Receta no creada.")

            elif opcion == '2':
                id_receta = int(input("ID de la receta a consultar: "))
                detalle = recetas.obtener_receta_completa(id_receta)
                if detalle:
                    pprint(detalle)
                else:
                    print("❌ No se encontró la receta.")
            
            elif opcion == '3':
                break
            else:
                print("❌ Opción no válida.")
        except (ValueError, TypeError):
            print("❌ Error de entrada: Ingrese un valor numérico válido.")

# --- FUNCIÓN PRINCIPAL (MENÚ) ---

def main():
    while True:
        print("\n===== 🥗 ProteinTrack - Menú Principal 🥗 =====")
        print("--- OPERACIONES DIARIAS ---")
        print("1. 💵 Registrar Venta")
        print("2. 🍳 Registrar Producción de Platillo")
        print("3. 🚚 Registrar Compra (Entrada de Insumo)")
        print("4. 🗑️ Registrar Merma (Desperdicio)")
        print("\n--- ADMINISTRACIÓN ---")
        print("5. 📦 Gestionar Catálogo de Productos")
        print("6. 🍲 Gestionar Recetas")
        print("7. 📏 Gestionar Unidades de Medida (Próximamente)")
        print("8. Salir")
        
        opcion = input("Seleccione una opción: ")

        if opcion == '1':
            registrar_venta_ui()
        elif opcion == '2':
            registrar_produccion_ui()
        elif opcion == '3':
            registrar_compra_ui()
        elif opcion == '4':
            registrar_merma_ui()
        elif opcion == '5':
            gestionar_productos_ui()
        elif opcion == '6':
            gestionar_recetas_ui()
        elif opcion == '7':
            print("ℹ️ Función 'Gestionar Unidades' no implementada en este menú.")
            pass
        elif opcion == '8':
            print("👋 ¡Hasta luego!")
            sys.exit() 
        else:
            print("❌ Opción no válida. Por favor, intente de nuevo.")

if __name__ == "__main__":
    main()