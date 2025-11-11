import sys
from pprint import pprint
from . import logica_negocio
from . import productos
from . import unidades_medida
from . import recetas
from . import familias
from decimal import Decimal

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

def _crear_producto_interactivo(codigo_sr_default: str, nombre_default: str, fila_excel: dict) -> int:

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
        nombre = input(f"Confirmar Nombre (default: {nombre_default}): ").strip().upper() or nombre_default.upper()
        codigo_sr = input(f"Confirmar CLAVE (default: {codigo_sr_default}): ").strip() or codigo_sr_default
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
        factor = unidades_medida.obtener_factor_base(unidad_id)
        stock_base = stock_inicial * factor
        
        es_vendido = _input_bool("¿Es un producto vendible? (s/n, default 's'): ", default=True)
        es_producido = _input_bool("¿Es un producto producido (usa receta)? (s/n, default 'n'): ", default=False)
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
            if es_producido:
                print("ℹ️  El producto se marcó como 'producido'.")
                crear_receta = _input_bool("¿Desea crear su receta AHORA? (s/n): ", default=False)
                if crear_receta:
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
    logica_negocio.procesar_ventas_excel(ruta, _crear_producto_interactivo)

def registrar_produccion_simple_ui():
    print("\n--- 🍳 Registrar Producción Simple ---")
    print("Seleccione el producto que ha producido (ej. HELADO, CREMA):")
    
    lista_producibles = [p for p in productos.obtener_todos_los_productos() if p['es_producido']]
    if not lista_producibles:
        print("❌ Error: No hay productos marcados como 'producibles'.")
        print("Vaya a 'Gestionar Catálogo' y marque la casilla 'es_producido' en sus productos base.")
        return

    pprint([f"ID: {p['id_producto']} | {p['nombre']}\t(Stock: {p['stock_convertido']:.3f} {p['unidad_nombre']})" for p in lista_producibles])
    
    try:
        id_prod = int(input("ID del producto a sumar stock: "))
        
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
        if logica_negocio.registrar_produccion_simple(
            id_producto=id_prod,
            cantidad=cantidad,
            unidad_id=producto_seleccionado['unidad_id'],
            unidad_nombre=producto_seleccionado['unidad_nombre']
        ):
            print("✅ Producción registrada y stock actualizado con éxito.")
        else:
            print("❌ Fallo al registrar la producción. Revise los mensajes de error.")
            
    except ValueError:
        print("❌ Error: ID y cantidad deben ser números.")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def registrar_merma_ui():
    print("\n--- 🗑️ Registrar Merma (Salida de Stock) ---")
    lista_productos_completa = productos.obtener_todos_los_productos(solo_activos=True)
    
    if not lista_productos_completa:
        print("ℹ️ No hay productos registrados.")
        return
    print("\n--- 📦 Productos Disponibles ---")
    pprint([f"ID: {p['id_producto']} | {p['nombre']} (Stock: {p['stock_convertido']:.3f} {p['unidad_nombre']})" for p in lista_productos_completa])
    
    try:
        id_prod = int(input("ID del producto a dar de baja: "))
        producto_info = next((p for p in lista_productos_completa if p['id_producto'] == id_prod), None)
        
        if not producto_info:
            print("❌ Error: ID de producto no válido.")
            return
            
        print(f"Producto seleccionado: {producto_info['nombre']}")
        print(f"Stock actual: {producto_info['stock_convertido']:.3f} {producto_info['unidad_nombre']}")
        if not _mostrar_unidades(): return
        unidad_merma_id = int(input(f"¿En qué unidad midió la merma? (ej. {producto_info['unidad_nombre']}, Gramo, Mililitro, etc.): "))
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
    print("\n--- + Crear Nuevo Producto ---")
    try:
        nombre = input("Nombre del producto: ").strip().upper()
        codigo_sr = input("Código/Clave de Soft Restaurant (opcional): ").strip() or None
        
        if not _mostrar_familias(): return
        id_familia = int(input("ID de Familia: "))
        
        if not _mostrar_unidades(): return
        unidad_id = int(input("ID de Unidad de Medida (ej. L, Kg, Pz): "))
        
        stock_inicial = _input_decimal("Stock Inicial (en la unidad elegida, ej. 10.5): ", default_cero=True)
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

