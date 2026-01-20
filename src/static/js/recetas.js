const API_URL = ""; // Déjalo vacío si estás en el mismo servidor, o pon tu IP http://192.168.1.130:5000

let todasLasRecetas = [];
let insumosList = [];   // Todos los productos (para ser usados como ingredientes)
let productosList = []; // Solo productos "producidos/vendidos" (para ser producto final)
let unidadesList = [];
let ordenActual = { columna: 'nombre', ascendente: true };

document.addEventListener("DOMContentLoaded", () => {
    cargarDatosIniciales().then(() => {
        cargarRecetas();
    });

    // Filtros
    const buscador = document.getElementById("buscador");
    if(buscador) buscador.addEventListener("input", filtrarTabla);
    
    // Botones de Ordenamiento
    const btnNombre = document.getElementById("btn-sort-nombre");
    const btnProd = document.getElementById("btn-sort-prod");

    if(btnNombre) {
        btnNombre.addEventListener("click", () => {
            ordenarTabla('nombre');
            actualizarBotonesOrden(btnNombre, btnProd);
        });
    }

    if(btnProd) {
        btnProd.addEventListener("click", () => {
            ordenarTabla('nombre_producto_final_calculado'); 
            actualizarBotonesOrden(btnProd, btnNombre);
        });
    }
});

/* =========================================
   1. CARGA DE CATÁLOGOS
   ========================================= */
async function cargarDatosIniciales() {
    try {
        const [resProd, resUni] = await Promise.all([
            fetch(`${API_URL}/api/productos`),
            fetch(`${API_URL}/api/unidades`)
        ]);

        const todos = await resProd.json();
        unidadesList = await resUni.json();

        insumosList = todos; // Todo producto puede ser ingrediente
        productosList = todos.filter(p => p.es_producido || p.es_vendido); // Candidatos a producto final

        // Llenar Select del Modal (Producto Final)
        const selFinal = document.getElementById("receta-producto-final");
        if(selFinal) {
            selFinal.innerHTML = "<option value=''>-- Ninguno (Solo referencia) --</option>";
            productosList.forEach(p => {
                const opt = document.createElement("option");
                opt.value = p.id_producto;
                opt.textContent = p.nombre;
                selFinal.appendChild(opt);
            });
        }

    } catch(e) { console.error("Error cargando catálogos:", e); }
}

/* =========================================
   2. CARGA DE RECETAS (TABLA PRINCIPAL)
   ========================================= */
async function cargarRecetas() {
    const tbody = document.getElementById("tabla-body");
    tbody.innerHTML = "<tr><td colspan='4' style='text-align:center'>Cargando...</td></tr>";

    try {
        const res = await fetch(`${API_URL}/api/recetas`);
        const data = await res.json();
        
        // --- PROCESAMIENTO DE DATOS ---
        todasLasRecetas = data.map(r => {
            // Calculamos nombre del producto final
            let nombreFinal = "N/A";
            if(r.id_producto_final) {
                const prod = productosList.find(p => p.id_producto === r.id_producto_final);
                if(prod) nombreFinal = prod.nombre;
            } else if (r.nombre_producto) { // A veces viene del SQL directo
                nombreFinal = r.nombre_producto;
            }

            return {
                ...r,
                nombre_producto_final_calculado: nombreFinal
            };
        });

        ordenarTabla('nombre', true); // Renderiza por defecto

    } catch(e) {
        console.error(e);
        tbody.innerHTML = "<tr><td colspan='4' style='color:red; text-align:center'>Error de conexión</td></tr>";
    }
}

/* =========================================
   3. RENDERIZADO DE TABLA
   ========================================= */
