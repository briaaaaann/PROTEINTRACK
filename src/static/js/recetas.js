const API_URL = "";
let productosList = [];
let unidadesList = [];
let todasLasRecetas = []; 
let ordenActual = { columna: null, ascendente: true };

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
    tbody.innerHTML = "<tr><td colspan='4' style='text-align:center'>Cargando...</td></tr>";

    try {
        const res = await fetch(`${API_URL}/api/recetas`);
        todasLasRecetas = await res.json(); 
        renderizarTabla(todasLasRecetas);   
    } catch(e) {
        tbody.innerHTML = "<tr><td colspan='4' style='text-align:center'>Error al cargar recetas</td></tr>";
    }
}

function renderizarTabla(lista) {
    const tbody = document.getElementById("tabla-body");
    tbody.innerHTML = "";

    if(lista.length === 0) {
        tbody.innerHTML = "<tr><td colspan='4' style='text-align:center'>No hay recetas registradas.</td></tr>";
        return;
    }

    lista.forEach(r => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${r.id_receta}</td>
            <td><b>${r.nombre_producto}</b></td>
            <td>${r.nombre}</td>
            <td>
                <button class="btn-edit" onclick="abrirModalEditar(${r.id_receta})">✏️</button>
                <button class="btn-delete" onclick="eliminarReceta(${r.id_receta})">🗑️</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

const modal = document.getElementById("modal-receta");

function abrirModalNueva() {
    document.getElementById("modal-titulo").textContent = "Nueva Receta";
    document.getElementById("receta-id").value = ""; 
    
    document.getElementById("receta-producto-final").value = "";
    document.getElementById("receta-nombre").value = "";
    document.getElementById("lista-ingredientes").innerHTML = ""; 
    agregarFilaIngrediente(); 
    modal.style.display = "block";
}

async function abrirModalEditar(idReceta) {
    document.getElementById("modal-titulo").textContent = "Editar Receta";
    document.getElementById("receta-id").value = idReceta; 
    
    try {
        const res = await fetch(`${API_URL}/api/recetas/${idReceta}`);
        const receta = await res.json();

        document.getElementById("receta-producto-final").value = receta.id_producto_final;
        document.getElementById("receta-nombre").value = receta.nombre;

        const tbody = document.getElementById("lista-ingredientes");
        tbody.innerHTML = "";

        if (receta.ingredientes && receta.ingredientes.length > 0) {
            receta.ingredientes.forEach(ing => {
                agregarFilaIngrediente(ing.id_insumo, ing.cantidad, ing.unidad_id);
            });
        } else {
            agregarFilaIngrediente();
        }

        modal.style.display = "block";

    } catch (e) {
        alert("Error al cargar detalles de la receta: " + e);
    }
}

function cerrarModal() { modal.style.display = "none"; }

function agregarFilaIngrediente(idInsumo = null, cantidad = null, idUnidad = null) {
    const tbody = document.getElementById("lista-ingredientes");
    const rowId = Date.now() + Math.random(); 

    let optionsProd = "<option value=''>Seleccione Insumo...</option>";
    productosList.forEach(p => {
        if (p.es_registrable_produccion) {
            const selected = (p.id_producto === idInsumo) ? "selected" : "";
            optionsProd += `<option value="${p.id_producto}" ${selected}>${p.nombre}</option>`;
        }
    });

    let optionsUnit = "<option value=''>Unidad...</option>";
    unidadesList.forEach(u => {
        const selected = (u.id === idUnidad) ? "selected" : "";
        optionsUnit += `<option value="${u.id}" ${selected}>${u.nombre}</option>`;
    });

    const valCantidad = cantidad !== null ? cantidad : "";

    const tr = document.createElement("tr");
    tr.id = `row-${rowId}`;
    tr.innerHTML = `
        <td><select class="input-insumo" style="width:100%">${optionsProd}</select></td>
        <td><input type="number" class="input-cantidad" value="${valCantidad}" step="0.01" placeholder="0.00"></td>
        <td><select class="input-unidad" style="width:100%">${optionsUnit}</select></td>
        <td><button class="btn-remove-ing" onclick="eliminarFila('${rowId}')" style="background:#d9534f;color:white;border:none;padding:5px;">X</button></td>
    `;
    tbody.appendChild(tr);
}

function eliminarFila(rowId) {
    document.getElementById(`row-${rowId}`).remove();
}

async function guardarReceta() {
    const idReceta = document.getElementById("receta-id").value;
    const esEdicion = !!idReceta; 
    const idProdFinal = document.getElementById("receta-producto-final").value;
    const nombreReceta = document.getElementById("receta-nombre").value;

    if(!idProdFinal || !nombreReceta) {
        alert("Faltan datos principales.");
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

    const url = esEdicion ? `${API_URL}/api/recetas/${idReceta}` : `${API_URL}/api/recetas`;
    const method = esEdicion ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(datos)
        });

        if(res.ok) {
            alert(esEdicion ? "✅ Receta actualizada" : "✅ Receta creada");
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

function ordenarTabla(columna) {

    if (ordenActual.columna === columna) {
        ordenActual.ascendente = !ordenActual.ascendente;
    } else {
        ordenActual.columna = columna;
        ordenActual.ascendente = true;
    }

    const factor = ordenActual.ascendente ? 1 : -1;

    todasLasRecetas.sort((a, b) => {
        let valA = a[columna];
        let valB = b[columna];
        if (valA == null) valA = "";
        if (valB == null) valB = "";
        if (columna === 'id_receta') {
            return (parseFloat(valA) - parseFloat(valB)) * factor;
        }
        if (typeof valA === 'string') {
            valA = valA.toLowerCase();
            valB = valB.toLowerCase();
            if (valA < valB) return -1 * factor;
            if (valA > valB) return 1 * factor;
            return 0;
        }
        return 0;
    });
    renderizarTabla(todasLasRecetas);
}

window.onclick = function(event) {
    if (event.target == modal) cerrarModal();
}