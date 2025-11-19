const API_URL = "http://127.0.0.1:5000";
let todosLosProductos = []; 

document.addEventListener("DOMContentLoaded", () => {
    cargarDropdowns();
    cargarProductos();
});

async function cargarProductos() {
    const tbody = document.getElementById("tabla-body");
    tbody.innerHTML = "<tr><td colspan='7' style='text-align:center'>Cargando...</td></tr>";

    try {
        const res = await fetch(`${API_URL}/api/productos`);
        todosLosProductos = await res.json();
        renderizarTabla(todosLosProductos);
    } catch (e) {
        tbody.innerHTML = "<tr><td colspan='7' style='text-align:center'>Error al cargar datos</td></tr>";
    }
}

function renderizarTabla(lista) {
    const tbody = document.getElementById("tabla-body");
    tbody.innerHTML = "";

    lista.forEach(p => {
        let badges = "";
        if (p.es_producido) badges += `<span class="badge badge-prod">Receta</span>`;
        if (p.es_registrable_produccion) badges += `<span class="badge badge-reg">Producción</span>`;

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${p.id_producto}</td>
            <td><b>${p.nombre}</b> <br> <span style="color:#777; font-size:0.8em">Clave: ${p.codigo_softrestaurant || '--'}</span></td>
            <td>${p.familia_nombre}</td>
            <td>${p.unidad_nombre}</td>
            <td>${parseFloat(p.stock_convertido).toFixed(2)}</td>
            <td>${badges}</td>
            <td>
                <button class="btn-edit" onclick="abrirModalEditar(${p.id_producto})">✏️</button>
                <button class="btn-delete" onclick="eliminarProducto(${p.id_producto})">🗑️</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function cargarDropdowns() {
    const resFam = await fetch(`${API_URL}/api/familias`);
    const familias = await resFam.json();
    const selFam = document.getElementById("prod-familia");
    familias.forEach(f => selFam.innerHTML += `<option value="${f.id_familia}">${f.nombre}</option>`);

    const resUn = await fetch(`${API_URL}/api/unidades`);
    const unidades = await resUn.json();
    const selUn = document.getElementById("prod-unidad");
    unidades.forEach(u => selUn.innerHTML += `<option value="${u.id}">${u.nombre}</option>`);
}

function filtrarTabla() {
    const texto = document.getElementById("buscador").value.toUpperCase();
    const filtrados = todosLosProductos.filter(p => 
        p.nombre.includes(texto) || 
        (p.codigo_softrestaurant && p.codigo_softrestaurant.toString().includes(texto))
    );
    renderizarTabla(filtrados);
}

const modal = document.getElementById("modal-producto");

function cerrarModal() { modal.style.display = "none"; }

function abrirModalNuevo() {
    document.getElementById("modal-titulo").textContent = "Nuevo Producto";
    document.getElementById("prod-id").value = ""; 
    document.getElementById("prod-nombre").value = "";
    document.getElementById("prod-clave").value = "";
    document.getElementById("check-vendido").checked = true;
    document.getElementById("check-producido").checked = false;
    document.getElementById("check-registrable").checked = false;

    modal.style.display = "block";
}

function abrirModalEditar(id) {
    const prod = todosLosProductos.find(p => p.id_producto === id);
    if (!prod) return;

    document.getElementById("modal-titulo").textContent = "Editar Producto: " + id;
    document.getElementById("prod-id").value = prod.id_producto;
    document.getElementById("prod-nombre").value = prod.nombre;
    document.getElementById("prod-clave").value = prod.codigo_softrestaurant || "";
    document.getElementById("prod-familia").value = prod.id_familia;
    document.getElementById("prod-unidad").value = prod.unidad_id; 

    document.getElementById("check-vendido").checked = prod.es_vendido;
    document.getElementById("check-producido").checked = prod.es_producido;
    document.getElementById("check-registrable").checked = prod.es_registrable_produccion;

    modal.style.display = "block";
}

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
        alert("Nombre, Familia y Unidad son obligatorios.");
        return;
    }

    const url = esNuevo ? `${API_URL}/api/productos` : `${API_URL}/api/productos/${id}`;
    const method = esNuevo ? "POST" : "PUT";

    try {
        const res = await fetch(url, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos)
        });

        if(res.ok) {
            alert("Producto guardado correctamente.");
            cerrarModal();
            cargarProductos(); 
        } else {
            const err = await res.json();
            alert("Error: " + err.error);
        }
    } catch(e) {
        alert("Error de red: " + e);
    }
}

async function eliminarProducto(id) {
    if(!confirm("¿Seguro que deseas desactivar este producto? Desaparecerá de las listas.")) return;

    try {
        const res = await fetch(`${API_URL}/api/productos/${id}`, { method: 'DELETE' });
        if(res.ok) {
            cargarProductos();
        } else {
            alert("No se pudo eliminar.");
        }
    } catch(e) { alert(e); }
}

window.onclick = function(event) {
    if (event.target == modal) cerrarModal();
}