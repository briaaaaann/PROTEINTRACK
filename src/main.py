import sys
from pprint import pprint
from . import logica_negocio
from . import productos
from . import unidades_medida
from . import recetas
from . import familias
from decimal import Decimal

# --- INICIO: FUNCIONES DE AYUDA GLOBALES ---
# (Movimos estas funciones aquí para que sean reutilizables)

def _input_decimal(mensaje: str, default_cero: bool = False) -> Decimal:
    """Pide un número decimal al usuario de forma segura."""
    while True:
        valor_str = input(mensaje)
        if default_cero and valor_str == "":
            return Decimal("0")
        try:
            return Decimal(valor_str)
        except Exception:
            print("❌ Error: Ingrese un valor numérico válido (ej. 10.5).")

def _input_bool(mensaje: str, default: bool = True) -> bool:
    """Pide un Sí/No al usuario de forma segura."""
    default_str = "s" if default else "n"
    while True:
        valor_str = input(mensaje).strip().lower() or default_str
        if valor_str == 's':
            return True
        elif valor_str == 'n':
            return False
        else:
            print("❌ Error: Responda solo 's' (sí) o 'n' (no).")

def _mostrar_productos_disponibles(con_stock: bool = False):
    print("\n--- 📦 Productos Disponibles ---")
    lista = productos.obtener_todos_los_productos(solo_activos=True)
    if not lista: 
        print("ℹ️ No hay productos registrados.")
        return False
    
    if con_stock:
        pprint([f"ID: {p['id_producto']} | {p['nombre']} (Stock: {p['stock_convertido']:.3f} {p['unidad_nombre']})" for p in lista])
    else:
        pprint([f"ID: {p['id_producto']} | {p['nombre']}\t(CLAVE: {p['codigo_softrestaurant']})" for p in lista])
    return True

def _mostrar_unidades():
    print("\n--- 📏 Unidades de Medida ---")
    lista = unidades_medida.obtener_todas_las_unidades()
    if not lista: 
        print("ℹ️ No hay unidades registradas.")
        return False
    pprint([f"ID: {u['id']} | {u['nombre']}\t(Base: {u['factor_base']})" for u in lista])
    return True

def _mostrar_familias():
    print("\n--- 👪 Familias Disponibles ---")
    lista = familias.obtener_todas_las_familias()
    if not lista: 
        print("ℹ️ No hay familias registradas.")
        return False
    pprint([f"ID: {f['id_familia']} | {f['nombre']}" for f in lista])
    return True

# --- FIN: FUNCIONES DE AYUDA GLOBALES ---


