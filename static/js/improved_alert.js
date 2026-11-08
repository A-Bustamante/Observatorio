/**
 * improved_alert.js
 * Módulo para visualización y gestión de la regla optimizada de alerta temprana (capacidad <= 120 consejeros).
 */

let improvedAlertData = null;
let currentAlertFilter = 'all';

async function loadImprovedAlertDashboard() {
    const loadingEl = document.getElementById('improved-alert-loading');
    const contentEl = document.getElementById('improved-alert-content');
    
    if (loadingEl) loadingEl.classList.remove('hidden');
    if (contentEl) contentEl.classList.add('hidden');

    try {
        const response = await fetch('/api/bi/improved-alert');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        improvedAlertData = data;
        renderImprovedAlertView(data);
    } catch (err) {
        console.error("Error al cargar mejora de alerta:", err);
        if (loadingEl) {
            loadingEl.innerHTML = `
                <div class="p-6 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-center">
                    <p class="font-bold">Error al cargar datos del módulo de alerta temprana</p>
                    <p class="text-xs mt-1 font-mono">${err.message}</p>
                </div>
            `;
        }
    } finally {
        if (loadingEl) loadingEl.classList.add('hidden');
        if (contentEl) contentEl.classList.remove('hidden');
    }
}

function renderImprovedAlertView(data) {
    const act = data.regla_actual;
    const opt = data.regla_nueva;

    // Actualizar Badges y KPIs Superiores
    setText('ia-opt-n-alertados', `${opt.n_alertados}`);
    setText('ia-opt-precision', `${opt.precision}%`);
    setText('ia-opt-cobertura', `${opt.cobertura}%`);
    setText('ia-opt-tp', `${opt.tp}`);
    setText('ia-opt-fp', `${opt.fp}`);

    // KPIs Comparativos
    setText('ia-cmp-act-n', `${act.n_alertados}`);
    setText('ia-cmp-opt-n', `${opt.n_alertados} / ${opt.capacidad_maxima}`);
    setText('ia-cmp-act-prec', `${act.precision}%`);
    setText('ia-cmp-opt-prec', `${opt.precision}%`);
    setText('ia-cmp-act-cob', `${act.cobertura}%`);
    setText('ia-cmp-opt-cob', `${opt.cobertura}%`);
    setText('ia-cmp-act-fp', `${act.fp}`);
    setText('ia-cmp-opt-fp', `${opt.fp}`);

    // Matriz de Confusión
    setText('cm-tp', opt.tp);
    setText('cm-fp', opt.fp);
    setText('cm-fn', opt.fn);
    setText('cm-tn', opt.tn);

    setText('cm-total-alertados', opt.n_alertados);
    setText('cm-total-no-alertados', opt.fn + opt.tn);
    setText('cm-total-desertores', opt.total_desertores);
    setText('cm-total-retenidos', opt.total_retenidos);
    setText('cm-total-cohorte', opt.total_cohorte);

    // Renderizar estudiantes alertados
    renderAlertedStudentsTable(data.estudiantes_alertados || []);
}

