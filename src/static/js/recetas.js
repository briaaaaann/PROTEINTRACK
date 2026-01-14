const API_URL = "http://192.168.1.130:5000"; 

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
    document.getElementById("buscador").addEventListener("input", filtrarTabla);
    
    // Botones de Ordenamiento (YA FUNCIONALES)
    const btnNombre = document.getElementById("btn-sort-nombre");
    const btnProd = document.getElementById("btn-sort-prod");

    btnNombre.addEventListener("click", () => {
        ordenarTabla('nombre');
        actualizarBotonesOrden(btnNombre, btnProd);
    });

    btnProd.addEventListener("click", () => {
        ordenarTabla('nombre_producto_final_calculado'); // Usamos el nombre calculado
        actualizarBotonesOrden(btnProd, btnNombre);
    });
});

// 1. CARGA DE CATALOGOS (Espera a que termine antes de cargar recetas)
async function cargarDatosIniciales() {
    try {
        const [resProd, resUni] = await Promise.all([
            fetch(`${API_URL}/api/productos`),
            fetch(`${API_URL}/api/unidades`)
        ]);

        const todos = await resProd.json();
        unidadesList = await resUni.json();

        insumosList = todos; // Todo puede ser ingrediente
        productosList = todos.filter(p => p.es_producido || p.es_vendido); // Candidatos a producto final

        // Llenar Select del Modal
        const selFinal = document.getElementById("receta-producto-final");
        selFinal.innerHTML = "<option value=''>-- Ninguno (Solo referencia) --</option>";
        productosList.forEach(p => {
            const opt = document.createElement("option");
            opt.value = p.id_producto;
            opt.textContent = p.nombre;
            selFinal.appendChild(opt);
        });

    } catch(e) { console.error("Error cargando catálogos:", e); }
}

// 2. CARGA DE RECETAS
async function cargarRecetas() {
    const tbody = document.getElementById("tabla-body");
    tbody.innerHTML = "<tr><td colspan='4' style='text-align:center'>Cargando...</td></tr>";

    try {
        const res = await fetch(`${API_URL}/api/recetas`);
        const data = await res.json();
        
        // --- PROCESAMIENTO DE DATOS (Arregla columnas vacías) ---
        todasLasRecetas = data.map(r => {
            // Buscamos el nombre del producto final usando el ID, ya que la API no siempre lo manda
            let nombreFinal = "N/A";
            if(r.id_producto_final) {
                const prod = productosList.find(p => p.id_producto === r.id_producto_final);
                if(prod) nombreFinal = prod.nombre;
            } else if (r.producto_final_nombre) {
                nombreFinal = r.producto_final_nombre;
            }

            return {
                ...r,
                nombre_producto_final_calculado: nombreFinal // Propiedad auxiliar para ordenar y mostrar
            };
        });

        ordenarTabla('nombre', true); // Renderiza por defecto

    } catch(e) {
        console.error(e);
        tbody.innerHTML = "<tr><td colspan='4' style='color:red; text-align:center'>Error de conexión</td></tr>";
    }
}

