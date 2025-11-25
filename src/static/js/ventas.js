document.addEventListener("DOMContentLoaded", () => {
    
    const API_URL = "";
    const fileInput = document.getElementById("file-input");
    const uploadBtn = document.getElementById("upload-btn");
    const mensajeDiv = document.getElementById("mensaje");
    const fechaInput = document.getElementById("fecha-venta-input");
    const crearProductoContainer = document.getElementById("crear-producto-container");
    const errorDetalle = document.getElementById("error-detalle");
    const claveInput = document.getElementById("clave-input");
    const nombreInput = document.getElementById("nombre-input");
    const familiaSelect = document.getElementById("familia-select");
    const unidadSelect = document.getElementById("unidad-select");
    const crearBtn = document.getElementById("crear-btn");
    const checkTieneReceta = document.getElementById("check-tiene-receta");
    const seccionIngredientes = document.getElementById("seccion-ingredientes");
    const btnAddIng = document.getElementById("btn-add-ing");
    const listaIngredientes = document.getElementById("lista-ingredientes");

    let archivoExcel;
    let filaDeError = 1; 
    let totalVentasProcesadas = 0;
    let insumosList = []; 
    let unidadesList = [];

    if(fechaInput) {
        fechaInput.valueAsDate = new Date();
    }

    async function loadDropdowns() {
        try {
            const resFam = await fetch(`${API_URL}/api/familias`);
            const familias = await resFam.json();
            familiaSelect.innerHTML = "<option value=''>Seleccione familia...</option>";
            familias.forEach(f => {
                const option = document.createElement("option");
                option.value = f.id_familia;
                option.textContent = f.nombre;
                familiaSelect.appendChild(option);
            });

            const resUn = await fetch(`${API_URL}/api/unidades`);
            unidadesList = await resUn.json();
            
            unidadSelect.innerHTML = "<option value=''>Seleccione unidad...</option>";
            unidadesList.forEach(u => {
                const option = document.createElement("option");
                option.value = u.id;
                option.textContent = u.nombre;
                unidadSelect.appendChild(option);
            });

            const resProd = await fetch(`${API_URL}/api/productos`);
            const todosProductos = await resProd.json();
            insumosList = todosProductos.filter(p => p.es_registrable_produccion);

        } catch (e) {
            console.error("Error cargando catalogos:", e);
            mostrarMensaje("Error cargando catálogos iniciales.", "error");
        }
    }

    async function handleUpload(fila_inicio = 1) {
        if (fila_inicio === 1) {
            totalVentasProcesadas = 0;
            archivoExcel = fileInput.files[0];
            if (!archivoExcel) {
                mostrarMensaje("Por favor, seleccione un archivo", "error");
                return;
            }
        }
        const fechaSeleccionada = fechaInput.value;
        if (!fechaSeleccionada) {
             mostrarMensaje("Por favor, seleccione la fecha de las ventas", "error");
             return;
        }

        const formData = new FormData();
        formData.append("file", archivoExcel);
        formData.append("fila_inicio", fila_inicio);
        formData.append("fecha_venta", fechaSeleccionada);
        mostrarMensaje(`Cargando y procesando archivo (desde fila ${fila_inicio})...`, "info");
        uploadBtn.disabled = true;

        try {
            const response = await fetch(`${API_URL}/api/upload-ventas`, {
                method: "POST",
                body: formData, 
            });
            const resultado = await response.json();
            
            if (resultado.filas_procesadas_exitosamente) {
                totalVentasProcesadas += resultado.filas_procesadas_exitosamente;
            }
            
            if (resultado.exito) {
                mostrarMensaje(`¡Éxito! Total de ${totalVentasProcesadas} ventas procesadas.`, "exito");
                fileInput.value = ""; 
                filaDeError = 1; 
                totalVentasProcesadas = 0;
                ocultarFormularioCreacion();
            
            } else if (resultado.error === "Producto no encontrado") {
                filaDeError = resultado.fila_excel;
                mostrarMensaje(`Fallo en Fila ${filaDeError}: ${resultado.error}. (Acumulado: ${totalVentasProcesadas} OK)`, "error");
                mostrarFormularioCreacion(resultado);
            
            } else {
                throw new Error(resultado.error || "Error desconocido en el servidor");
            }

        } catch (error) {
            mostrarMensaje(`Error de red o subida: ${error.message}`, "error");
        } finally {
            uploadBtn.disabled = false;
        }
    }
    function mostrarFormularioCreacion(errorData) {

        errorDetalle.textContent = `CLAVE: ${errorData.clave_faltante} (${errorData.nombre_producto})`;
        claveInput.value = errorData.clave_faltante;
        nombreInput.value = errorData.nombre_producto;

        const optFamilia = [...familiaSelect.options].find(o => o.text === errorData.familia_grupo);
        if (optFamilia) familiaSelect.value = optFamilia.value;
        else familiaSelect.value = "";

        checkTieneReceta.checked = false;
        seccionIngredientes.style.display = "none";
        listaIngredientes.innerHTML = "";
        
        crearProductoContainer.style.display = "block";
    }

    function ocultarFormularioCreacion() {
        crearProductoContainer.style.display = "none";
    }

    checkTieneReceta.addEventListener("change", () => {
        if (checkTieneReceta.checked) {
            seccionIngredientes.style.display = "block";
            if (listaIngredientes.children.length === 0) agregarFilaIngrediente();
        } else {
            seccionIngredientes.style.display = "none";
        }
    });

    btnAddIng.addEventListener("click", agregarFilaIngrediente);

    function agregarFilaIngrediente() {
        const rowId = Date.now();
        
        let optsProd = "<option value=''>Insumo...</option>";
        insumosList.forEach(p => optsProd += `<option value="${p.id_producto}">${p.nombre}</option>`);
        
        let optsUnit = "<option value=''>Unidad...</option>";
        unidadesList.forEach(u => optsUnit += `<option value="${u.id}">${u.nombre}</option>`);

        const tr = document.createElement("tr");
        tr.id = `row-${rowId}`;
        tr.innerHTML = `
            <td><select class="ing-insumo" style="width:100%">${optsProd}</select></td>
            <td><input type="number" class="ing-cant" style="width:60px" step="0.01"></td>
            <td><select class="ing-unidad" style="width:100%">${optsUnit}</select></td>
            <td><button onclick="document.getElementById('row-${rowId}').remove()" style="background:#d9534f;color:white;border:none;">X</button></td>
        `;
        listaIngredientes.appendChild(tr);
    }

    async function handleCrearProducto() {
        const tieneReceta = checkTieneReceta.checked;

        const datosProducto = {
            nombre: nombreInput.value,
            codigo_softrestaurante: claveInput.value,
            id_familia: parseInt(familiaSelect.value),
            unidad_id: parseInt(unidadSelect.value),
            es_vendido: true, 
            es_producido: tieneReceta, 
            es_registrable_produccion: false 
        };

        if (!datosProducto.id_familia || !datosProducto.unidad_id) {
            alert("Seleccione Familia y Unidad del producto.");
            return;
        }

        let ingredientes = [];
        if (tieneReceta) {
            const filas = listaIngredientes.querySelectorAll("tr");
            filas.forEach(tr => {
                const idIns = tr.querySelector(".ing-insumo").value;
                const cant = tr.querySelector(".ing-cant").value;
                const idUni = tr.querySelector(".ing-unidad").value;
                if (idIns && cant && idUni) {
                    ingredientes.push({
                        id_insumo: parseInt(idIns),
                        cantidad: parseFloat(cant),
                        unidad_id: parseInt(idUni)
                    });
                }
            });
            if (ingredientes.length === 0) {
                alert("Si marca 'Tiene Receta', debe agregar al menos un ingrediente válido.");
                return;
            }
        }

        crearBtn.disabled = true;
        mostrarMensaje("Guardando producto...", "info");

        try {
            const resProd = await fetch(`${API_URL}/api/productos`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(datosProducto)
            });
            const dataProd = await resProd.json();
            if (!resProd.ok) throw new Error(dataProd.error || "Error creando producto");

            const nuevoIdProducto = dataProd.id_producto;

            if (tieneReceta) {
                mostrarMensaje("Guardando receta...", "info");
                const datosReceta = {
                    id_producto_final: nuevoIdProducto,
                    nombre: "Receta - " + datosProducto.nombre,
                    ingredientes: ingredientes
                };
                
                const resReceta = await fetch(`${API_URL}/api/recetas`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(datosReceta)
                });
                if (!resReceta.ok) {
                    console.error("Error creando receta:", await resReceta.json());
                    alert("El producto se creó, pero hubo un error guardando la receta. Por favor verifique en 'Gestionar Recetas'.");
                }
            }

            mostrarMensaje(`Producto creado. Reintentando carga desde fila ${filaDeError}...`, "info");
            ocultarFormularioCreacion();
            
            crearBtn.disabled = false;
            handleUpload(filaDeError); 

        } catch (error) {
            crearBtn.disabled = false;
            mostrarMensaje(`Error: ${error.message}`, "error");
        }
    }

    function mostrarMensaje(texto, tipo) {
        mensajeDiv.textContent = texto;
        mensajeDiv.className = `mensaje-${tipo}`;
    }

    uploadBtn.addEventListener("click", () => handleUpload(1));
    crearBtn.addEventListener("click", handleCrearProducto);

    loadDropdowns();
});