def _crear_producto_interactivo(codigo_sr_default: str, nombre_default: str, fila_excel: dict) -> int:
    """
    UI interactiva para crear un nuevo producto. 
    Llamada desde el proceso de ventas cuando un producto no se encuentra.
    Retorna el nuevo ID de producto, o None si se cancela.
    """
    print("\n" + "="*40)
    print("--- 🆕 Registrar Producto Faltante ---")
    print(f"El Excel reportó un producto con:")
    print(f"  CLAVE: {codigo_sr_default}")
    print(f"  NOMBRE: {nombre_default}")
    print(f"  FAMILIA (GRUPO): {fila_excel.get('GRUPO', 'No encontrada')}")
    print("="*40)
    
    confirmar = input("¿Desea registrar este producto ahora? (s/n): ").strip().lower()
    if confirmar != 's':
        return None

    try:
        # Usar los valores del Excel o pedir al usuario que los corrija
        nombre = input(f"Confirmar Nombre (default: {nombre_default}): ").strip().upper() or nombre_default.upper()
        codigo_sr = input(f"Confirmar CLAVE (default: {codigo_sr_default}): ").strip() or codigo_sr_default
        
        # Intentar adivinar la familia
        familia_excel = fila_excel.get('GRUPO', '')
        familia_encontrada = familias.obtener_familia_por_nombre(familia_excel)
        
        if familia_encontrada:
            print(f"ℹ️  Familia '{familia_excel}' encontrada con ID: {familia_encontrada['id_familia']}")
            id_familia = familia_encontrada['id_familia']
        else:
            print(f"⚠️  No se encontró la familia '{familia_excel}'. Seleccione una:")
            if not _mostrar_familias(): return None
            id_familia = int(input("ID de Familia: "))
        
        if not _mostrar_unidades(): return None
        unidad_id = int(input("ID de Unidad de Medida (ej. 10=Pz, 7=Kg, 8=L): "))
        
        stock_inicial = _input_decimal("Stock Inicial (en la unidad elegida, ej. 10.5): ", default_cero=True)
        
        # Convertir stock a unidad base para la BD
        factor = unidades_medida.obtener_factor_base(unidad_id)
        stock_base = stock_inicial * factor
        
        es_vendido = _input_bool("¿Es un producto vendible? (s/n, default 's'): ", default=True)
        es_producido = _input_bool("¿Es un producto producido (usa receta)? (s/n, default 'n'): ", default=False)
        
        # Crear el producto en la BD
        nuevo_prod = productos.crear_producto(
            nombre=nombre,
            unidad_id=unidad_id,
            id_familia=id_familia,
            stock_inicial=stock_base,
            codigo_softrestaurante=codigo_sr,
            es_producido=es_producido,
            es_vendido=es_vendido,
            activo=True
        )
        
        if nuevo_prod:
            nuevo_id = nuevo_prod['id_producto']
            print(f"✅ Producto '{nombre}' (ID: {nuevo_id}) creado con éxito.")
            
            # Si es producido, preguntar por la receta
            if es_producido:
                print("ℹ️  El producto se marcó como 'producido'.")
                crear_receta = _input_bool("¿Desea crear su receta AHORA? (s/n): ", default=False)
                if crear_receta:
                    # (Llamada a la función de UI de recetas)
                    _gestionar_ingredientes_receta_ui(nuevo_id, nombre)
                else:
                    print("Recuerde crear la receta más tarde desde el Menú 6.")
                    
            return nuevo_id
        else:
            print("❌ Error: No se pudo crear el producto en la BD.")
            return None
    
    except Exception as e:
        print(f"❌ Error fatal durante la creación: {e}")
        return None


def cargar_ventas_excel_ui():
    print("\n--- 📂 Cargar Ventas desde Excel ---")
    ruta = input("Arrastra el archivo Excel a la consola o escribe la ruta completa y presiona Enter: ")
    
    # --- MODIFICACIÓN ---
    # Pasamos la función interactiva como un 'callback'
    logica_negocio.procesar_ventas_excel(ruta, _crear_producto_interactivo)
    # --- FIN DE MODIFICACIÓN ---


def registrar_produccion_simple_ui():
    """UI para registrar producción simple (ej. Helados, Cremas)."""
    print("\n--- 🍳 Registrar Producción Simple ---")
    print("Seleccione el producto que ha producido (ej. HELADO, CREMA):")
    
    # Filtramos para mostrar solo productos marcados como 'es_producido'
    lista_producibles = [p for p in productos.obtener_todos_los_productos() if p['es_producido']]
    if not lista_producibles:
        print("❌ Error: No hay productos marcados como 'producibles'.")
        print("Vaya a 'Gestionar Catálogo' y marque la casilla 'es_producido' en sus productos base.")
        return

    pprint([f"ID: {p['id_producto']} | {p['nombre']}\t(Stock: {p['stock_convertido']:.3f} {p['unidad_nombre']})" for p in lista_producibles])
    
    try:
        id_prod = int(input("ID del producto a sumar stock: "))
        
        # Validar que el ID esté en la lista de producibles
        producto_seleccionado = next((p for p in lista_producibles if p['id_producto'] == id_prod), None)
        
        if not producto_seleccionado:
            print("❌ Error: ID no válido o el producto no está marcado como 'producible'.")
            return
            
        print(f"Producto seleccionado: {producto_seleccionado['nombre']}")
        print(f"Unidad de medida: {producto_seleccionado['unidad_nombre']}")
        
        cantidad = _input_decimal(f"Cantidad a sumar (en {producto_seleccionado['unidad_nombre']}): ")
        
        if cantidad <= 0:
            print("❌ Error: La cantidad debe ser positiva.")
            return

        print("\n--- 🥣 Registrando consumo de receta (si existe)... ---")
        
        # Llamamos a la lógica de negocio
        if logica_negocio.registrar_produccion_simple(
            id_producto=id_prod,
            cantidad=cantidad,
            unidad_id=producto_seleccionado['unidad']
        ):
            print("✅ Producción registrada y stock actualizado con éxito.")
        else:
            print("❌ Fallo al registrar la producción. Revise los mensajes de error.")
            
    except ValueError:
        print("❌ Error: ID y cantidad deben ser números.")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")


