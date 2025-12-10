document.addEventListener("DOMContentLoaded", () => {
    
    const API_URL = "";
    const productoSelect = document.getElementById("producto-select");
    const unidadSelect = document.getElementById("unidad-select");
    const cantidadInput = document.getElementById("cantidad-input");
    const guardarBtn = document.getElementById("guardar-btn");
    const mensajeDiv = document.getElementById("mensaje");
    const fechaInput = document.getElementById("fecha-input");
    if(fechaInput) {
        fechaInput.valueAsDate = new Date();
    }

    let listaProductos = [];
    let ultimoClick = 0; 

    async function cargarProductos() {
        try {
            if(listaProductos.length > 0) return;

            const response = await fetch(`${API_URL}/api/productos`);
            if (!response.ok) throw new Error("No se pudieron cargar los productos");
            
            listaProductos = await response.json();
            productoSelect.innerHTML = "<option value=''>Seleccione un producto...</option>";
            
            listaProductos.forEach(producto => {
                if (producto.es_registrable_produccion) {
                    const option = document.createElement("option");
                    option.value = producto.id_producto;
                    const stockFormateado = parseFloat(producto.stock_convertido).toFixed(3);
                    option.textContent = `${producto.nombre} (Stock: ${stockFormateado} ${producto.unidad_nombre})`;
                    option.setAttribute('data-unidad-id', producto.unidad_id);
                    option.setAttribute('data-unidad-nombre', producto.unidad_nombre);
                    productoSelect.appendChild(option);
                }
            });

        } catch (error) {
            console.error("Error cargando productos:", error);
            productoSelect.innerHTML = "<option value=''>Error al cargar</option>";
        }
    }

    function actualizarUnidadPorDefecto() {
        const productoSeleccionado = productoSelect.options[productoSelect.selectedIndex];
        if (!productoSeleccionado || !productoSeleccionado.value) {
            unidadSelect.innerHTML = "<option value=''>...</option>";
            return;
        }
        const unidadId = productoSeleccionado.getAttribute('data-unidad-id');
        const unidadNombre = productoSeleccionado.getAttribute('data-unidad-nombre');
        unidadSelect.innerHTML = `<option value="${unidadId}">${unidadNombre}</option>`;
    }
    async function registrarProduccion(e) {
        if(e) e.preventDefault();
        if(e) e.stopPropagation(); 
        const ahora = Date.now();
        if (ahora - ultimoClick < 2000) {
            console.warn("🚫 Doble clic bloqueado por JS.");
            return; 
        }
        ultimoClick = ahora;

        const id_producto = productoSelect.value;
        const unidad_id = unidadSelect.value;
        const cantidad = cantidadInput.value;
        
        if (!id_producto || !unidad_id || !cantidad) {
            mostrarMensaje("Complete todos los campos", "error");
            return;
        }

        const optionSelected = productoSelect.options[productoSelect.selectedIndex];
        const unidad_nombre = optionSelected ? optionSelected.getAttribute('data-unidad-nombre') : '';
        guardarBtn.disabled = true;
        guardarBtn.textContent = "Guardando...";

        const datosProduccion = {
            id_producto: parseInt(id_producto),
            unidad_id: parseInt(unidad_id),
            cantidad: parseFloat(cantidad),
            unidad_nombre: unidad_nombre,
            fecha: fechaInput.value
        };

        try {
            const response = await fetch(`${API_URL}/api/produccion-simple`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(datosProduccion),
            });

            const resultado = await response.json();

            if (!response.ok) throw new Error(resultado.error || "Error desconocido");
            
            mostrarMensaje(resultado.mensaje, "exito");
            cantidadInput.value = "";
            listaProductos = []; 
            cargarProductos(); 

        } catch (error) {
            console.error(error);
            mostrarMensaje(`Error: ${error.message}`, "error");
        } finally {
            guardarBtn.disabled = false;
            guardarBtn.textContent = "Registrar Producción";
        }
    }

    function mostrarMensaje(texto, tipo) {
        mensajeDiv.textContent = texto;
        mensajeDiv.className = (tipo === "exito") ? "mensaje-exito" : "mensaje-error";
        setTimeout(() => {
            mensajeDiv.textContent = "";
            mensajeDiv.className = "";
        }, 3000);
    }
    guardarBtn.onclick = registrarProduccion;
    productoSelect.onchange = actualizarUnidadPorDefecto;
    cargarProductos();
});