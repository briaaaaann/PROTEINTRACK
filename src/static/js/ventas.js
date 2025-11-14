document.addEventListener("DOMContentLoaded", () => {
    
    const API_URL = "http://127.0.0.1:5000";
    const fileInput = document.getElementById("file-input");
    const uploadBtn = document.getElementById("upload-btn");
    const mensajeDiv = document.getElementById("mensaje");
    const crearProductoContainer = document.getElementById("crear-producto-container");
    const errorDetalle = document.getElementById("error-detalle");
    const claveInput = document.getElementById("clave-input");
    const nombreInput = document.getElementById("nombre-input");
    const familiaSelect = document.getElementById("familia-select");
    const unidadSelect = document.getElementById("unidad-select");
    const crearBtn = document.getElementById("crear-btn");

    let archivoExcel;
    let filaDeError = 1; 
    let totalVentasProcesadas = 0; 
    async function loadDropdowns() {
        try {
            const resFam = await fetch(`${API_URL}/api/familias`);
            const familias = await resFam.json();
            familiaSelect.innerHTML = "<option value=''>Seleccione una familia...</option>";
            familias.forEach(f => {
                const option = document.createElement("option");
                option.value = f.id_familia;
                option.textContent = f.nombre;
                familiaSelect.appendChild(option);
            });
        } catch (e) { /* ... */ }
        try {
            const resUn = await fetch(`${API_URL}/api/unidades`);
            const unidades = await resUn.json();
            unidadSelect.innerHTML = "<option value=''>Seleccione una unidad...</option>";
            unidades.forEach(u => {
                const option = document.createElement("option");
                option.value = u.id;
                option.textContent = u.nombre;
                unidadSelect.appendChild(option);
            });
        } catch (e) { /* ... */ }
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

        const formData = new FormData();
        formData.append("file", archivoExcel);
        formData.append("fila_inicio", fila_inicio);

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
                mostrarMensaje(`Fallo en Fila ${filaDeError}: ${resultado.error}. (Total acumulado: ${totalVentasProcesadas} ventas OK)`, "error");
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
        const familiaNombre = errorData.familia_grupo;
        const optFamilia = [...familiaSelect.options].find(o => o.text === familiaNombre);
        if (optFamilia) {
            familiaSelect.value = optFamilia.value;
        }
        crearProductoContainer.style.display = "block";
    }

    function ocultarFormularioCreacion() {
        crearProductoContainer.style.display = "none";
    }

    async function handleCrearProducto() {
        const datosProducto = {
            nombre: nombreInput.value,
            codigo_softrestaurante: claveInput.value,
            id_familia: parseInt(familiaSelect.value),
            unidad_id: parseInt(unidadSelect.value),
            es_vendido: true, 
            es_producido: false, 
            es_registrable_produccion: false
        };
        if (!datosProducto.id_familia || !datosProducto.unidad_id) {
            alert("Por favor, seleccione una Familia y una Unidad");
            return;
        }

        try {
            const response = await fetch(`${API_URL}/api/productos`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(datosProducto)
            });

            const resultado = await response.json();
            if (!response.ok) throw new Error(resultado.error || "Error al crear producto");

            mostrarMensaje(`Producto ${datosProducto.nombre} (ID: ${resultado.id_producto}) creado.`, "exito");
            ocultarFormularioCreacion();
            mostrarMensaje(`Producto creado. Reintentando carga desde la fila ${filaDeError}... (Total acumulado: ${totalVentasProcesadas} ventas)`, "info");
            handleUpload(filaDeError); 

        } catch (error) {
            mostrarMensaje(`Error al crear producto: ${error.message}`, "error");
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