document.addEventListener("DOMContentLoaded", () => {
    
    const API_URL = "http://127.0.0.1:5000";

    const productoSelect = document.getElementById("producto-select");
    const unidadSelect = document.getElementById("unidad-select");
    const cantidadInput = document.getElementById("cantidad-input");
    const obsInput = document.getElementById("obs-input");
    const guardarBtn = document.getElementById("guardar-btn");
    const mensajeDiv = document.getElementById("mensaje");

    let listaProductos = []; 

    async function cargarProductos() {
        try {
            const response = await fetch(`${API_URL}/api/productos`);
            
            if (!response.ok) {
                throw new Error("No se pudieron cargar los productos");
            }

            listaProductos = await response.json(); 
            
            productoSelect.innerHTML = "<option value=''>Seleccione un producto...</option>"; 

            listaProductos.forEach(producto => {
                const option = document.createElement("option");
                option.value = producto.id_producto;
                option.textContent = `${producto.nombre} (Stock: ${producto.stock_convertido} ${producto.unidad_nombre})`;
                option.setAttribute('data-unidad-id', producto.unidad_id);
                option.setAttribute('data-unidad-nombre', producto.unidad_nombre);
                productoSelect.appendChild(option);
            });

        } catch (error) {
            console.error("Error cargando productos:", error);
            productoSelect.innerHTML = "<option value=''>Error al cargar</option>";
        }
    }

    function actualizarUnidadPorDefecto() {
        const productoSeleccionado = productoSelect.options[productoSelect.selectedIndex];
        
        if (!productoSeleccionado.value) {
            unidadSelect.innerHTML = "<option value=''>Cargando unidades...</option>";
            return;
        }

        const unidadId = productoSeleccionado.getAttribute('data-unidad-id');
        const unidadNombre = productoSeleccionado.getAttribute('data-unidad-nombre');

        unidadSelect.innerHTML = `<option value="${unidadId}">${unidadNombre}</option>`;
    }

    async function registrarMerma() {

        const id_producto = productoSelect.value;
        const unidad_id = unidadSelect.value;
        const cantidad = cantidadInput.value;
        const observaciones = obsInput.value;

        if (!id_producto || !unidad_id || !cantidad) {
            mostrarMensaje("Por favor, complete todos los campos", "error");
            return;
        }

        const datosMerma = {
            id_producto: parseInt(id_producto),
            unidad_id: parseInt(unidad_id),
            cantidad: parseFloat(cantidad),
            observaciones: observaciones
        };

        try {
            const response = await fetch(`${API_URL}/api/registrar-merma`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(datosMerma),
            });

            const resultado = await response.json();

            if (!response.ok) {
                throw new Error(resultado.error || "Error desconocido");
            }
            
            mostrarMensaje(resultado.mensaje, "exito");

            cantidadInput.value = "";
            obsInput.value = "";

            cargarProductos();

        } catch (error) {
            console.error("Error al registrar merma:", error);
            mostrarMensaje(`Error: ${error.message}`, "error");
        }
    }

    function mostrarMensaje(texto, tipo) {
        mensajeDiv.textContent = texto;
        if (tipo === "exito") {
            mensajeDiv.className = "mensaje-exito";
        } else {
            mensajeDiv.className = "mensaje-error";
        }
        
        setTimeout(() => {
            mensajeDiv.textContent = "";
            mensajeDiv.className = "";
        }, 3000);
    }

    guardarBtn.addEventListener("click", registrarMerma);
    
    productoSelect.addEventListener("change", actualizarUnidadPorDefecto);

    cargarProductos();
    actualizarUnidadPorDefecto();
});