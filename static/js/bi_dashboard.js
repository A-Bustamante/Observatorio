// ============================================================
// TABLERO BI DIMENSIONAL — COHORTE, RETENCIÓN & ALERTAS TEMPRANAS
// ============================================================

let biChartDesercion = null;
let biChartAlertas = null;
let biCatalogos = null;
let currentDrilldownData = null;

// Escuchar cambios de filtros
function onBiFacultadChange() {
    const facSelect = document.getElementById("bi-filter-facultad");
    const progSelect = document.getElementById("bi-filter-programa");
    if (!facSelect || !progSelect || !biCatalogos) return;

    const selectedFac = facSelect.value;
    const mapping = biCatalogos.facultad_mapping || {};

    let optionsHtml = '<option value="TODOS">Todos los Programas</option>';
    (biCatalogos.programas || []).forEach(prog => {
        const facOfProg = mapping[prog] || "Otras Facultades";
        if (selectedFac === "TODAS" || facOfProg === selectedFac) {
            optionsHtml += `<option value="${prog}">${prog}</option>`;
        }
    });
    progSelect.innerHTML = optionsHtml;
    loadBiDashboard();
}

function resetBiFilters() {
    const fac = document.getElementById("bi-filter-facultad");
    const prog = document.getElementById("bi-filter-programa");
    const est = document.getElementById("bi-filter-estrato");
    if (fac) fac.value = "TODAS";
    if (est) est.value = "TODOS";
    if (prog) {
        if (biCatalogos && biCatalogos.programas) {
            let optionsHtml = '<option value="TODOS">Todos los Programas</option>';
            biCatalogos.programas.forEach(p => optionsHtml += `<option value="${p}">${p}</option>`);
            prog.innerHTML = optionsHtml;
        }
        prog.value = "TODOS";
    }
    loadBiDashboard();
}

async function loadBiDashboard() {
    const facSelect = document.getElementById("bi-filter-facultad");
    const progSelect = document.getElementById("bi-filter-programa");
    const estSelect = document.getElementById("bi-filter-estrato");
    const loaderPill = document.getElementById("bi-loading-pill");

    const facultad = facSelect ? facSelect.value : "TODAS";
    const programa = progSelect ? progSelect.value : "TODOS";
    const estrato = estSelect ? estSelect.value : "TODOS";

    if (loaderPill) loaderPill.classList.remove("hidden");

    try {
        const params = new URLSearchParams({ facultad, programa, estrato });
        const resp = await fetch(`/api/bi/cohort-dashboard?${params}`);
        if (!resp.ok) {
            console.error("Error al cargar tablero BI");
            if (loaderPill) loaderPill.classList.add("hidden");
            return;
        }

        const data = await resp.json();
        if (loaderPill) loaderPill.classList.add("hidden");

        if (!biCatalogos && data.catalogos) {
            biCatalogos = data.catalogos;
            initBiFilterOptions(data.catalogos);
        }

        renderBiKpis(data.kpis);
        renderBiCharts(data.desglose_programas, data.matriz_confusion);
        renderBiTable(data.desglose_programas);

    } catch (err) {
        console.error("Fallo de conexión al cargar tablero BI:", err);
        if (loaderPill) loaderPill.classList.add("hidden");
    }
}

function initBiFilterOptions(catalogos) {
    const facSelect = document.getElementById("bi-filter-facultad");
    const progSelect = document.getElementById("bi-filter-programa");
    const estSelect = document.getElementById("bi-filter-estrato");

    if (facSelect && catalogos.facultades) {
        let facHtml = '<option value="TODAS">Todas las Facultades</option>';
        catalogos.facultades.forEach(f => {
            facHtml += `<option value="${f}">${f}</option>`;
        });
        facSelect.innerHTML = facHtml;
    }

    if (progSelect && catalogos.programas) {
        let progHtml = '<option value="TODOS">Todos los Programas</option>';
        catalogos.programas.forEach(p => {
            progHtml += `<option value="${p}">${p}</option>`;
        });
        progSelect.innerHTML = progHtml;
    }

    if (estSelect && catalogos.estratos) {
        let estHtml = '<option value="TODOS">Todos los Estratos</option>';
        catalogos.estratos.forEach(e => {
            estHtml += `<option value="${e}">Estrato ${e}</option>`;
        });
        estSelect.innerHTML = estHtml;
    }
}