def registrar_compra_ui():
    """UI para registrar la compra o entrada de un insumo."""
    print("\n--- 🚚 Registrar Compra (Entrada de Stock) ---")
    if not _mostrar_productos_disponibles(con_stock=True): return
    
    try:
        id_prod = int(input("ID del producto que compró: "))
        producto_info = productos.obtener_producto_por_id_completo(id_prod)
        if not producto_info:
            print("❌ Error: ID de producto no válido.")
            return
            
        print(f"Producto seleccionado: {producto_info['nombre']}")
        print(f"Unidad de medida base: {producto_info['unidad_base_nombre']}")
        
        if not _mostrar_unidades(): return
        unidad_compra_id = int(input(f"¿En qué unidad compró? (ej. {producto_info['unidad_nombre']}, Costal, Caja, etc.): "))
        cantidad_compra = _input_decimal(f"Cantidad comprada (en la unidad que seleccionó): ")
        
        if logica_negocio.registrar_compra_logica(id_prod, cantidad_compra, unidad_compra_id):
            print("✅ Compra registrada y stock actualizado.")
        else:
            print("❌ Error al registrar la compra.")
            
    except ValueError:
        print("❌ Error: ID y cantidad deben ser números.")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")


def registrar_merma_ui():
    """UI para registrar merma o desperdicio."""
    print("\n--- 🗑️ Registrar Merma (Salida de Stock) ---")
    if not _mostrar_productos_disponibles(con_stock=True): return
    
    try:
        id_prod = int(input("ID del producto a dar de baja: "))
        producto_info = productos.obtener_producto_por_id_completo(id_prod)
        if not producto_info:
            print("❌ Error: ID de producto no válido.")
            return
            
        print(f"Producto seleccionado: {producto_info['nombre']}")
        print(f"Stock actual: {producto_info['stock_convertido']:.3f} {producto_info['unidad_nombre']}")
        
        if not _mostrar_unidades(): return
        unidad_merma_id = int(input(f"¿En qué unidad midió la merma? (ej. {producto_info['unidad_nombre']}, {producto_info['unidad_base_nombre']}, etc.): "))
        cantidad_merma = _input_decimal(f"Cantidad de merma (en la unidad que seleccionó): ")
        observaciones = input("Observaciones (opcional): ")

        if logica_negocio.registrar_merma_logica(id_prod, cantidad_merma, unidad_merma_id, observaciones):
            print("✅ Merma registrada y stock actualizado.")
        else:
            print("❌ Error al registrar la merma.")
            
    except ValueError:
        print("❌ Error: ID y cantidad deben ser números.")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")


def _crear_nuevo_producto_ui():
    """UI para el sub-menú de crear un producto."""
    print("\n--- + Crear Nuevo Producto ---")
    try:
        nombre = input("Nombre del producto: ").strip().upper()
        codigo_sr = input("Código/Clave de Soft Restaurant (opcional): ").strip() or None
        
        if not _mostrar_familias(): return
        id_familia = int(input("ID de Familia: "))
        
        if not _mostrar_unidades(): return
        unidad_id = int(input("ID de Unidad de Medida (ej. L, Kg, Pz): "))
        
        stock_inicial = _input_decimal("Stock Inicial (en la unidad elegida, ej. 10.5): ", default_cero=True)
        
        # Convertir stock a unidad base para la BD
        factor = unidades_medida.obtener_factor_base(unidad_id)
        stock_base = stock_inicial * factor
        
        es_vendido = _input_bool("¿Es un producto vendible? (s/n, default 's'): ", default=True)
        es_producido = _input_bool("¿Es un producto producido (usa receta o es base)? (s/n, default 'n'): ", default=False)
        
        nuevo_prod = productos.crear_producto(
            nombre=nombre,
            unidad_id=unidad_id,
            id_familia=id_familia,
            stock_inicial=stock_base,
            codigo_softrestaurante=codigo_sr,
            es_producido=es_producido,
            es_vendido=es_vendido,
            activo=True
        )
        if nuevo_prod:
            print(f"✅ Producto '{nombre}' (ID: {nuevo_prod['id_producto']}) creado con éxito.")
        else:
            print("❌ Error: No se pudo crear el producto.")
            
    except Exception as e:
        print(f"❌ Error fatal durante la creación: {e}")