function renderizarTabla(lista) {
    const tbody = document.getElementById("tabla-body");
    tbody.innerHTML = "";

    if (!lista || lista.length === 0) {
        tbody.innerHTML = "<tr><td colspan='4' style='text-align:center; padding:20px; color:#777;'>No hay recetas registradas.</td></tr>";
        return;
    }

    lista.forEach(r => {
        const tr = document.createElement("tr");

        // Nombre del Producto Final
        const nombreProducto = (r.nombre_producto_final_calculado && r.nombre_producto_final_calculado !== 'N/A')
            ? `<strong style="color:#2c3e50;">${r.nombre_producto_final_calculado}</strong>` 
            : `<span style="color:#ccc; font-style:italic;">- Sin vincular -</span>`;

        // Lista de Ingredientes (Viene del SQL como TEXTO concatenado)
        let htmlIngredientes = "";
        if (!r.lista_ingredientes || r.lista_ingredientes === 'Sin ingredientes') {
            htmlIngredientes = '<span style="color:#ccc;">Sin ingredientes definidos</span>';
        } else {
            htmlIngredientes = `<div style="font-size:0.85em; color:#555; line-height:1.4;">${r.lista_ingredientes}</div>`;
        }

        tr.innerHTML = `
            <td>
                <div style="font-weight:600; font-size:1.05em;">${r.nombre}</div>
            </td>
            <td>${nombreProducto}</td>
            <td>${htmlIngredientes}</td>
            <td style="text-align: right; white-space: nowrap;">
                <button onclick="abrirModalEditar(${r.id_receta})" class="btn-action" style="background:#3498db; color:white; border:none; border-radius:4px; padding:6px 10px; cursor:pointer; margin-right:5px;" title="Editar">
                    <i class="fas fa-edit"></i>
                </button>
                <button onclick="eliminarReceta(${r.id_receta})" class="btn-action" style="background:#e74c3c; color:white; border:none; border-radius:4px; padding:6px 10px; cursor:pointer;" title="Borrar">
                    <i class="fas fa-trash-alt"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

/* =========================================
   4. ORDENAMIENTO Y FILTROS
   ========================================= */
function ordenarTabla(columna, forzarRender = false) {
    if (!forzarRender) {
        if (ordenActual.columna === columna) ordenActual.ascendente = !ordenActual.ascendente;
        else { ordenActual.columna = columna; ordenActual.ascendente = true; }
    }
    const factor = ordenActual.ascendente ? 1 : -1;
    todasLasRecetas.sort((a, b) => {
        let valA = (a[columna] || "").toString().toLowerCase();
        let valB = (b[columna] || "").toString().toLowerCase();
        if (valA < valB) return -1 * factor;
        if (valA > valB) return 1 * factor;
        return 0;
    });
    renderizarTabla(todasLasRecetas);
}

function filtrarTabla() {
    const texto = document.getElementById("buscador").value.toLowerCase();
    const filtrados = todasLasRecetas.filter(r => 
        r.nombre.toLowerCase().includes(texto) || 
        r.nombre_producto_final_calculado.toLowerCase().includes(texto) ||
        (r.lista_ingredientes && r.lista_ingredientes.toLowerCase().includes(texto))
    );
    renderizarTabla(filtrados);
}

function actualizarBotonesOrden(activo, inactivo) {
    if(activo) activo.classList.add("active");
    if(inactivo) inactivo.classList.remove("active");
}

/* =========================================
   5. GESTIÓN DEL MODAL (CREAR / EDITAR)
   ========================================= */
function abrirModalNueva() {
    document.getElementById("modal-titulo").innerText = "Nueva Receta";
    // IMPORTANTE: Asegúrate que en tu HTML los IDs sean "receta-id", "receta-nombre", etc.
    // Si usabas "receta-id-hidden", cámbialo aquí o en el HTML. Usaremos "receta-id" según tu código.
    document.getElementById("receta-id").value = "";
    document.getElementById("receta-nombre").value = "";
    document.getElementById("receta-producto-final").value = "";
    document.getElementById("lista-ingredientes").innerHTML = "";
    
    agregarFilaIngrediente(); // Fila vacía inicial
    document.getElementById("modal-receta").style.display = "flex";
}

async function abrirModalEditar(id) {
    document.getElementById("modal-receta").style.display = "flex";
    document.getElementById("modal-titulo").innerText = "Cargando...";
    document.getElementById("lista-ingredientes").innerHTML = ""; 

    let recetaFull = null;

    try {
        // Obtenemos el detalle completo (ingredientes incluidos)
        const res = await fetch(`${API_URL}/api/recetas/${id}`);
        if(res.ok) {
            recetaFull = await res.json();
        } else {
            // Fallback (solo si la API falla)
            recetaFull = todasLasRecetas.find(r => r.id_receta === id);
        }
    } catch(e) {
        console.error("Error fetching detail:", e);
        recetaFull = todasLasRecetas.find(r => r.id_receta === id);
    }

    if(!recetaFull) { alert("No se pudo cargar la receta"); cerrarModal(); return; }

    // Llenar formulario cabecera
    document.getElementById("modal-titulo").innerText = "Editar Receta";
    document.getElementById("receta-id").value = recetaFull.id_receta;
    document.getElementById("receta-nombre").value = recetaFull.nombre;
    document.getElementById("receta-producto-final").value = recetaFull.id_producto_final || "";

    // Llenar filas de ingredientes
    const tbody = document.getElementById("lista-ingredientes");
    tbody.innerHTML = "";

    if (recetaFull.ingredientes && recetaFull.ingredientes.length > 0) {
        recetaFull.ingredientes.forEach(ing => {
            // CORRECCIÓN: El backend manda 'cantidad_estimada', el fallback 'cantidad'
            const cantidad = ing.cantidad_estimada || ing.cantidad || 0;
            agregarFilaIngrediente(ing.id_insumo, cantidad);
        });
    } else {
        agregarFilaIngrediente(); 
    }
}

function agregarFilaIngrediente(idInsumoPre = null, cantidadPre = null) {
    const tbody = document.getElementById("lista-ingredientes");
    const tr = document.createElement("tr");

    let options = `<option value="">Seleccionar...</option>`;
    insumosList.forEach(p => {
        const sel = (idInsumoPre && p.id_producto == idInsumoPre) ? "selected" : "";
        options += `<option value="${p.id_producto}" ${sel}>${p.nombre}</option>`;
    });

    tr.innerHTML = `
        <td>
            <select class="form-control-modal insumo-select" onchange="actualizarUnidadRow(this)">${options}</select>
        </td>
        <td>
            <input type="number" class="form-control-modal cantidad-input" step="0.001" value="${cantidadPre || ''}" placeholder="0.00">
        </td>
        <td style="text-align:center; padding-top:10px;">
            <span class="unidad-texto" style="font-size:0.85rem; color:#666; font-weight:bold;">-</span>
        </td>
        <td style="text-align:center;">
            <button type="button" class="btn-remove" onclick="this.closest('tr').remove()" style="color:red; background:none; border:none; cursor:pointer; font-size:1.2rem;">&times;</button>
        </td>
    `;
    tbody.appendChild(tr);

    // Si precargamos un insumo, calculamos su unidad inmediatamente
    if(idInsumoPre) {
        const select = tr.querySelector(".insumo-select");
        actualizarUnidadRow(select);
    }
}

function actualizarUnidadRow(select) {
    const tr = select.closest("tr");
    const idProd = select.value;
    const span = tr.querySelector(".unidad-texto");
    
    if(!idProd) { span.innerText = "-"; return; }

    const prod = insumosList.find(p => p.id_producto == idProd);
    if(prod) {
        // Buscamos la unidad por 'unidad' (FK) o 'unidad_id'
        const idUnidadBuscada = prod.unidad || prod.unidad_id;
        const u = unidadesList.find(x => x.id == idUnidadBuscada);
        span.innerText = u ? u.nombre : "u";
    }
}

/* =========================================
   6. GUARDAR (CREATE / UPDATE)
   ========================================= */
async function guardarReceta() {
    const id = document.getElementById("receta-id").value;
    const nombre = document.getElementById("receta-nombre").value;
    const idProdFinal = document.getElementById("receta-producto-final").value;

    if (!nombre) { alert("El nombre es obligatorio"); return; }

    // Recolectar datos de la tabla
    const filas = document.querySelectorAll("#lista-ingredientes tr");
    let ingredientes = [];

    filas.forEach(tr => {
        const sel = tr.querySelector(".insumo-select");
        const cant = tr.querySelector(".cantidad-input");
        if(sel && sel.value && cant.value) {
            const prod = insumosList.find(p => p.id_producto == sel.value);
            ingredientes.push({
                id_insumo: parseInt(sel.value),
                cantidad: parseFloat(cant.value),
                unidad_id: prod ? (prod.unidad || prod.unidad_id) : null 
            });
        }
    });

    const datos = {
        nombre: nombre,
        id_producto_final: idProdFinal ? parseInt(idProdFinal) : null,
        ingredientes: ingredientes
    };

    const url = id ? `${API_URL}/api/recetas/${id}` : `${API_URL}/api/recetas`;
    const method = id ? "PUT" : "POST";

    const btn = document.querySelector(".btn-save-modal");
    const originalText = btn.innerText;
    btn.innerText = "Guardando..."; btn.disabled = true;

    try {
        const res = await fetch(url, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos)
        });

        if(res.ok) {
            cerrarModal();
            cargarRecetas(); // Recargar tabla principal
        } else {
            const err = await res.json();
            alert("Error: " + (err.error || err.message || "Error desconocido"));
        }
    } catch(e) {
        alert("Error de red: " + e);
    } finally {
        btn.innerText = originalText; btn.disabled = false;
    }
}

/* =========================================
   7. FUNCIONES AUXILIARES FALTANTES
   ========================================= */
function cerrarModal() {
    document.getElementById("modal-receta").style.display = "none";
}

async function eliminarReceta(id) {
    if(!confirm("¿Estás seguro de que deseas eliminar esta receta? Esta acción no se puede deshacer.")) return;

    try {
        const res = await fetch(`${API_URL}/api/recetas/${id}`, {
            method: 'DELETE'
        });
        
        if(res.ok) {
            cargarRecetas();
        } else {
            const err = await res.json();
            alert("Error al eliminar: " + (err.error || "Desconocido"));
        }
    } catch(e) {
        console.error(e);
        alert("Error de conexión al intentar eliminar.");
    }
}

// Hacemos accesibles las funciones al HTML global
window.abrirModalEditar = abrirModalEditar;
window.eliminarReceta = eliminarReceta;
window.guardarReceta = guardarReceta;
window.agregarFilaIngrediente = agregarFilaIngrediente;
window.actualizarUnidadRow = actualizarUnidadRow;
window.abrirModalNueva = abrirModalNueva;
window.cerrarModal = cerrarModal;