function getSemaforoBadge(semaforo, labelText = null) {
    if (semaforo === "verde") {
        return `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-sm">
            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            ${labelText || "Cumple Meta"}
        </span>`;
    } else if (semaforo === "amarillo") {
        return `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300 shadow-sm">
            <span class="w-2 h-2 rounded-full bg-amber-500"></span>
            ${labelText || "En Observación"}
        </span>`;
    } else {
        return `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300 shadow-sm">
            <span class="w-2 h-2 rounded-full bg-rose-500 animate-bounce"></span>
            ${labelText || "Crítico"}
        </span>`;
    }
}

function renderBiKpis(kpis) {
    if (!kpis) return;

    // 1. Absorción
    const abs = kpis.absorcion;
    document.getElementById("kpi-absorcion-val").textContent = `${abs.valor}%`;
    document.getElementById("kpi-absorcion-sem").innerHTML = getSemaforoBadge(abs.semaforo);
    document.getElementById("kpi-absorcion-sub").textContent = `${abs.numerador.toLocaleString()} cohorte / ${abs.denominador.toLocaleString()} admitidos`;

    // 2. Retención (Matriculados & Pagados)
    const ret = kpis.retencion;
    document.getElementById("kpi-retencion-val").textContent = `${ret.valor}%`;
    document.getElementById("kpi-retencion-sem").innerHTML = getSemaforoBadge(ret.semaforo);
    document.getElementById("kpi-retencion-sub").textContent = `${ret.numerador.toLocaleString()} matriculados con pago / ${ret.denominador.toLocaleString()} cohorte`;

    // 3. Deserción
    const des = kpis.desercion;
    document.getElementById("kpi-desercion-val").textContent = `${des.valor}%`;
    document.getElementById("kpi-desercion-sem").innerHTML = getSemaforoBadge(des.semaforo);
    document.getElementById("kpi-desercion-sub").textContent = `${des.numerador.toLocaleString()} desertores (no renovó o sin pago)`;

    // 4. Promedio Cohorte
    const pro = kpis.promedio_cohorte;
    document.getElementById("kpi-promedio-val").textContent = `${pro.valor.toFixed(2)}`;
    document.getElementById("kpi-promedio-sem").innerHTML = getSemaforoBadge(pro.semaforo);
    document.getElementById("kpi-promedio-sub").textContent = `Escala 0.0 - 5.0 (Meta institucional: ≥ 3.6)`;

    // 5. Número de Alertados
    const ale = kpis.alertados;
    document.getElementById("kpi-alertados-val").textContent = `${ale.valor.toLocaleString()}`;
    document.getElementById("kpi-alertados-sem").innerHTML = `<span class="text-xs px-2.5 py-1 rounded-full bg-purple-100 text-purple-800 font-bold border border-purple-200">${ale.tasa_alertados}% cohorte</span>`;
    document.getElementById("kpi-alertados-sub").textContent = `Bajo regla de notas < 3.0 o 0 accesos`;

    // 6. Precisión
    const pre = kpis.precision_alerta;
    document.getElementById("kpi-precision-val").textContent = `${pre.valor}%`;
    document.getElementById("kpi-precision-sem").innerHTML = getSemaforoBadge(pre.semaforo);
    document.getElementById("kpi-precision-sub").textContent = `${pre.numerador} desertaron de ${pre.denominador} alertados`;

    // 7. Cobertura
    const cob = kpis.cobertura_alerta;
    document.getElementById("kpi-cobertura-val").textContent = `${cob.valor}%`;
    document.getElementById("kpi-cobertura-sem").innerHTML = getSemaforoBadge(cob.semaforo);
    document.getElementById("kpi-cobertura-sub").textContent = `Detectó ${cob.numerador} de los ${cob.denominador} desertores`;
}

