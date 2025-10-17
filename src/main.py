import sys
from pprint import pprint
from datetime import datetime

# Usamos importaciones relativas porque estamos dentro del paquete 'src'
from . import productos
from . import unidades_medida
from . import ventas
from . import produccion
from . import movimientos_inventario
# from . import recetas # Descomenta cuando quieras probar recetas

def gestionar_productos():
    """Submenú para las operaciones CRUD de productos."""
    while True:
        print("\n--- 📦 Gestión de Productos ---")
        print("1. Crear nuevo producto")
        print("2. Ver todos los productos")
        print("3. Actualizar stock de un producto")
        print("4. Desactivar un producto")
        print("5. Volver al menú principal")
        
        opcion = input("Seleccione una opción: ")

        try:
            if opcion == '1':
                nombre = input("Nombre del producto: ")
                # Aquí listaríamos las unidades para que el usuario elija
                pprint(unidades_medida.obtener_todas_las_unidades())
                unidad_id = int(input("ID de la unidad de medida: "))
                stock = float(input("Stock inicial: "))
                nuevo = productos.crear_producto(nombre, unidad_id, stock)
                print(f"✅ Producto creado con éxito. ID: {nuevo['id_producto']}")
            
            elif opcion == '2':
                lista_productos = productos.obtener_todos_los_productos()
                if not lista_productos:
                    print("ℹ️ No hay productos registrados.")
                else:
                    pprint(lista_productos)

            elif opcion == '3':
                id_prod = int(input("ID del producto a actualizar: "))
                cantidad = float(input("Cantidad a sumar (negativo para restar): "))
                if productos.actualizar_stock(id_prod, cantidad):
                    print("✅ Stock actualizado con éxito.")
                else:
                    print("❌ Error: No se encontró el producto.")
            
            elif opcion == '4':
                id_prod = int(input("ID del producto a desactivar: "))
                if productos.desactivar_producto(id_prod):
                    print("✅ Producto desactivado.")
                else:
                    print("❌ Error: No se encontró el producto.")

            elif opcion == '5':
                break
            else:
                print("❌ Opción no válida.")
        except (ValueError, TypeError) as e:
            print(f"❌ Error de entrada: {e}. Por favor, ingrese un valor válido.")
        except Exception as e:
            print(f"❌ Ocurrió un error inesperado: {e}")

def registrar_venta_y_actualizar_stock():
    """Función de Lógica de Negocio: registra una venta y descuenta el stock."""
    print("\n--- 💵 Registrar Venta ---")
    try:
        pprint(productos.obtener_todos_los_productos(solo_activos=True))
        id_prod = int(input("ID del producto vendido: "))
        cantidad = float(input("Cantidad vendida: "))
        precio = float(input("Precio unitario: "))

        # 1. Registrar la venta
        nueva_venta = ventas.registrar_venta(id_prod, cantidad, precio)
        print(f"✅ Venta registrada con ID: {nueva_venta['id_venta']}")

        # 2. Descontar el stock (lógica de negocio)
        productos.actualizar_stock(id_prod, -cantidad)
        print("✅ Stock del producto actualizado.")

    except (ValueError, TypeError) as e:
        print(f"❌ Error de entrada: {e}. Por favor, ingrese un valor válido.")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado: {e}")
        
def registrar_produccion_y_actualizar_stock():
    """Función de Lógica de Negocio: registra producción y aumenta el stock."""
    print("\n--- 🍳 Registrar Producción ---")
    try:
        pprint(productos.obtener_todos_los_productos(solo_activos=True))
        id_prod = int(input("ID del producto producido (platillo): "))
        cantidad = float(input("Cantidad producida: "))
        unidad_id = int(input("ID de la unidad de medida: "))

        # 1. Registrar el evento de producción
        nueva_prod = produccion.registrar_produccion(id_prod, cantidad, unidad_id)
        print(f"✅ Producción registrada con ID: {nueva_prod['id_produccion']}")

        # 2. Aumentar el stock del producto final
        productos.actualizar_stock(id_prod, cantidad)
        print("✅ Stock del producto final actualizado.")
        
        # NOTA: La lógica para descontar insumos se manejaría aquí,
        # consultando la receta del producto.

    except (ValueError, TypeError) as e:
        print(f"❌ Error de entrada: {e}. Por favor, ingrese un valor válido.")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado: {e}")

def main():
    """Función principal que ejecuta el menú."""
    while True:
        print("\n===== 🥗 ProteinTrack - Menú Principal 🥗 =====")
        print("1. Gestionar Productos")
        print("2. Registrar Venta")
        print("3. Registrar Producción")
        # Aquí puedes añadir opciones para los otros módulos (unidades, recetas, etc.)
        print("4. Salir")
        
        opcion = input("Seleccione una opción: ")

        if opcion == '1':
            gestionar_productos()
        elif opcion == '2':
            registrar_venta_y_actualizar_stock()
        elif opcion == '3':
            registrar_produccion_y_actualizar_stock()
        elif opcion == '4':
            print("👋 ¡Hasta luego!")
            sys.exit() # Termina el programa
        else:
            print("❌ Opción no válida. Por favor, intente de nuevo.")

if __name__ == "__main__":
    main()