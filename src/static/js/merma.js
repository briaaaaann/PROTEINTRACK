document.addEventListener("DOMContentLoaded", () => {

    const API_URL = ""; 

    // Referencias DOM
    const buscadorInput = document.getElementById("producto-buscador");
    const listaResultados = document.getElementById("lista-resultados");
    const productoIdHidden = document.getElementById("producto-id-hidden");
    
    const unidadSelect = document.getElementById("unidad-select");
    const cantidadInput = document.getElementById("cantidad-input");
    const obsInput = document.getElementById("obs-input");
    const guardarBtn = document.getElementById("guardar-btn");
    const mensajeDiv = document.getElementById("mensaje");
    const fechaInput = document.getElementById("fecha-input");

    if(fechaInput) fechaInput.valueAsDate = new Date();

    let todosLosProductos = []; // Base de datos local en memoria

    // 1. Cargar productos al inicio
    async function cargarProductos() {
        try {
            const res = await fetch(`${API_URL}/api/productos`);
            if(res.ok) {
                todosLosProductos = await res.json();
            }
        } catch (error) {
            console.error("Error cargando productos:", error);
        }
    }

    // 2. Lógica del Buscador (Evento Input)
    buscadorInput.addEventListener('input', function() {
        const texto = this.value.toLowerCase();
        listaResultados.innerHTML = ''; // Limpiar lista anterior
        productoIdHidden.value = ''; // Resetear ID si el usuario modifica el texto

        if (texto.length === 0) {
            listaResultados.classList.remove('mostrar');
            return;
        }

        // Filtrar productos
        const coincidencias = todosLosProductos.filter(prod => 
            prod.nombre.toLowerCase().includes(texto)
        );

        if (coincidencias.length > 0) {
            listaResultados.classList.add('mostrar');
            
            coincidencias.forEach(prod => {
                const div = document.createElement('div');
                div.classList.add('item-resultado');
                // Resaltar la parte coincidente (opcional, visualmente agradable)
                div.innerHTML = prod.nombre; 
                
                div.addEventListener('click', () => {
                    seleccionarProducto(prod);
                });
                
                listaResultados.appendChild(div);
            });
        } else {
            listaResultados.classList.remove('mostrar');
        }
    });

    // 3. Seleccionar Producto
    function seleccionarProducto(prod) {
        buscadorInput.value = prod.nombre; // Poner nombre en el input visual
        productoIdHidden.value = prod.id_producto; // Guardar ID oculto
        listaResultados.classList.remove('mostrar'); // Ocultar lista
        
        // Cargar unidades
        cargarUnidades(prod.unidad || prod.unidad_id);
    }

    // 4. Cerrar lista si clicamos fuera
    document.addEventListener('click', (e) => {
        if (!buscadorInput.contains(e.target) && !listaResultados.contains(e.target)) {
            listaResultados.classList.remove('mostrar');
        }
    });

    // 5. Cargar Unidades
    async function cargarUnidades(unidadPreseleccionadaId) {
        try {
            const res = await fetch(`${API_URL}/api/unidades`);
            if(res.ok) {
                const unidades = await res.json();
                unidadSelect.innerHTML = "";
                unidades.forEach(u => {
                    const opt = document.createElement("option");
                    opt.value = u.id;
                    opt.textContent = u.nombre;
                    if(u.id == unidadPreseleccionadaId) opt.selected = true;
                    unidadSelect.appendChild(opt);
                });
            }
        } catch(e) { console.error(e); }
    }

    // 6. Registrar Merma
    async function registrarMerma() {
        const idProducto = productoIdHidden.value;
        const idUnidad = unidadSelect.value;
        const cantidad = cantidadInput.value;
        const obs = obsInput.value;

        if (!idProducto) {
            mostrarMensaje("⚠️ Selecciona un producto de la lista desplegable.", "error");
            return;
        }
        if (!cantidad || parseFloat(cantidad) <= 0) {
            mostrarMensaje("⚠️ Cantidad inválida.", "error");
            return;
        }

        guardarBtn.disabled = true;
        
        try {
            const datos = {
                id_producto: parseInt(idProducto),
                unidad_id: parseInt(idUnidad),
                cantidad: parseFloat(cantidad),
                observaciones: obs,
                fecha: fechaInput.value
            };

            const res = await fetch(`${API_URL}/api/registrar-merma`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(datos)
            });

            const data = await res.json();
            
            if(res.ok) {
                mostrarMensaje(data.mensaje, "exito");
                // Limpiar todo
                buscadorInput.value = "";
                productoIdHidden.value = "";
                cantidadInput.value = "";
                obsInput.value = "";
                unidadSelect.innerHTML = "<option>...</option>";
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            mostrarMensaje(error.message, "error");
        } finally {
            guardarBtn.disabled = false;
        }
    }

    function mostrarMensaje(texto, tipo) {
        mensajeDiv.textContent = texto;
        mensajeDiv.className = (tipo === "exito") ? "mensaje-exito" : "mensaje-error";
        setTimeout(() => { mensajeDiv.textContent = ""; mensajeDiv.className = ""; }, 3000);
    }

    guardarBtn.addEventListener("click", registrarMerma);
    cargarProductos();
});