function renderBiCharts(desglose, matriz) {
    if (!desglose || desglose.length === 0) return;

    // --- GRÁFICO 1: RETENCIÓN Y DESERCIÓN POR PROGRAMA ---
    const ctxDes = document.getElementById("bi-chart-desercion");
    if (ctxDes) {
        if (biChartDesercion) biChartDesercion.destroy();

        const labels = desglose.map(d => d.programa);
        const dataRet = desglose.map(d => d.retencion_pct);
        const dataDes = desglose.map(d => d.desercion_pct);

        biChartDesercion = new Chart(ctxDes, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Retención Pagada (%)",
                        data: dataRet,
                        backgroundColor: "rgba(16, 185, 129, 0.85)",
                        borderColor: "rgba(5, 150, 105, 1)",
                        borderWidth: 1.5,
                        borderRadius: 6
                    },
                    {
                        label: "Deserción / No Pago (%)",
                        data: dataDes,
                        backgroundColor: "rgba(239, 68, 68, 0.85)",
                        borderColor: "rgba(220, 38, 38, 1)",
                        borderWidth: 1.5,
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        ticks: { font: { size: 11, family: "Inter" }, maxRotation: 25, minRotation: 15 },
                        grid: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { callback: v => v + "%", font: { size: 10, family: "Inter" } },
                        grid: { color: "rgba(226, 232, 240, 0.6)" }
                    }
                },
                plugins: {
                    legend: { position: "top", labels: { font: { size: 11, weight: "bold" }, usePointStyle: true } },
                    tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.raw}%` } }
                }
            }
        });
    }

    // --- GRÁFICO 2: PRECISIÓN VS COBERTURA POR PROGRAMA ---
    const ctxAle = document.getElementById("bi-chart-alertas");
    if (ctxAle) {
        if (biChartAlertas) biChartAlertas.destroy();

        const labels = desglose.map(d => d.programa);
        const dataPrec = desglose.map(d => d.precision_pct);
        const dataCob = desglose.map(d => d.cobertura_pct);

        biChartAlertas = new Chart(ctxAle, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Precisión Alerta (%)",
                        data: dataPrec,
                        backgroundColor: "rgba(168, 85, 247, 0.85)",
                        borderColor: "rgba(147, 51, 234, 1)",
                        borderWidth: 1.5,
                        borderRadius: 6
                    },
                    {
                        label: "Cobertura Alerta (%)",
                        data: dataCob,
                        backgroundColor: "rgba(59, 130, 246, 0.85)",
                        borderColor: "rgba(37, 99, 235, 1)",
                        borderWidth: 1.5,
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        ticks: { font: { size: 11, family: "Inter" }, maxRotation: 25, minRotation: 15 },
                        grid: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { callback: v => v + "%", font: { size: 10, family: "Inter" } },
                        grid: { color: "rgba(226, 232, 240, 0.6)" }
                    }
                },
                plugins: {
                    legend: { position: "top", labels: { font: { size: 11, weight: "bold" }, usePointStyle: true } },
                    tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.raw}%` } }
                }
            }
        });
    }
}