def _editar_producto_ui():
    print("\n--- ✏️ Editar Producto ---")
    lista_productos_completa = productos.obtener_todos_los_productos(solo_activos=True)
    if not lista_productos_completa:
        print("ℹ️ No hay productos registrados.")
        return

    print("\n--- 📦 Productos Disponibles ---")
    pprint([f"ID: {p['id_producto']} | {p['nombre']} (Stock: {p['stock_convertido']:.3f} {p['unidad_nombre']})" for p in lista_productos_completa])
    
    try:
        id_prod = int(input("\nID del producto a editar: "))
        prod_actual = productos.obtener_producto_por_id(id_prod)
        
        if not prod_actual:
            print("❌ Error: Producto no encontrado.")
            return

        print(f"\nEditando: {prod_actual['nombre']} (ID: {id_prod})")
        print("ℹ️  Deje el campo en blanco para conservar el valor actual.")
        nombre = input(f"Nombre (actual: {prod_actual['nombre']}): ").strip().upper() or prod_actual['nombre']
        codigo_sr = input(f"CLAVE Soft Restaurant (actual: {prod_actual['codigo_softrestaurant']}): ").strip() or prod_actual['codigo_softrestaurant']
        
        print(f"\nFamilia actual: ID {prod_actual['id_familia']}")
        if _input_bool("¿Desea cambiar la familia? (s/n, default 'n'): ", default=False):
            if not _mostrar_familias(): return
            id_familia = int(input("Nuevo ID de Familia: "))
        else:
            id_familia = prod_actual['id_familia']

        print(f"\nUnidad actual: ID {prod_actual['unidad']}")
        if _input_bool("¿Desea cambiar la unidad de medida? (s/n, default 'n'): ", default=False):
            if not _mostrar_unidades(): return
            unidad_id = int(input("Nuevo ID de Unidad: "))
        else:
            unidad_id = prod_actual['unidad']

        print("\n--- Flags Booleanos ---")
        es_vendido = _input_bool(f"¿Es vendible? (actual: {prod_actual['es_vendido']}, default '{'s' if prod_actual['es_vendido'] else 'n'}'): ", default=prod_actual['es_vendido'])
        es_producido = _input_bool(f"¿Es producido? (actual: {prod_actual['es_producido']}, default '{'s' if prod_actual['es_producido'] else 'n'}'): ", default=prod_actual['es_producido'])
        activo = _input_bool(f"¿Está activo? (actual: {prod_actual['activo']}, default '{'s' if prod_actual['activo'] else 'n'}'): ", default=prod_actual['activo'])
        if productos.actualizar_producto(
            id_producto=id_prod,
            nombre=nombre,
            unidad_id=unidad_id,
            id_familia=id_familia,
            codigo_softrestaurante=codigo_sr,
            es_producido=es_producido,
            es_vendido=es_vendido,
            activo=activo
        ):
            print(f"✅ Producto '{nombre}' (ID: {id_prod}) actualizado con éxito.")
        else:
            print("❌ Error: No se pudo actualizar el producto.")
    
    except ValueError:
        print("❌ Error: El ID debe ser un número.")
    except Exception as e:
        print(f"❌ Error fatal durante la edición: {e}")

def gestionar_productos_ui():
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
            _editar_producto_ui()
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
            factor = unidades_medida.obtener_factor_base(unidad_id)
            cantidad_base = cantidad * factor
            
            print(f"ℹ️  Se guardará {cantidad_base} {insumo_info['unidad_base_nombre']} (base).")
            
            ingredientes.append({
                'id_insumo': id_insumo,
                'cantidad': cantidad_base, 
                'unidad_id': unidades_medida.obtener_id_unidad_base(unidad_id)
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
    while True:
        print("\n--- 🍲 Gestión de Recetas ---")
        print("1. Ver todas las recetas")
        print("2. Crear nueva receta")
        print("3. Ver detalle de receta (Insumos)")
        print("4. Volver al menú principal")
        
        opcion = input("Seleccione una opción: ")
        if opcion == '1':
            print("\n--- 📜 Recetas Registradas ---")
            
            lista = recetas.obtener_todas_las_recetas_con_producto()
            if not lista: 
                print("ℹ️ No hay recetas registradas.")
                continue
            
            print("Formato: [ID Receta] | Producto Final -> (Nombre de la Receta)")
            pprint([f"[{r['id_receta']}] | {r['nombre_producto']} -> ({r['nombre']})" for r in lista])
            
            print("\nℹ️ Para ver los ingredientes (insumos), use la 'Opción 3'.")
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
                
        elif opcion == '3':
            print("\n--- ℹ️ Ver Detalle de Receta (Insumos) ---")
            try:
                id_rec = int(input("ID de la receta a consultar: "))
                detalle = recetas.obtener_receta_completa(id_rec)
                if not detalle:
                    print("❌ No se encontró la receta.")
                    continue
                
                print(f"\n--- Detalle Receta ID: {detalle['id_receta']} ---")
                print(f"Nombre: {detalle['nombre']}")
                print(f"Producto Final: {detalle['id_producto_final']}")
                print("Ingredientes (Insumos):")
                if not detalle['ingredientes']:
                    print("  (Esta receta no tiene ingredientes asignados)")
                else:
                    for ing in detalle['ingredientes']:
                        print(f"  - {ing['cantidad_estimada']} {ing['unidad']} de {ing['nombre']}")
            except ValueError:
                print("❌ Error: ID debe ser un número.")
            
        elif opcion == '4':
            break
        else:
            print("❌ Opción no válida.")

def main():
    while True:
        print("\n===== 🥗 ProteinTrack - Menú Principal 🥗 =====")
        print("--- OPERACIONES DIARIAS ---")
        print("1. 📂 Cargar Ventas desde Excel") 
        print("2. 🍳 Registrar Producción Simple (Helados, Cremas)")
        print("3. 🗑️ Registrar Merma (Desperdicio)")
        print("\n--- ADMINISTRACIÓN ---")
        print("4. 📦 Gestionar Catálogo de Productos")
        print("5. 🍲 Gestionar Recetas")
        print("6. Salir")
        
        opcion = input("Seleccione una opción: ")

        if opcion == '1':
            cargar_ventas_excel_ui()
        elif opcion == '2':
            registrar_produccion_simple_ui()
        elif opcion == '3':
            registrar_merma_ui()
        elif opcion == '4':
            gestionar_productos_ui()
        elif opcion == '5':
            gestionar_recetas_ui()
        elif opcion == '6':
            print("👋 ¡Hasta luego!")
            sys.exit(0)
        else:
            print("❌ Opción no válida. Intente de nuevo.")

if __name__ == "__main__":
    main()