def gestionar_productos_ui():
    """UI para el menú de gestión de productos (CRUD)."""
    while True:
        print("\n--- 📦 Gestión de Catálogo de Productos ---")
        print("1. Ver todos los productos")
        print("2. Crear nuevo producto")
        print("3. Editar producto (Próximamente)")
        print("4. Desactivar producto")
        print("5. Volver al menú principal")
        
        opcion = input("Seleccione una opción: ")
        
        if opcion == '1':
            _mostrar_productos_disponibles(con_stock=True)
        elif opcion == '2':
            _crear_nuevo_producto_ui()
        elif opcion == '3':
            print("ℹ️ Función no implementada.")
        elif opcion == '4':
            print("\n--- - Desactivar Producto ---")
            if not _mostrar_productos_disponibles(): return
            try:
                id_prod = int(input("ID del producto a desactivar: "))
                if productos.desactivar_producto(id_prod):
                    print(f"✅ Producto ID {id_prod} desactivado. Ya no aparecerá en listas.")
                else:
                    print("❌ Error: No se pudo desactivar el producto (¿ID incorrecto?).")
            except ValueError:
                print("❌ Error: Ingrese un ID numérico.")
        elif opcion == '5':
            break
        else:
            print("❌ Opción no válida.")


def _gestionar_ingredientes_receta_ui(id_producto_final: int, nombre_producto: str):
    """UI interactiva para añadir ingredientes a una nueva receta."""
    print(f"\n--- 🍲 Creando receta para: {nombre_producto} ---")
    nombre_receta = input(f"Nombre de la receta (default: 'Receta de {nombre_producto}'): ") or f"Receta de {nombre_producto}"
    
    ingredientes = []
    while True:
        print(f"\nIngredientes actuales: {len(ingredientes)}")
        if not _mostrar_productos_disponibles(con_stock=True):
            print("⚠️ No hay productos/insumos para agregar.")
            break
            
        try:
            id_insumo_str = input("ID del insumo a agregar (o 'listo' para terminar): ")
            if id_insumo_str.lower() == 'listo':
                break
            
            id_insumo = int(id_insumo_str)
            insumo_info = productos.obtener_producto_por_id_completo(id_insumo)
            if not insumo_info:
                print("❌ ID no válido.")
                continue

            print(f"Insumo seleccionado: {insumo_info['nombre']}")
            print(f"Unidad base: {insumo_info['unidad_base_nombre']}")
            if not _mostrar_unidades(): continue
            
            unidad_id = int(input("ID de la unidad de medida para este ingrediente: "))
            cantidad = _input_decimal(f"Cantidad (en la unidad seleccionada): ")
            
            # Convertir a unidad base para guardar en BD
            factor = unidades_medida.obtener_factor_base(unidad_id)
            cantidad_base = cantidad * factor
            
            print(f"ℹ️  Se guardará {cantidad_base} {insumo_info['unidad_base_nombre']} (base).")
            
            ingredientes.append({
                'id_insumo': id_insumo,
                'cantidad': cantidad_base, # Guardamos en unidad base
                'unidad_id': unidades_medida.obtener_id_unidad_base(unidad_id) # Guardamos el ID de la unidad base (g/ml/pz)
            })
            
        except ValueError:
            print("❌ Error: ID y cantidad deben ser numéricos.")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")

    if not ingredientes:
        print("⚠️ No se agregaron ingredientes. Receta no creada.")
        return False
        
    try:
        nueva_receta = recetas.crear_receta(id_producto_final, nombre_receta, ingredientes)
        if nueva_receta:
            print(f"✅ Receta (ID: {nueva_receta['id_receta']}) creada con éxito con {len(ingredientes)} ingredientes.")
            return True
        else:
            print("❌ Error: No se pudo guardar la receta en la base de datos.")
            return False
    except Exception as e:
        print(f"❌ Error fatal al guardar la receta: {e}")
        return False