function renderBiTable(desglose) {
    const tbody = document.getElementById("bi-table-body");
    if (!tbody) return;

    if (!desglose || desglose.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="p-8 text-center text-slate-400 font-sans">No hay datos para los filtros seleccionados.</td></tr>`;
        return;
    }

    tbody.innerHTML = desglose.map(row => {
        const semDes = getSemaforoBadge(row.semaforo_desercion, `${row.desercion_pct}%`);
        const semRet = getSemaforoBadge(row.semaforo_retencion, `${row.retencion_pct}%`);
        const semPrec = getSemaforoBadge(row.semaforo_precision, `${row.precision_pct}%`);
        const semCob = getSemaforoBadge(row.semaforo_cobertura, `${row.cobertura_pct}%`);

        return `<tr class="hover:bg-blue-50/50 transition border-b border-slate-100 cursor-pointer group"
                    onclick="openBiDrilldown('programa', '${row.programa.replace(/'/g, "\\'")}')"
                    title="Haga clic para ver los ${row.cohorte} estudiantes de ${row.programa}">
            <td class="p-3 font-semibold text-slate-900 flex items-center justify-between">
                <span>${row.programa}</span>
                <i class="fa-solid fa-arrow-up-right-from-square text-[10px] text-blue-400 opacity-0 group-hover:opacity-100 transition"></i>
            </td>
            <td class="p-3 text-slate-500 text-xs">${row.facultad}</td>
            <td class="p-3 text-center font-mono font-bold text-slate-800">${row.cohorte}</td>
            <td class="p-3 text-center font-mono text-slate-700">${row.promedio.toFixed(2)}</td>
            <td class="p-3 text-center">${semRet}</td>
            <td class="p-3 text-center">${semDes}</td>
            <td class="p-3 text-center font-mono text-purple-700 font-bold">${row.alertados}</td>
            <td class="p-3 text-center">${semPrec}</td>
            <td class="p-3 text-center">${semCob}</td>
        </tr>`;
    }).join('');
}

// ============================================================
// DRILL-DOWN / AUDITORÍA DE REGISTROS AL HACER CLIC EN UN VALOR
// ============================================================

async function openBiDrilldown(metrica, progOverride = null) {
    const modal = document.getElementById("bi-drilldown-modal");
    if (!modal) return;

    modal.classList.remove("hidden");
    document.body.style.overflow = "hidden"; // Bloquear scroll de fondo

    const titleEl = document.getElementById("bi-modal-title");
    const subtitleEl = document.getElementById("bi-modal-subtitle");
    const countBadge = document.getElementById("bi-modal-count");
    const tbody = document.getElementById("bi-modal-tbody");
    const searchInput = document.getElementById("bi-modal-search");

    if (searchInput) searchInput.value = "";
    titleEl.textContent = "Cargando registros...";
    subtitleEl.textContent = "Consultando datos de estudiantes...";
    countBadge.textContent = "Consultando...";
    tbody.innerHTML = `<tr><td colspan="8" class="p-12 text-center">
        <div class="animate-spin inline-block w-8 h-8 border-3 border-emerald-500 border-t-transparent rounded-full"></div>
        <p class="text-xs text-slate-500 mt-2 font-sans">Obteniendo registros con los que se calculó el indicador...</p>
    </td></tr>`;

    const facSelect = document.getElementById("bi-filter-facultad");
    const progSelect = document.getElementById("bi-filter-programa");
    const estSelect = document.getElementById("bi-filter-estrato");

    const facultad = facSelect ? facSelect.value : "TODAS";
    const programa = progOverride || (progSelect ? progSelect.value : "TODOS");
    const estrato = estSelect ? estSelect.value : "TODOS";

    try {
        const params = new URLSearchParams({ metrica, facultad, programa, estrato });
        const resp = await fetch(`/api/bi/drilldown?${params}`);
        if (!resp.ok) {
            tbody.innerHTML = `<tr><td colspan="8" class="p-8 text-center text-rose-500 font-sans">Error al consultar los registros.</td></tr>`;
            return;
        }

        const data = await resp.json();
        currentDrilldownData = data;

        titleEl.textContent = data.titulo || "Detalle de Registros de Cálculo";
        subtitleEl.textContent = data.subtitulo || `Métrica: ${metrica.toUpperCase()}`;
        countBadge.textContent = `${data.total.toLocaleString()} estudiantes`;

        renderDrilldownRows(data.registros);

    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" class="p-8 text-center text-rose-500 font-sans">Error de conexión: ${err.message}</td></tr>`;
    }
}

