const API_URL = "http://192.168.1.130:5000";
let todosLosProductos = []; 
let ordenActual = { columna: 'nombre', ascendente: true };

document.addEventListener("DOMContentLoaded", () => {
    cargarDropdowns();
    cargarProductos();

    // Event Listeners para el Buscador
    const buscador = document.getElementById("buscador");
    if(buscador) buscador.addEventListener("input", filtrarTabla);

    // Event Listeners para Botones de Ordenamiento
    const btnAz = document.getElementById("btn-sort-az");
    const btnStock = document.getElementById("btn-sort-stock");

    if(btnAz) {
        btnAz.addEventListener("click", () => {
            ordenarTabla('nombre');
            actualizarBotonesOrden(btnAz, btnStock);
        });
    }

    if(btnStock) {
        btnStock.addEventListener("click", () => {
            ordenarTabla('stock_convertido');
            actualizarBotonesOrden(btnStock, btnAz);
        });
    }
});

// --- CARGA DE DATOS ---
async function cargarProductos() {
    const tbody = document.getElementById("tabla-productos"); // ID corregido según tu HTML nuevo
    if(!tbody) return;
    
    tbody.innerHTML = "<tr><td colspan='6' style='text-align:center; padding:20px;'><i class='fas fa-spinner fa-spin'></i> Cargando catálogo...</td></tr>";

    try {
        const res = await fetch(`${API_URL}/api/productos`);
        if(!res.ok) throw new Error("Error en servidor");
        todosLosProductos = await res.json();
        
        // Orden por defecto al cargar
        ordenarTabla(ordenActual.columna, true); 
    } catch (e) {
        console.error(e);
        tbody.innerHTML = "<tr><td colspan='6' style='text-align:center; color:red;'>Error al cargar datos. Verifica la conexión.</td></tr>";
    }
}