def gestionar_recetas_ui():
    """UI para el menú de gestión de recetas."""
    while True:
        print("\n--- 🍲 Gestión de Recetas ---")
        print("1. Ver todas las recetas")
        print("2. Crear nueva receta")
        print("3. Ver detalle de receta")
        print("4. Eliminar receta (Próximamente)")
        print("5. Volver al menú principal")
        
        opcion = input("Seleccione una opción: ")
        
        if opcion == '1':
            print("\n--- 📜 Recetas Registradas ---")
            lista = recetas.obtener_todas_las_recetas_con_producto()
            if not lista: 
                print("ℹ️ No hay recetas registradas.")
                continue
            pprint([f"ID Receta: {r['id_receta']} | Producto: {r['nombre_producto']} | Nombre Receta: {r['nombre']}" for r in lista])
            
        elif opcion == '2':
            print("\n--- + Crear Nueva Receta ---")
            print("Seleccione el producto FINAL al que pertenece esta receta:")
            if not _mostrar_productos_disponibles():
                continue
            try:
                id_prod = int(input("ID del producto final: "))
                prod_info = productos.obtener_producto_por_id(id_prod)
                if not prod_info:
                    print("❌ ID no válido.")
                    continue
                _gestionar_ingredientes_receta_ui(id_prod, prod_info['nombre'])
            except ValueError:
                print("❌ Error: ID debe ser un número.")
                
        elif opcion == '3.':
            print("\n--- ℹ️ Ver Detalle de Receta ---")
            try:
                id_rec = int(input("ID de la receta a consultar: "))
                detalle = recetas.obtener_receta_completa(id_rec)
                if not detalle:
                    print("❌ No se encontró la receta.")
                    continue
                
                print(f"\n--- Detalle Receta ID: {detalle['id_receta']} ---")
                print(f"Nombre: {detalle['nombre']}")
                print(f"Producto Final ID: {detalle['id_producto_final']}")
                print("Ingredientes:")
                pprint(detalle['ingredientes'])
                
            except ValueError:
                print("❌ Error: ID debe ser un número.")
                
        elif opcion == '4':
            print("ℹ️ Función no implementada.")
            
        elif opcion == '5':
            break
        else:
            print("❌ Opción no válida.")


def main():
    while True:
        print("\n===== 🥗 ProteinTrack - Menú Principal 🥗 =====")
        print("--- OPERACIONES DIARIAS ---")
        print("1. 📂 Cargar Ventas desde Excel") 
        print("2. 🍳 Registrar Producción Simple (Helados, Cremas)")
        print("3. 🚚 Registrar Compra (Entrada de Insumo)")
        print("4. 🗑️ Registrar Merma (Desperdicio)")
        print("\n--- ADMINISTRACIÓN ---")
        print("5. 📦 Gestionar Catálogo de Productos")
        print("6. 🍲 Gestionar Recetas")
        print("7. 👪 Gestionar Familias (Próximamente)")
        print("8. 📏 Gestionar Unidades de Medida (Próximamente)")
        print("9. Salir")
        
        opcion = input("Seleccione una opción: ")

        if opcion == '1':
            cargar_ventas_excel_ui()
        elif opcion == '2':
            registrar_produccion_simple_ui()
        elif opcion == '3':
            registrar_compra_ui()
        elif opcion == '4.':
            registrar_merma_ui()
        elif opcion == '5':
            gestionar_productos_ui()
        elif opcion == '6':
            gestionar_recetas_ui()
        elif opcion == '7':
             print("ℹ️ Función 'Gestionar Familias' no implementada en este menú.")
        elif opcion == '8':
            print("ℹ️ Función 'Gestionar Unidades' no implementada en este menú.")
        elif opcion == '9':
            print("👋 ¡Hasta luego!")
            sys.exit(0)
        else:
            print("❌ Opción no válida. Intente de nuevo.")

if __name__ == "__main__":
    main()