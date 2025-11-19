const API_URL = "http://192.168.1.130:5000";
let productosList = []; 
let unidadesList = [];

document.addEventListener("DOMContentLoaded", () => {
    cargarDatosIniciales();
    cargarRecetas();
});

async function cargarDatosIniciales() {
    const resProd = await fetch(`${API_URL}/api/productos`);
    productosList = await resProd.json();

    const resUni = await fetch(`${API_URL}/api/unidades`);
    unidadesList = await resUni.json();

    const selFinal = document.getElementById("receta-producto-final");
    selFinal.innerHTML = "<option value=''>Seleccione...</option>";
    
    productosList.forEach(p => {
        if (p.es_producido || p.es_registrable_produccion) {
            const opt = document.createElement("option");
            opt.value = p.id_producto;
            opt.textContent = p.nombre;
            selFinal.appendChild(opt);
        }
    });
}

async function cargarRecetas() {
    const tbody = document.getElementById("tabla-body");
    tbody.innerHTML = "<tr><td colspan='4'>Cargando...</td></tr>";

    try {
        const res = await fetch(`${API_URL}/api/recetas`);
        const recetas = await res.json();
        
        tbody.innerHTML = "";
        if(recetas.length === 0) tbody.innerHTML = "<tr><td colspan='4'>No hay recetas registradas.</td></tr>";

        recetas.forEach(r => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${r.id_receta}</td>
                <td><b>${r.nombre_producto}</b></td>
                <td>${r.nombre}</td>
                <td>
                    <button class="btn-delete" onclick="eliminarReceta(${r.id_receta})">🗑️</button>
                    </td>
            `;
            tbody.appendChild(tr);
        });
    } catch(e) {
        tbody.innerHTML = "<tr><td colspan='4'>Error al cargar recetas</td></tr>";
    }
}

const modal = document.getElementById("modal-receta");

function abrirModalNueva() {
    document.getElementById("receta-producto-final").value = "";
    document.getElementById("receta-nombre").value = "";
    document.getElementById("lista-ingredientes").innerHTML = ""; 
    agregarFilaIngrediente(); 
    modal.style.display = "block";
}

function cerrarModal() { modal.style.display = "none"; }

function agregarFilaIngrediente() {
    const tbody = document.getElementById("lista-ingredientes");
    const rowId = Date.now(); 
    let optionsProd = "<option value=''>Seleccione Insumo...</option>";
    productosList.forEach(p => {
        if (p.es_registrable_produccion) {
            optionsProd += `<option value="${p.id_producto}">${p.nombre}</option>`;
        }
    });

    let optionsUnit = "<option value=''>Unidad...</option>";
    unidadesList.forEach(u => {
        optionsUnit += `<option value="${u.id}">${u.nombre}</option>`;
    });

    const tr = document.createElement("tr");
    tr.id = `row-${rowId}`;
    tr.innerHTML = `
        <td><select class="input-insumo">${optionsProd}</select></td>
        <td><input type="number" class="input-cantidad" step="0.01" placeholder="0.00"></td>
        <td><select class="input-unidad">${optionsUnit}</select></td>
        <td><button class="btn-remove-ing" onclick="eliminarFila('${rowId}')">X</button></td>
    `;
    tbody.appendChild(tr);
}

function eliminarFila(rowId) {
    document.getElementById(`row-${rowId}`).remove();
}

async function guardarReceta() {
    const idProdFinal = document.getElementById("receta-producto-final").value;
    const nombreReceta = document.getElementById("receta-nombre").value;

    if(!idProdFinal || !nombreReceta) {
        alert("Seleccione un producto final y asigne un nombre a la receta.");
        return;
    }

    const filas = document.querySelectorAll("#lista-ingredientes tr");
    let ingredientes = [];

    for (let tr of filas) {
        const idInsumo = tr.querySelector(".input-insumo").value;
        const cantidad = tr.querySelector(".input-cantidad").value;
        const idUnidad = tr.querySelector(".input-unidad").value;

        if (idInsumo && cantidad && idUnidad) {
            ingredientes.push({
                id_insumo: parseInt(idInsumo),
                cantidad: parseFloat(cantidad),
                unidad_id: parseInt(idUnidad)
            });
        }
    }

    if(ingredientes.length === 0) {
        alert("Debe agregar al menos un ingrediente válido.");
        return;
    }

    const datos = {
        id_producto_final: parseInt(idProdFinal),
        nombre: nombreReceta,
        ingredientes: ingredientes
    };

    try {
        const res = await fetch(`${API_URL}/api/recetas`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos)
        });

        if(res.ok) {
            alert("✅ Receta creada con éxito");
            cerrarModal();
            cargarRecetas();
        } else {
            const err = await res.json();
            alert("Error: " + err.error);
        }
    } catch(e) {
        alert("Error de red: " + e);
    }
}

async function eliminarReceta(id) {
    if(!confirm("¿Seguro que deseas eliminar esta receta?")) return;
    try {
        const res = await fetch(`${API_URL}/api/recetas/${id}`, { method: 'DELETE' });
        if(res.ok) cargarRecetas();
        else alert("Error al eliminar");
    } catch(e) { alert(e); }
}

window.onclick = function(event) {
    if (event.target == modal) cerrarModal();
}