// 3. RENDERIZADO
function renderizarTabla(lista) {
    const tbody = document.getElementById("tabla-body");
    tbody.innerHTML = "";

    if (lista.length === 0) {
        tbody.innerHTML = "<tr><td colspan='4' style='text-align:center; padding:20px; color:#777;'>No hay recetas.</td></tr>";
        return;
    }

    lista.forEach(r => {
        const tr = document.createElement("tr");

        // Columna Ingredientes: Si viene vacío, mostramos "Ver detalle"
        let textoIngredientes = '<span style="color:#999; font-style:italic;">Ver detalle</span>';
        if (r.ingredientes && r.ingredientes.length > 0) {
            textoIngredientes = `<span style="background:#e8f8f5; color:#27ae60; padding:2px 8px; border-radius:10px; font-weight:bold;">${r.ingredientes.length} insumos</span>`;
        }

        const nombreFinalDisplay = r.nombre_producto_final_calculado !== "N/A" 
            ? `<strong>${r.nombre_producto_final_calculado}</strong>` 
            : `<span style="color:#ccc;">- Sin asignar -</span>`;

        tr.innerHTML = `
            <td>${r.nombre}</td>
            <td>${nombreFinalDisplay}</td>
            <td style="text-align:center;">${textoIngredientes}</td>
            <td style="text-align: right;">
                <button onclick="abrirModalEditar(${r.id_receta})" style="background:#3498db; color:white; border:none; border-radius:4px; padding:5px 10px; cursor:pointer;" title="Editar"><i class="fas fa-edit"></i></button>
                <button onclick="eliminarReceta(${r.id_receta})" style="background:#e74c3c; color:white; border:none; border-radius:4px; padding:5px 10px; cursor:pointer; margin-left:5px;" title="Borrar"><i class="fas fa-trash-alt"></i></button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// 4. FUNCIONES DE ORDENAMIENTO
function ordenarTabla(columna, forzarRender = false) {
    if (!forzarRender) {
        if (ordenActual.columna === columna) ordenActual.ascendente = !ordenActual.ascendente;
        else { ordenActual.columna = columna; ordenActual.ascendente = true; }
    }

    const factor = ordenActual.ascendente ? 1 : -1;

    todasLasRecetas.sort((a, b) => {
        let valA = a[columna] || "";
        let valB = b[columna] || "";
        
        valA = valA.toString().toLowerCase();
        valB = valB.toString().toLowerCase();

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
        r.nombre_producto_final_calculado.toLowerCase().includes(texto)
    );
    renderizarTabla(filtrados);
}

function actualizarBotonesOrden(activo, inactivo) {
    activo.classList.add("active");
    inactivo.classList.remove("active");
}

// 5. GESTIÓN DEL MODAL (Aquí está la corrección para EDITAR)
function abrirModalNueva() {
    document.getElementById("modal-titulo").innerText = "Nueva Receta";
    document.getElementById("receta-id").value = "";
    document.getElementById("receta-nombre").value = "";
    document.getElementById("receta-producto-final").value = "";
    document.getElementById("lista-ingredientes").innerHTML = "";
    agregarFilaIngrediente(); 
    document.getElementById("modal-receta").style.display = "flex";
}

async function abrirModalEditar(id) {
    // 1. Mostrar modal cargando
    document.getElementById("modal-receta").style.display = "flex";
    document.getElementById("modal-titulo").innerText = "Cargando ingredientes...";
    document.getElementById("lista-ingredientes").innerHTML = ""; // Limpiar

    let recetaFull = null;

    try {
        // 2. PETICIÓN CRÍTICA: Traer detalle completo del servidor
        const res = await fetch(`${API_URL}/api/recetas/${id}`);
        if(res.ok) {
            recetaFull = await res.json();
        } else {
            // Fallback por si la API de detalle falla
            recetaFull = todasLasRecetas.find(r => r.id_receta === id);
        }
    } catch(e) {
        console.error("Error fetching detail:", e);
        recetaFull = todasLasRecetas.find(r => r.id_receta === id);
    }

    if(!recetaFull) { alert("No se pudo cargar la receta"); cerrarModal(); return; }

    // 3. Llenar formulario
    document.getElementById("modal-titulo").innerText = "Editar Receta";
    document.getElementById("receta-id").value = recetaFull.id_receta;
    document.getElementById("receta-nombre").value = recetaFull.nombre;
    document.getElementById("receta-producto-final").value = recetaFull.id_producto_final || "";

    // 4. Llenar ingredientes
    const tbody = document.getElementById("lista-ingredientes");
    tbody.innerHTML = "";

    if (recetaFull.ingredientes && recetaFull.ingredientes.length > 0) {
        recetaFull.ingredientes.forEach(ing => {
            // Manejamos 'cantidad' o 'cantidad_bruta' según venga del back
            const cantidad = ing.cantidad || ing.cantidad_bruta || 0;
            agregarFilaIngrediente(ing.id_insumo, cantidad);
        });
    } else {
        agregarFilaIngrediente(); // Fila vacía si no hay
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
        <td><select class="form-control-modal insumo-select" onchange="actualizarUnidadRow(this)">${options}</select></td>
        <td><input type="number" class="form-control-modal cantidad-input" step="0.001" value="${cantidadPre || ''}" placeholder="0.00"></td>
        <td style="text-align:center; padding-top:15px;"><span class="unidad-texto" style="font-size:0.8rem; color:#666;">-</span></td>
        <td style="text-align:center;"><button type="button" class="btn-remove" onclick="this.closest('tr').remove()">&times;</button></td>
    `;
    tbody.appendChild(tr);

    if(idInsumoPre) actualizarUnidadRow(tr.querySelector(".insumo-select"));
}

function actualizarUnidadRow(select) {
    const tr = select.closest("tr");
    const idProd = select.value;
    const span = tr.querySelector(".unidad-texto");
    
    if(!idProd) { span.innerText = "-"; return; }

    const prod = insumosList.find(p => p.id_producto == idProd);
    if(prod) {
        const u = unidadesList.find(x => x.id == prod.unidad_id);
        span.innerText = u ? u.nombre : "u";
    }
}

// 6. GUARDAR
async function guardarReceta() {
    const id = document.getElementById("receta-id").value;
    const nombre = document.getElementById("receta-nombre").value;
    const idProdFinal = document.getElementById("receta-producto-final").value;

    if (!nombre) { alert("El nombre es obligatorio"); return; }

    // Recolectar tabla
    const filas = document.querySelectorAll("#lista-ingredientes tr");
    let ingredientes = [];

    filas.forEach(tr => {
        const sel = tr.querySelector(".insumo-select");
        const cant = tr.querySelector(".cantidad-input");
        if(sel && sel.value && cant.value) {
            // Buscamos la unidad del insumo original para evitar Error 500
            const prod = insumosList.find(p => p.id_producto == sel.value);
            ingredientes.push({
                id_insumo: parseInt(sel.value),
                cantidad: parseFloat(cant.value),
                unidad_id: prod ? prod.unidad_id : null 
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
            cargarRecetas();
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