function renderDrilldownRows(registros) {
    const tbody = document.getElementById("bi-modal-tbody");
    if (!tbody) return;

    if (!registros || registros.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="p-8 text-center text-slate-400 font-sans">No se encontraron estudiantes para este criterio.</td></tr>`;
        return;
    }

    tbody.innerHTML = registros.map(r => {
        let badgeEstado = '';
        if (r.estado_cohorte.includes("Retenido")) {
            badgeEstado = `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">Retenido (Pagado)</span>`;
        } else if (r.estado_cohorte.includes("Pendiente")) {
            badgeEstado = `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-200">Deserción (Pago Pendiente)</span>`;
        } else if (r.estado_cohorte.includes("Admitido No Matriculado")) {
            badgeEstado = `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-100 text-slate-700 border border-slate-200">Admitido No Matriculado</span>`;
        } else {
            badgeEstado = `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 text-rose-800 border border-rose-200">Deserción (No Renovó)</span>`;
        }

        let badgeAlerta = r.alertado
            ? `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-purple-100 text-purple-800 border border-purple-200 cursor-help" title="${r.motivo_alerta}">⚠️ Alerta Activa</span>`
            : `<span class="px-2 py-0.5 rounded text-[11px] text-slate-400">Sin Alerta</span>`;

        // Indicador visual para promedio Moodle < 3.0
        const isBajoProm = r.promedio_moodle !== '—' && Number(r.promedio_moodle) < 3.0;
        const isCeroAcc = r.accesos_moodle !== '—' && Number(r.accesos_moodle) === 0;

        return `<tr class="hover:bg-slate-50 transition border-b border-slate-100 text-xs">
            <td class="p-2.5 font-mono font-bold text-slate-900">${r.documento}</td>
            <td class="p-2.5 font-medium text-slate-800">${r.nombre_completo}</td>
            <td class="p-2.5 text-slate-700">${r.programa}</td>
            <td class="p-2.5 text-center font-mono">${r.estrato !== 'N/D' ? 'Estrato ' + r.estrato : '—'}</td>
            <td class="p-2.5 text-center font-mono font-bold ${isBajoProm ? 'text-rose-600 bg-rose-50/50 rounded' : 'text-slate-800'}">
                ${r.promedio_moodle !== undefined ? r.promedio_moodle : r.promedio}
            </td>
            <td class="p-2.5 text-center font-mono font-semibold ${isCeroAcc ? 'text-amber-600 font-extrabold bg-amber-50 rounded' : 'text-slate-700'}">
                ${r.accesos_moodle !== undefined ? r.accesos_moodle : '—'}
            </td>
            <td class="p-2.5 text-center font-medium">${r.estado_pago_2025_2}</td>
            <td class="p-2.5 text-center">${badgeAlerta}</td>
            <td class="p-2.5 text-center">${badgeEstado}</td>
        </tr>`;
    }).join('');
}

function filterDrilldownModal() {
    if (!currentDrilldownData || !currentDrilldownData.registros) return;
    const term = document.getElementById("bi-modal-search").value.toLowerCase().trim();
    if (!term) {
        renderDrilldownRows(currentDrilldownData.registros);
        document.getElementById("bi-modal-count").textContent = `${currentDrilldownData.total.toLocaleString()} estudiantes`;
        return;
    }

    const filtered = currentDrilldownData.registros.filter(r => {
        return (r.documento && r.documento.toLowerCase().includes(term)) ||
            (r.nombre_completo && r.nombre_completo.toLowerCase().includes(term)) ||
            (r.programa && r.programa.toLowerCase().includes(term)) ||
            (r.motivo_alerta && r.motivo_alerta.toLowerCase().includes(term)) ||
            (r.estado_cohorte && r.estado_cohorte.toLowerCase().includes(term));
    });

    renderDrilldownRows(filtered);
    document.getElementById("bi-modal-count").textContent = `${filtered.length} de ${currentDrilldownData.total} estudiantes`;
}

function closeBiDrilldownModal() {
    const modal = document.getElementById("bi-drilldown-modal");
    if (modal) modal.classList.add("hidden");
    document.body.style.overflow = "auto";
}

function exportDrilldownCSV() {
    if (!currentDrilldownData || !currentDrilldownData.registros || currentDrilldownData.registros.length === 0) return;

    const headers = ["Documento", "Nombre Completo", "Programa", "Facultad", "Estrato", "Promedio Moodle Sem 4-8", "Accesos Moodle Sem 7-8", "Promedio Periodo", "Estado Pago 2025-2", "Alertado", "Motivo Alerta", "Estado Cohorte"];
    const rows = currentDrilldownData.registros.map(r => [
        `"${r.documento}"`,
        `"${r.nombre_completo.replace(/"/g, '""')}"`,
        `"${r.programa}"`,
        `"${r.facultad}"`,
        `"${r.estrato}"`,
        `"${r.promedio_moodle !== undefined ? r.promedio_moodle : ''}"`,
        `"${r.accesos_moodle !== undefined ? r.accesos_moodle : ''}"`,
        `"${r.promedio}"`,
        `"${r.estado_pago_2025_2}"`,
        `"${r.alertado ? 'SI' : 'NO'}"`,
        `"${r.motivo_alerta.replace(/"/g, '""')}"`,
        `"${r.estado_cohorte}"`
    ]);

    const csvContent = "\uFEFF" + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Registros_${currentDrilldownData.metrica || 'BI'}_Cohorte.csv`;
    a.click();
    URL.revokeObjectURL(url);
}

// Escuchar tecla Escape para cerrar modal
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeBiDrilldownModal();
});
