document.addEventListener("DOMContentLoaded", () => {

    const API_URL = "http://192.168.1.130:5000";

    const buscadorInput = document.getElementById("buscador-producto"); 
    const productoSelect = document.getElementById("producto-select");
    const unidadSelect = document.getElementById("unidad-select");
    const cantidadInput = document.getElementById("cantidad-input");
    const obsInput = document.getElementById("obs-input");
    const guardarBtn = document.getElementById("guardar-btn");
    const mensajeDiv = document.getElementById("mensaje");
    const fechaInput = document.getElementById("fecha-input");
    if(fechaInput) {
        fechaInput.valueAsDate = new Date();
    }

    let listaProductos = []; 

    async function cargarProductos() {
        try {
            const response = await fetch(`${API_URL}/api/productos`);
            if (!response.ok) throw new Error("Error al cargar productos");

            listaProductos = await response.json(); 
            
            renderizarOpciones(listaProductos);

        } catch (error) {
            console.error(error);
            productoSelect.innerHTML = "<option value=''>Error al cargar datos</option>";
        }
    }

    function renderizarOpciones(lista) {
        productoSelect.innerHTML = ""; 

        if (lista.length === 0) {
            productoSelect.innerHTML = "<option value=''>No se encontraron productos</option>";
            return;
        }

        lista.forEach(producto => {
            const option = document.createElement("option");
            option.value = producto.id_producto;
            
            const stock = parseFloat(producto.stock_convertido).toFixed(3);
            option.textContent = `${producto.nombre} (Stock: ${stock} ${producto.unidad_nombre})`;
            
            option.setAttribute('data-unidad-id', producto.unidad_id);
            option.setAttribute('data-unidad-nombre', producto.unidad_nombre);
            
            productoSelect.appendChild(option);
        });
    }

    buscadorInput.addEventListener("keyup", (e) => {
        const texto = e.target.value.toLowerCase();

        const filtrados = listaProductos.filter(p => 
            p.nombre.toLowerCase().includes(texto)
        );
        
        renderizarOpciones(filtrados);
        
        if (filtrados.length === 1) {
            productoSelect.selectedIndex = 0;
            actualizarUnidadPorDefecto();
        }
    });

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

    async function registrarMerma() {
        const id_producto = productoSelect.value;
        const unidad_id = unidadSelect.value;
        const cantidad = cantidadInput.value;
        const observaciones = obsInput.value;

        if (!id_producto || !unidad_id || !cantidad) {
            mostrarMensaje("Complete todos los campos", "error");
            return;
        }

        const datosMerma = {
            id_producto: parseInt(id_producto),
            unidad_id: parseInt(unidad_id),
            cantidad: parseFloat(cantidad),
            observaciones: observaciones,
            fecha: fechaInput.value
        };

        try {
            const response = await fetch(`${API_URL}/api/registrar-merma`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(datosMerma),
            });

            const resultado = await response.json();

            if (!response.ok) throw new Error(resultado.error || "Error desconocido");
            
            mostrarMensaje(resultado.mensaje, "exito");
            
            cantidadInput.value = "";
            obsInput.value = "";
            buscadorInput.value = ""; 

            cargarProductos(); 

        } catch (error) {
            mostrarMensaje(`Error: ${error.message}`, "error");
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

    guardarBtn.addEventListener("click", registrarMerma);
    productoSelect.addEventListener("change", actualizarUnidadPorDefecto);
    productoSelect.addEventListener("click", actualizarUnidadPorDefecto);

    cargarProductos();
});