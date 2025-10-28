import sys
from pprint import pprint
from . import logica_negocio
from . import productos
from . import unidades_medida
from . import recetas
from . import familias
from decimal import Decimal

def _mostrar_productos_disponibles(con_stock: bool = False):
    print("\n--- 📦 Productos Disponibles ---")
    lista = productos.obtener_todos_los_productos(solo_activos=True)
    if not lista: print("ℹ️ No hay productos registrados."); return False
    
    if con_stock:
        pprint([f"ID: {p['id_producto']} | {p['nombre']} (Stock: {p['stock_convertido']:.3f} {p['unidad_nombre']})" for p in lista])
    else:
        pprint([f"ID: {p['id_producto']} | {p['nombre']}" for p in lista])
    return True

def _mostrar_unidades():
    print("\n--- 📏 Unidades de Medida ---")
    lista = unidades_medida.obtener_todas_las_unidades()
    if not lista: print("ℹ️ No hay unidades registradas."); return False
    pprint([f"ID: {u['id']} | {u['nombre']}" for u in lista])
    return True

def _mostrar_familias():
    print("\n--- 👪 Familias Disponibles ---")
    lista = familias.obtener_todas_las_familias()
    if not lista: print("❌ No hay familias registradas."); return False
    pprint([f"ID: {f['id_familia']} | {f['nombre']}" for f in lista])
    return True

def _capturar_ingredientes():
    ingredientes = []
    while True:
        print("\n--- Añadiendo Ingrediente ---")
        if not _mostrar_productos_disponibles():
            print("❌ No puede agregar ingredientes si no hay productos."); return []
        id_insumo_str = input("ID del producto/insumo (o 'fin' para terminar): ")
        if id_insumo_str.lower() == 'fin': break
        try:
            id_insumo = int(id_insumo_str)
            cantidad = float(input(f"Cantidad estimada del insumo (ID {id_insumo}): "))
            if not _mostrar_unidades(): continue
            unidad_id = int(input(f"ID de la unidad de medida para este insumo: "))
            ingredientes.append({'id_insumo': id_insumo, 'cantidad': cantidad, 'unidad_id': unidad_id})
            print(f"✅ Ingrediente (ID {id_insumo}) agregado.")
        except (ValueError, TypeError):
            print("❌ Error: Ingrese un número válido.")
    return ingredientes
def cargar_ventas_excel_ui():
    """
    Interfaz para pedir al usuario la ruta del archivo Excel.
    """
    print("\n--- 📂 Cargar Ventas desde Excel ---")
    try:
        ruta_archivo = input("Arrastra el archivo Excel a la consola o escribe la ruta completa y presiona Enter: ")
        logica_negocio.procesar_ventas_excel(ruta_archivo)
        
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado en la interfaz: {e}")


def registrar_produccion_simple_ui():
    """Interfaz para registrar una PRODUCCIÓN SIMPLE (Suma a Stock, sin receta)."""
    print("\n--- 🍳 Registrar Producción Simple (Ej: Helados, Cremas) ---")
    try:
        if not _mostrar_productos_disponibles(): 
            return
            
        id_prod = int(input("ID del producto que se produjo (ej. Helado de Chocolate): "))
        cantidad = float(input("Cantidad producida: "))
        
        if not _mostrar_unidades(): 
            return
        unidad_id = int(input("ID de la unidad de medida: "))
        
        obs = input("Observaciones (opcional): ") or "Producción interna"
        logica_negocio.registrar_produccion_simple(id_prod, cantidad, unidad_id, obs)

    except (ValueError, TypeError):
        print("❌ Error de entrada: Ingrese un valor numérico válido.")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado: {e}")


def registrar_compra_ui():
    print("\n--- 🚚 Registrar Compra (Entrada de Insumo) ---")
    try:
        if not _mostrar_productos_disponibles(con_stock=True): return
        id_prod = int(input("ID del producto/insumo comprado: "))
        cantidad = float(input("Cantidad comprada (ej. 10): "))
        
        if not _mostrar_unidades(): return
        unidad_id = int(input("ID de la unidad de medida de la compra (ej. 'Kilogramo'): "))
        logica_negocio.registrar_compra_logica(id_prod, cantidad, unidad_id)
        
    except (ValueError, TypeError):
        print("❌ Error de entrada: Ingrese un valor numérico válido.")

def registrar_merma_ui():
    print("\n--- 🗑️ Registrar Merma (Desperdicio) ---")
    try:
        if not _mostrar_productos_disponibles(con_stock=True): return
        id_prod = int(input("ID del producto/insumo perdido: "))
        cantidad = float(input("Cantidad perdida (positiva): "))
        if not _mostrar_unidades(): return
        unidad_id = int(input("ID de la unidad de medida: "))
        obs = input("Observaciones (causa de la merma): ")
        logica_negocio.registrar_merma_logica(id_prod, cantidad, unidad_id, obs)
    except (ValueError, TypeError):
        print("❌ Error de entrada: Ingrese un valor numérico válido.")

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
                unidad_id = int(input("ID de la unidad de medida *principal* (ej. Litro): "))             
                if not _mostrar_familias(): continue
                id_familia = int(input("ID de la familia del producto: "))  
                stock_inicial_input = float(input(f"Stock inicial (en la unidad principal, ej. 'Litros'): "))
                factor = unidades_medida.obtener_factor_base(unidad_id) 
                if factor is None:
                    print("❌ Unidad no válida. No se pudo crear el producto."); continue
                stock_base = Decimal(str(stock_inicial_input)) * Decimal(factor)
                codigo_sr = input("Código SoftRestaurant (opcional, presiona Enter para omitir): ")
                codigo_softrestaurante = int(codigo_sr) if codigo_sr.isdigit() else None
                es_prod = input("¿Es un platillo producido? (s/n): ").lower() == 's'
                es_vend = input("¿Es un producto vendible? (s/n): ").lower() == 's'
                
                nuevo = productos.crear_producto(
                    nombre=nombre, 
                    unidad_id=unidad_id, 
                    id_familia=id_familia, 
                    stock_inicial=stock_base,  
                    codigo_softrestaurante=codigo_softrestaurante,
                    es_producido=es_prod, 
                    es_vendido=es_vend
                )
                print(f"✅ Producto creado con éxito. ID: {nuevo['id_producto']} (Stock base: {stock_base} g/ml)")
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
        except Exception as e:
            print(f"❌ Ocurrió un error inesperado: {e}")


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
                if detalle: pprint(detalle);
                else: print("❌ No se encontró la receta.");
            elif opcion == '3':
                break
            else:
                print("❌ Opción no válida.")
        except (ValueError, TypeError):
            print("❌ Error de entrada: Ingrese un valor numérico válido.")

def main():
    while True:
        print("\n===== 🥗 ProteinTrack - Menú Principal 🥗 =====")
        print("--- OPERACIONES DIARIAS ---")
        print("1. 📂 Cargar Ventas desde Excel") 
        print("2. 🍳 Registrar Producción de Platillo (Manual)")
        print("3. 🚚 Registrar Compra (Entrada de Insumo)")
        print("4. 🗑️ Registrar Merma (Desperdicio)")
        print("\n--- ADMINISTRACIÓN ---")
        print("5. 📦 Gestionar Catálogo de Productos")
        print("6. 🍲 Gestionar Recetas")
        print("7. 📏 Gestionar Unidades de Medida (Próximamente)")
        print("8. Salir")
        
        opcion = input("Seleccione una opción: ")

        if opcion == '1':
            cargar_ventas_excel_ui()
        elif opcion == '2':
            registrar_produccion_simple_ui()
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