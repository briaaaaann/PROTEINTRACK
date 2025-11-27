import sys
import os
from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from decimal import Decimal

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
try:
    from . import logica_negocio
    from . import productos
    from . import recetas
    from . import unidades_medida
    from . import familias
    from . import historial
except ImportError:
    print("❌ Error: No se pudieron importar los módulos locales. Asegúrate de correr con 'python -m src.app'")
    import logica_negocio
    import productos
    import recetas
    import unidades_medida
    from . import familias
    from . import historial

app = Flask(__name__)
current_dir = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(current_dir, 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CORS(app) 

@app.route('/')
def pagina_principal():
    return render_template('index.html')

@app.route('/merma')
def pagina_registrar_merma():
    return render_template('merma.html')

@app.route('/produccion')
def pagina_registrar_produccion():
    return render_template('produccion.html') 

@app.route('/ventas')
def pagina_cargar_ventas():
    return render_template('ventas.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/api/test', methods=['GET'])
def test_route():
    return jsonify({"mensaje": "¡El servidor Flask está funcionando!"})

@app.route('/api/productos', methods=['GET'])
def get_todos_los_productos():
    try:
        lista_productos = productos.obtener_todos_los_productos(solo_activos=True)
        return jsonify(lista_productos), 200
    except Exception as e:
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@app.route('/api/produccion-simple', methods=['POST'])
def api_registrar_produccion_simple():
    try:
        datos = request.json
        if not datos or 'id_producto' not in datos or 'cantidad' not in datos or 'unidad_id' not in datos:
            return jsonify({"error": "Datos incompletos. Se requiere 'id_producto', 'cantidad', y 'unidad_id'."}), 400

        exito = logica_negocio.registrar_produccion_simple(
            id_producto=int(datos['id_producto']),
            cantidad=float(datos['cantidad']),
            unidad_id=int(datos['unidad_id']),
            unidad_nombre=datos.get('unidad_nombre', 'unidades') 
        )

        if exito:
            return jsonify({"mensaje": "Producción registrada con éxito"}), 201
        else:
            return jsonify({"error": "Fallo al registrar la producción en la lógica de negocio"}), 400

    except ValueError:
        return jsonify({"error": "Error de tipo de dato. 'id_producto' y 'unidad_id' deben ser enteros, 'cantidad' debe ser un número."}), 400
    except Exception as e:
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
    
@app.route('/api/registrar-merma', methods=['POST'])
def api_registrar_merma():
    print("Recibida petición POST en /api/registrar-merma")
    try:
        datos = request.json
        if not datos or 'id_producto' not in datos or 'cantidad' not in datos or 'unidad_id' not in datos:
            return jsonify({"error": "Datos incompletos. Se requiere 'id_producto', 'cantidad' y 'unidad_id'."}), 400
        print(f"Datos recibidos: {datos}")
        exito = logica_negocio.registrar_merma_logica(
            id_producto=int(datos['id_producto']), 
            cantidad=float(datos['cantidad']),
            unidad_id=int(datos['unidad_id']),
            observaciones=datos.get('observaciones', None)
        )
        if exito:
            return jsonify({"mensaje": "Merma registrada con éxito"}), 201
        else:
            return jsonify({"error": "Fallo al registrar la merma en la lógica de negocio"}), 400

    except ValueError:
        return jsonify({"error": "Error de tipo de dato. IDs deben ser enteros, cantidad debe ser un número."}), 400
    except Exception as e:
        print(f"ERROR en /api/registrar-merma: {e}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
        
@app.route('/api/productos', methods=['POST'])
def api_crear_producto():
    print("Recibida petición POST en /api/productos")
    try:
        datos = request.json
        
        nuevo_prod = productos.crear_producto(
            nombre=datos['nombre'],
            unidad_id=int(datos['unidad_id']),
            id_familia=int(datos['id_familia']),
            stock_inicial=float(datos.get('stock_inicial', 0)),
            codigo_softrestaurante=datos.get('codigo_softrestaurante', None),
            es_producido=bool(datos.get('es_producido', False)),
            es_vendido=bool(datos.get('es_vendido', True)),
            activo=True,
            es_registrable_produccion=bool(datos.get('es_registrable_produccion', False))
        )
        
        if nuevo_prod:
            return jsonify(nuevo_prod), 201
        else:
            return jsonify({"error": "No se pudo crear el producto"}), 400
            
    except Exception as e:
        print(f"ERROR en POST /api/productos: {e}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
    
@app.route('/api/productos/<int:id_producto>', methods=['PUT'])
def api_editar_producto(id_producto):
    print(f"Recibida petición PUT en /api/productos/{id_producto}")
    try:
        datos = request.json
        
        exito = productos.actualizar_producto(
            id_producto=id_producto,
            nombre=datos['nombre'],
            unidad_id=int(datos['unidad_id']),
            id_familia=int(datos['id_familia']),
            codigo_softrestaurante=datos.get('codigo_softrestaurante', None),
            es_producido=bool(datos.get('es_producido', False)),
            es_vendido=bool(datos.get('es_vendido', True)),
            activo=bool(datos.get('activo', True)),
            es_registrable_produccion=bool(datos.get('es_registrable_produccion', False))
        )
        
        if exito:
            return jsonify({"mensaje": f"Producto {id_producto} actualizado"}), 200
        else:
            return jsonify({"error": f"No se pudo actualizar el producto {id_producto}"}), 400

    except Exception as e:
        print(f"ERROR en PUT /api/productos/{id_producto}: {e}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@app.route('/api/productos/<int:id_producto>', methods=['DELETE'])
def api_desactivar_producto(id_producto):
    print(f"Recibida petición DELETE en /api/productos/{id_producto}")
    try:
        exito = productos.desactivar_producto(id_producto)
        
        if exito:
            return jsonify({"mensaje": f"Producto {id_producto} desactivado"}), 200
        else:
            return jsonify({"error": f"No se pudo desactivar el producto {id_producto}"}), 400

    except Exception as e:
        print(f"ERROR en DELETE /api/productos/{id_producto}: {e}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@app.route('/api/upload-ventas', methods=['POST'])
def api_upload_ventas_excel():
    if 'file' not in request.files:
        return jsonify({"exito": False, "error": "No se encontró la parte del archivo ('file')"}), 400
    
    file = request.files['file']
    fila_inicio = int(request.form.get('fila_inicio', 1))
    fecha_venta_str = request.form.get('fecha_venta') 
    
    if file.filename == '':
        return jsonify({"exito": False, "error": "No se seleccionó ningún archivo"}), 400

    if file:
        try:
            filename = secure_filename(file.filename)
            ruta_guardada = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            if fila_inicio == 1:
                file.save(ruta_guardada)
            
            resultado = logica_negocio.procesar_ventas_excel(ruta_guardada, fila_inicio, fecha_venta_str)
            
            if resultado["exito"]:
                os.remove(ruta_guardada)

            return jsonify(resultado), 200 

        except Exception as e:
            return jsonify({"exito": False, "error": f"Error interno: {str(e)}"}), 500
        
@app.route('/api/recetas', methods=['GET'])
def api_get_todas_las_recetas():
    print("Recibida petición GET en /api/recetas")
    try:
        lista = recetas.obtener_todas_las_recetas_con_producto()
        return jsonify(lista), 200
    except Exception as e:
        print(f"ERROR en GET /api/recetas: {e}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@app.route('/api/recetas/<int:id_receta>', methods=['GET'])
def api_get_detalle_receta(id_receta):
    print(f"Recibida petición GET en /api/recetas/{id_receta}")
    try:
        detalle = recetas.obtener_receta_completa(id_receta)
        if detalle:
            return jsonify(detalle), 200
        else:
            return jsonify({"error": f"No se encontró la receta con ID {id_receta}"}), 404
    except Exception as e:
        print(f"ERROR en GET /api/recetas/{id_receta}: {e}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@app.route('/api/recetas', methods=['POST'])
def api_crear_receta():
    print("Recibida petición POST en /api/recetas")
    try:
        datos = request.json      
        if not datos or 'id_producto_final' not in datos or 'nombre' not in datos or 'ingredientes' not in datos:
            return jsonify({"error": "Datos incompletos. Se requiere 'id_producto_final', 'nombre' y 'ingredientes'."}), 400
        nueva_receta = recetas.crear_receta(
            id_producto_final=int(datos['id_producto_final']),
            nombre=datos['nombre'],
            ingredientes=datos['ingredientes'] 
        )
        
        if nueva_receta:
            return jsonify(nueva_receta), 201
        else:
            return jsonify({"error": "No se pudo crear la receta"}), 400

    except Exception as e:
        print(f"ERROR en POST /api/recetas: {e}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@app.route('/api/recetas/<int:id_receta>', methods=['PUT'])
def api_editar_receta(id_receta):
    try:
        datos = request.json
        exito = recetas.actualizar_receta(
            id_receta=id_receta,
            id_producto_final=int(datos['id_producto_final']),
            nombre=datos['nombre'],
            ingredientes=datos['ingredientes']
        )
        if exito:
            return jsonify({"mensaje": "Receta actualizada"}), 200
        else:
            return jsonify({"error": "No se pudo actualizar"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recetas/<int:id_receta>', methods=['DELETE'])
def api_eliminar_receta(id_receta):
    print(f"Recibida petición DELETE en /api/recetas/{id_receta}")
    try:
        exito = recetas.eliminar_receta(id_receta)
        if exito:
            return jsonify({"mensaje": f"Receta {id_receta} eliminada"}), 200
        else:
            return jsonify({"error": f"No se pudo eliminar la receta {id_receta} (o no existía)"}), 400
    except Exception as e:
        print(f"ERROR en DELETE /api/recetas/{id_receta}: {e}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@app.route('/api/familias', methods=['GET'])
def api_get_familias():
    try:
        lista = familias.obtener_todas_las_familias()
        return jsonify(lista), 200
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@app.route('/api/unidades', methods=['GET'])
def api_get_unidades():
    try:
        lista = unidades_medida.obtener_todas_las_unidades()
        return jsonify(lista), 200
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@app.route('/historial')
def pagina_historial():
    return render_template('historial.html')

@app.route('/api/historial/generar', methods=['POST'])
def api_generar_snapshot():
    try:
        resultado = historial.generar_snapshot_diario()
        return jsonify(resultado), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/historial/<string:fecha>', methods=['GET'])
def api_ver_historial(fecha):
    try:
        datos = historial.obtener_historial_por_fecha(fecha)
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/productos')
def pagina_gestion_productos():
    return render_template('productos.html')

@app.route('/recetas')
def pagina_gestion_recetas():
    return render_template('recetas.html')

@app.route('/inventario-actual')
def pagina_inventario_actual():
    return render_template('inventario_actual.html')

def main():
    print("🚀 Iniciando servidor Flask en http://192.168.1.130:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main()