function renderAlertedStudentsTable(students) {
    const tbody = document.getElementById('improved-alert-table-body');
    const counter = document.getElementById('ia-table-count');
    if (!tbody) return;

    const searchTerm = (document.getElementById('ia-search-input')?.value || '').toLowerCase().trim();
    
    let filtered = students.filter(s => {
        const matchesSearch = !searchTerm || 
            s.documento.toLowerCase().includes(searchTerm) ||
            s.nombre_completo.toLowerCase().includes(searchTerm) ||
            s.programa.toLowerCase().includes(searchTerm) ||
            s.motivo_alerta.toLowerCase().includes(searchTerm);

        if (!matchesSearch) return false;

        if (currentAlertFilter === 'desertores') return s.deserto_real;
        if (currentAlertFilter === 'retenidos') return !s.deserto_real;
        if (currentAlertFilter === 'inactivos') return s.acc_sem_7_8 === 0;
        return true;
    });

    if (counter) counter.innerText = `${filtered.length} de ${students.length} estudiantes`;

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="p-8 text-center text-slate-400 font-sans">No se encontraron estudiantes con los filtros seleccionados.</td></tr>`;
        return;
    }

    tbody.innerHTML = filtered.map((s, idx) => {
        const badgeEstado = s.deserto_real
            ? `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 text-rose-800 border border-rose-200">🔴 Desertó (TP)</span>`
            : `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">🟢 Retenido (FP)</span>`;

        let badgeMotivoClass = "bg-purple-100 text-purple-800 border-purple-200";
        if (s.acc_sem_7_8 === 0) {
            badgeMotivoClass = "bg-rose-100 text-rose-800 border-rose-200";
        } else if (s.acc_sem_7_8 <= 2) {
            badgeMotivoClass = "bg-amber-100 text-amber-800 border-amber-200";
        }

        return `
            <tr class="hover:bg-slate-50 transition border-b border-slate-100 text-xs">
                <td class="p-2.5 text-center font-mono text-slate-400 font-bold">${idx + 1}</td>
                <td class="p-2.5 font-mono font-bold text-slate-900">${s.documento}</td>
                <td class="p-2.5 font-medium text-slate-800">${s.nombre_completo}</td>
                <td class="p-2.5 text-slate-700">${s.programa}</td>
                <td class="p-2.5 text-center font-mono font-bold ${s.prom_moodle_4_8 < 3.0 ? 'text-rose-600' : 'text-slate-700'}">
                    ${s.prom_moodle_4_8.toFixed(2)}
                </td>
                <td class="p-2.5 text-center font-mono font-extrabold ${s.acc_sem_7_8 === 0 ? 'text-rose-600 bg-rose-50 rounded' : 'text-slate-800'}">
                    ${s.acc_sem_7_8}
                </td>
                <td class="p-2.5 text-center font-mono text-slate-600">
                    ${s.acc_tot_1_8}
                </td>
                <td class="p-2.5">
                    <span class="inline-block px-2 py-1 rounded text-[11px] font-medium border ${badgeMotivoClass}">
                        ${s.motivo_alerta}
                    </span>
                </td>
                <td class="p-2.5 text-center">
                    ${badgeEstado}
                </td>
            </tr>
        `;
    }).join('');
}

function filterAlertTable(filterType) {
    currentAlertFilter = filterType;
    document.querySelectorAll('.ia-filter-btn').forEach(btn => {
        btn.classList.remove('bg-rose-600', 'text-white', 'border-rose-600');
        btn.classList.add('bg-white', 'text-slate-600', 'border-slate-200');
    });

    const activeBtn = document.getElementById(`ia-filter-${filterType}`);
    if (activeBtn) {
        activeBtn.classList.remove('bg-white', 'text-slate-600', 'border-slate-200');
        activeBtn.classList.add('bg-rose-600', 'text-white', 'border-rose-600');
    }

    if (improvedAlertData && improvedAlertData.estudiantes_alertados) {
        renderAlertedStudentsTable(improvedAlertData.estudiantes_alertados);
    }
}

function exportImprovedAlertCSV() {
    if (!improvedAlertData || !improvedAlertData.estudiantes_alertados) {
        alert("No hay datos disponibles para exportar.");
        return;
    }

    const students = improvedAlertData.estudiantes_alertados;
    let csv = "Index,Documento,Nombre Completo,Programa,Promedio_Sem_4_8,Accesos_Sem_7_8,Accesos_Totales_1_8,Motivo_Alerta,Estado_Real\n";
    
    students.forEach((s, idx) => {
        csv += `${idx + 1},"${s.documento}","${s.nombre_completo}","${s.programa}",${s.prom_moodle_4_8},${s.acc_sem_7_8},${s.acc_tot_1_8},"${s.motivo_alerta}","${s.deserto_real ? 'Deserto' : 'Retenido'}"\n`;
    });

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Estudiantes_Alertados_Consejeria_Priorizados_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function setText(elementId, text) {
    const el = document.getElementById(elementId);
    if (el) el.innerText = text;
}