// --- RENDERIZADO (VISUAL) ---
function renderizarTabla(lista) {
    const tbody = document.getElementById("tabla-productos");
    if(!tbody) return;
    tbody.innerHTML = "";

    if(lista.length === 0) {
        tbody.innerHTML = "<tr><td colspan='6' style='text-align:center; padding:20px; color:#777;'>No se encontraron productos.</td></tr>";
        return;
    }

    lista.forEach(p => {
        // Generar Badges (Etiquetas de colores)
        let badges = "";
        if (p.es_vendido) badges += `<span class="tag-config tag-vendido">Venta</span>`;
        if (p.es_producido) badges += `<span class="tag-config tag-receta">Receta</span>`;
        if (p.es_registrable_produccion) badges += `<span class="tag-config tag-registrable">Prod. Manual</span>`;

        const tr = document.createElement("tr");
        
        // IMPORTANTE: El orden de estos TD debe coincidir EXACTAMENTE con los TH del HTML
        // 1. Nombre, 2. Familia, 3. Unidad, 4. Stock, 5. Config, 6. Acciones
        tr.innerHTML = `
            <td>
                <strong>${p.nombre}</strong><br>
                <small style="color:#999;">${p.codigo_softrestaurant || ''}</small>
            </td>
            <td>${p.familia_nombre || '-'}</td>
            <td>${p.unidad_nombre || '-'}</td>
            <td><strong>${parseFloat(p.stock_convertido || 0).toFixed(2)}</strong></td>
            <td>${badges}</td>
            <td style="text-align: right;">
                <div class="action-buttons" style="justify-content: flex-end;">
                    <button class="btn-action btn-edit" onclick="abrirModalEditar(${p.id_producto})" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-action btn-delete" onclick="eliminarProducto(${p.id_producto})" title="Borrar">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function cargarDropdowns() {
    try {
        // Familias
        const resFam = await fetch(`${API_URL}/api/familias`);
        const familias = await resFam.json();
        const selFam = document.getElementById("prod-familia");
        // Limpiar y llenar
        selFam.innerHTML = ""; 
        familias.forEach(f => selFam.innerHTML += `<option value="${f.id_familia}">${f.nombre}</option>`);

        // Unidades
        const resUn = await fetch(`${API_URL}/api/unidades`);
        const unidades = await resUn.json();
        const selUn = document.getElementById("prod-unidad");
        selUn.innerHTML = "";
        unidades.forEach(u => selUn.innerHTML += `<option value="${u.id}">${u.nombre}</option>`);
    } catch(e) {
        console.error("Error cargando dropdowns", e);
    }
}

// --- FILTROS Y ORDEN ---
function filtrarTabla() {
    const input = document.getElementById("buscador");
    if(!input) return;
    const texto = input.value.toUpperCase();
    
    const filtrados = todosLosProductos.filter(p => 
        (p.nombre && p.nombre.toUpperCase().includes(texto)) || 
        (p.codigo_softrestaurant && p.codigo_softrestaurant.toString().includes(texto))
    );
    renderizarTabla(filtrados);
}

function ordenarTabla(columna, forzarRender = false) {
    // Si la columna es la misma, invertimos orden. Si es nueva, ascendente.
    if (!forzarRender) {
        if (ordenActual.columna === columna) {
            ordenActual.ascendente = !ordenActual.ascendente;
        } else {
            ordenActual.columna = columna;
            ordenActual.ascendente = true; 
        }
    }

    const factor = ordenActual.ascendente ? 1 : -1;

    todosLosProductos.sort((a, b) => {
        let valA = a[columna];
        let valB = b[columna];

        // Manejo de nulos
        if (valA == null) valA = "";
        if (valB == null) valB = "";

        // Si es número (Stock o ID)
        if (columna === 'stock_convertido' || columna === 'id_producto') {
            return (parseFloat(valA) - parseFloat(valB)) * factor;
        }

        // Si es texto
        valA = valA.toString().toLowerCase();
        valB = valB.toString().toLowerCase();
        if (valA < valB) return -1 * factor;
        if (valA > valB) return 1 * factor;
        return 0;
    });

    renderizarTabla(todosLosProductos);
}

// Función visual para cambiar color de botones de orden
function actualizarBotonesOrden(btnActivo, btnInactivo) {
    btnActivo.classList.add("active");
    btnInactivo.classList.remove("active");
}

// --- MODALES ---
const modal = document.getElementById("modal-producto");

// Corregido: Nombre debe coincidir con el HTML (abrirModalNueva)
function abrirModalNueva() {
    document.getElementById("modal-titulo").innerText = "Nuevo Producto";
    document.getElementById("prod-id").value = ""; 
    document.getElementById("prod-nombre").value = "";
    document.getElementById("prod-clave").value = "";
    
    // Resetear checks
    document.getElementById("check-vendido").checked = true;
    document.getElementById("check-producido").checked = false;
    document.getElementById("check-registrable").checked = false;

    modal.style.display = "flex"; // Flex para centrar con el nuevo CSS
}

function abrirModalEditar(id) {
    const prod = todosLosProductos.find(p => p.id_producto === id);
    if (!prod) return;

    document.getElementById("modal-titulo").innerText = "Editar Producto";
    document.getElementById("prod-id").value = prod.id_producto;
    document.getElementById("prod-nombre").value = prod.nombre;
    document.getElementById("prod-clave").value = prod.codigo_softrestaurant || "";
    
    // Seleccionar valores en dropdowns
    document.getElementById("prod-familia").value = prod.id_familia;
    document.getElementById("prod-unidad").value = prod.unidad_id; 

    // Checks
    document.getElementById("check-vendido").checked = prod.es_vendido;
    document.getElementById("check-producido").checked = prod.es_producido;
    document.getElementById("check-registrable").checked = prod.es_registrable_produccion;

    modal.style.display = "flex";
}

function cerrarModal() {
    modal.style.display = "none";
}

// --- GUARDAR Y ELIMINAR ---
async function guardarProducto() {
    const id = document.getElementById("prod-id").value;
    const esNuevo = !id;

    const datos = {
        nombre: document.getElementById("prod-nombre").value,
        codigo_softrestaurante: document.getElementById("prod-clave").value,
        id_familia: parseInt(document.getElementById("prod-familia").value),
        unidad_id: parseInt(document.getElementById("prod-unidad").value),
        es_vendido: document.getElementById("check-vendido").checked,
        es_producido: document.getElementById("check-producido").checked,
        es_registrable_produccion: document.getElementById("check-registrable").checked
    };

    if(!datos.nombre || !datos.id_familia || !datos.unidad_id) {
        alert("El nombre, la familia y la unidad son obligatorios.");
        return;
    }

    const url = esNuevo ? `${API_URL}/api/productos` : `${API_URL}/api/productos/${id}`;
    const method = esNuevo ? "POST" : "PUT";

    // Cambiar texto botón para feedback
    const btnSave = document.querySelector(".btn-save");
    const textoOriginal = btnSave.innerHTML;
    btnSave.innerHTML = "<i class='fas fa-spinner fa-spin'></i> Guardando...";
    btnSave.disabled = true;

    try {
        const res = await fetch(url, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos)
        });

        if(res.ok) {
            cerrarModal();
            cargarProductos(); 
        } else {
            const err = await res.json();
            alert("Error al guardar: " + (err.error || err.message));
        }
    } catch(e) {
        alert("Error de conexión: " + e);
    } finally {
        btnSave.innerHTML = textoOriginal;
        btnSave.disabled = false;
    }
}

async function eliminarProducto(id) {
    if(!confirm("¿Estás seguro de eliminar este producto?")) return;

    try {
        const res = await fetch(`${API_URL}/api/productos/${id}`, { method: 'DELETE' });
        if(res.ok) {
            cargarProductos();
        } else {
            alert("No se pudo eliminar el producto.");
        }
    } catch(e) { alert(e); }
}

// Cierre de modal al dar click fuera (Backup por si el HTML script falla)
window.onclick = function(event) {
    if (event.target == modal) cerrarModal();
}