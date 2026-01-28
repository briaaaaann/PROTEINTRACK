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
    const progressContainer = document.getElementById("progress-container");
    const progressBar = document.getElementById("progress-bar");
    const progressText = document.getElementById("progress-text");

    let progressInterval;
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

    async function handleUpload(filaInicio = 1) {
        if (!fileInput.files[0]) {
            mostrarMensaje("Selecciona un archivo primero", "error");
            return;
        }

        const formData = new FormData();
        formData.append("file", fileInput.files[0]);
        
        if (fechaInput && fechaInput.value) {
            // CORRECCIÓN: Usar el nombre exacto que espera app.py
            formData.append("fecha_venta", fechaInput.value); 
        }

        mostrarMensaje("", "");
        uploadBtn.disabled = true;
        
        // --- ANIMACIÓN BARRA ---
        progressContainer.style.display = "block";
        progressBar.style.width = "0%";
        progressBar.textContent = "0%";
        progressText.textContent = "Analizando archivo...";
        
        let width = 0;
        clearInterval(progressInterval);
        progressInterval = setInterval(() => {
            if (width >= 90) clearInterval(progressInterval);
            else {
                width += Math.random() * 5;
                if(width > 90) width = 90;
                progressBar.style.width = width + "%";
                progressBar.textContent = Math.round(width) + "%";
            }
        }, 400);

        try {
            const res = await fetch(`${API_URL}/api/upload-ventas?fila_inicio=${filaInicio}`, {
                method: "POST",
                body: formData
            });

            const data = await res.json();

            // Finalizar barra
            clearInterval(progressInterval);
            progressBar.style.width = "100%";
            progressBar.textContent = "100%";
            progressText.textContent = "Procesado.";
            setTimeout(() => { progressContainer.style.display = "none"; }, 1000);

            // --- CORRECCIÓN CRÍTICA AQUÍ ---
            // No dependemos del status HTTP (200, 400, 404), sino de la lógica interna (data.exito)
            
            if (data.exito) {
                // CASO DE ÉXITO REAL
                mostrarMensaje(`✅ Éxito: ${data.mensaje || "Carga completa"}`, "exito");
                uploadBtn.disabled = false;
                
            } else {
                // CASO DE ERROR (Lógico o de Servidor)
                uploadBtn.disabled = false;

                // Verificamos si el error es porque falta un producto
                if (data.producto_faltante) {
                    mostrarMensaje(`⚠️ ${data.error}`, "error");
                    
                    // Llenar datos para el modal
                    errorDetalle.textContent = `Fila Excel: ${data.fila}. Clave no encontrada: "${data.producto_faltante}"`;
                    filaDeError = data.fila; 
                    
                    claveInput.value = data.producto_faltante;
                    nombreInput.value = data.descripcion_sugerida || "";
                    
                    // Abrir modal
                    crearProductoContainer.style.display = "block";
                    crearProductoContainer.scrollIntoView({ behavior: "smooth" });
                    
                } else {
                    // Otros errores (fecha duplicada, archivo corrupto, etc.)
                    mostrarMensaje(`❌ Error: ${data.error || "Error desconocido"}`, "error");
                }
            }

        } catch (error) {
            clearInterval(progressInterval);
            progressContainer.style.display = "none";
            console.error(error);
            mostrarMensaje("❌ Error de conexión o respuesta inválida del servidor", "error");
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