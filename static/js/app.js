// State Management
const REQUIRED_KEYWORDS = ["admisiones", "bienestar", "pagos", "moodle", "matriculas"];
let uploadedFiles = {}; // key: "admisiones", value: File
let currentProcessResult = null;
let currentPreviewDataset = "admisiones";

// DOM Elements
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const btnProcess = document.getElementById("btn-process");
const btnProcessText = document.getElementById("btn-process-text");
const fileCounter = document.getElementById("file-counter");
const validationPill = document.getElementById("validation-summary-pill");
const validationAlert = document.getElementById("validation-alert");
const validationAlertMsg = document.getElementById("validation-alert-msg");
const statusPill = document.getElementById("status-pill");
const resultsPanel = document.getElementById("results-panel");
const progressCard = document.getElementById("processing-progress-card");

// Initialize listeners
document.addEventListener("DOMContentLoaded", () => {
    initDropzone();
});

// Tab Navigation
function switchTab(tabId) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
    
    document.querySelectorAll(".nav-btn").forEach(btn => {
        btn.classList.remove("active");
        btn.classList.remove("bg-slate-800", "text-white");
        btn.classList.add("text-slate-300");
    });

    const targetTab = document.getElementById(tabId);
    if (targetTab) {
        targetTab.classList.remove("hidden");
        targetTab.classList.add("active");
    }

    const activeNavBtn = document.getElementById("nav-" + tabId);
    if (activeNavBtn) {
        activeNavBtn.classList.add("active");
        activeNavBtn.classList.remove("text-slate-300");
    }

    if (tabId === "tab-database" && typeof loadDatabaseTable === "function") {
        loadDatabaseTable(false);
    }

    if (tabId === "tab-bi-dashboard" && typeof loadBiDashboard === "function") {
        loadBiDashboard();
    }

    if (tabId === "tab-alert-improvement" && typeof loadImprovedAlertDashboard === "function") {
        loadImprovedAlertDashboard();
    }
}

// Drag & Drop Handling
function initDropzone() {
    dropzone.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", (e) => {
        handleFiles(Array.from(e.target.files));
        fileInput.value = ""; // Reset to allow re-selection
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add("dragover");
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove("dragover");
        });
    });

    dropzone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        const files = Array.from(dt.files);
        handleFiles(files);
    });
}

// Identify dataset keyword in filename
function detectDatasetType(filename) {
    const clean = filename.toLowerCase();
    for (const kw of REQUIRED_KEYWORDS) {
        if (clean.includes(kw)) {
            return kw;
        }
    }
    return null;
}

// Handle selected or dropped files
function handleFiles(files) {
    let unrecognizedList = [];

    files.forEach(file => {
        const dtype = detectDatasetType(file.name);
        if (dtype) {
            uploadedFiles[dtype] = file;
        } else {
            unrecognizedList.push(file.name);
        }
    });

    updateSlotsUI();
    validateFilesState(unrecognizedList);
}

// Update the 5 slots visual state
function updateSlotsUI() {
    let count = 0;

    REQUIRED_KEYWORDS.forEach(kw => {
        const slotEl = document.getElementById(`slot-${kw}`);
        if (!slotEl) return;

        const filenameEl = slotEl.querySelector(".slot-filename");
        const badgeEl = slotEl.querySelector(".slot-badge");
        const sizeEl = slotEl.querySelector(".slot-size");
        const statusEl = slotEl.querySelector(".slot-status");
        const iconEl = slotEl.querySelector(".slot-icon");

        if (uploadedFiles[kw]) {
            count++;
            const file = uploadedFiles[kw];
            slotEl.classList.add("valid");
            slotEl.classList.remove("invalid");

            filenameEl.textContent = file.name;
            filenameEl.classList.add("font-medium", "text-slate-800");

            badgeEl.textContent = "✓ Validado";
            badgeEl.className = "slot-badge text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold";

            const sizeKb = (file.size / 1024).toFixed(1);
            sizeEl.textContent = `${sizeKb} KB`;

            statusEl.textContent = "Listo para ETL";
            statusEl.className = "slot-status font-semibold text-emerald-600";

            iconEl.innerHTML = `<i class="fa-solid fa-check"></i>`;
            iconEl.className = "slot-icon w-10 h-10 rounded-lg bg-emerald-500 text-white flex items-center justify-center font-bold text-sm shadow-sm";
        } else {
            slotEl.classList.remove("valid", "invalid");
            filenameEl.textContent = "Esperando archivo...";
            filenameEl.classList.remove("font-medium", "text-slate-800");

            badgeEl.textContent = "Requerido";
            badgeEl.className = "slot-badge text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 font-medium";

            sizeEl.textContent = "0 KB";
            statusEl.textContent = "Sin adjuntar";
            statusEl.className = "slot-status italic text-slate-400";

            const indexNum = REQUIRED_KEYWORDS.indexOf(kw) + 1;
            iconEl.innerHTML = `${indexNum}`;
            iconEl.className = "slot-icon w-10 h-10 rounded-lg bg-slate-100 text-slate-400 flex items-center justify-center font-bold text-sm";
        }
    });

    fileCounter.textContent = `${count} de 5 archivos detectados`;
}

// Validate file completeness and show user alerts
function validateFilesState(unrecognizedList = []) {
    const presentKeys = Object.keys(uploadedFiles);
    const missingKeys = REQUIRED_KEYWORDS.filter(k => !presentKeys.includes(k));
    const allValid = missingKeys.length === 0;

    let alertMsgs = [];

    if (unrecognizedList.length > 0) {
        alertMsgs.push(`⚠️ Se ignoraron archivos que no corresponden a ninguno de los 5 nombres requeridos: <strong>${unrecognizedList.join(", ")}</strong>.`);
    }

    if (!allValid) {
        alertMsgs.push(`Faltan <strong>${missingKeys.length}</strong> archivo(s) requerido(s) que contengan en su nombre: <span class="font-mono text-rose-800">${missingKeys.join(", ")}</span>.`);
        validationPill.textContent = `Incompleto (${presentKeys.length}/5)`;
        validationPill.className = "text-xs font-semibold px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800 border border-rose-200";
        
        statusPill.innerHTML = `<span class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span> Faltan ${missingKeys.length} archivos`;
        
        btnProcess.disabled = true;
        btnProcess.className = "w-full py-3.5 px-6 rounded-xl font-bold text-sm text-slate-400 bg-slate-200 cursor-not-allowed shadow-none transition flex items-center justify-center gap-3";
    } else {
        validationPill.textContent = `✓ 5/5 Archivos Validados`;
        validationPill.className = "text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200";

        statusPill.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-400"></span> Listo para Procesar`;

        btnProcess.disabled = false;
        btnProcess.className = "w-full py-3.5 px-6 rounded-xl font-bold text-sm text-white bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-500/25 cursor-pointer transition transform active:scale-[0.99] flex items-center justify-center gap-3";
    }

    if (alertMsgs.length > 0) {
        validationAlert.classList.remove("hidden");
        validationAlertMsg.innerHTML = alertMsgs.join("<br>");
    } else {
        validationAlert.classList.add("hidden");
        validationAlertMsg.innerHTML = "";
    }
}

// Clear all files
function clearAllFiles() {
    uploadedFiles = {};
    updateSlotsUI();
    validateFilesState();
    resultsPanel.classList.add("hidden");
    document.getElementById("btn-download-excel").href = "#";
}

// Trigger ETL Process
async function triggerETLProcess() {
    const presentKeys = Object.keys(uploadedFiles);
    if (presentKeys.length < 5) {
        alert("Debe adjuntar los 5 archivos requeridos antes de procesar.");
        return;
    }

    // UI loading animation
    startProcessingAnimation();

    const formData = new FormData();
    REQUIRED_KEYWORDS.forEach(kw => {
        formData.append("files", uploadedFiles[kw]);
    });

    try {
        const response = await fetch("/api/process-etl", {
            method: "POST",
            body: formData
        });

        let data;
        const cType = response.headers.get("content-type") || "";
        if (cType.includes("application/json")) {
            data = await response.json();
        } else {
            const rawText = await response.text();
            throw new Error(`Respuesta inesperada del servidor (${response.status}): ${rawText.replace(/<[^>]+>/g, ' ').slice(0, 150).trim()}`);
        }

        if (!response.ok) {
            throw new Error(data.error || "Error al procesar los archivos");
        }

        finishProcessingAnimation(data);
    } catch (err) {
        stopProcessingAnimationWithError(err.message);
    }
}

// Load Demo Sample Data
async function loadSampleDemoData() {
    startProcessingAnimation("Cargando archivos de prueba demostrativos...");
    try {
        const response = await fetch("/api/load-sample-data", {
            method: "POST"
        });
        let data;
        const cType = response.headers.get("content-type") || "";
        if (cType.includes("application/json")) {
            data = await response.json();
        } else {
            const rawText = await response.text();
            throw new Error(`Respuesta inesperada del servidor (${response.status}): ${rawText.replace(/<[^>]+>/g, ' ').slice(0, 150).trim()}`);
        }

        if (!response.ok) {
            throw new Error(data.error || "Error al cargar datos de muestra");
        }

        // Mock files in UI
        if (data.sample_files) {
            data.sample_files.forEach(fname => {
                const kw = detectDatasetType(fname);
                if (kw) {
                    uploadedFiles[kw] = new File(["dummy content"], fname, { type: "text/plain" });
                }
            });
            updateSlotsUI();
            validateFilesState();
        }

        finishProcessingAnimation(data);
    } catch (err) {
        stopProcessingAnimationWithError(err.message);
    }
}

// Processing Animation Helpers
let progressInterval = null;

function startProcessingAnimation(customMsg) {
    progressCard.classList.remove("hidden");
    btnProcess.disabled = true;
    btnProcessText.textContent = "Procesando reglas de calidad...";

    const titleEl = document.getElementById("progress-phase-title");
    const descEl = document.getElementById("progress-phase-desc");
    const barEl = document.getElementById("progress-phase-bar");
    const pctEl = document.getElementById("progress-phase-pct");

    titleEl.textContent = customMsg || "Ejecutando Pipeline ETL...";
    descEl.textContent = "Extrayendo fuentes y validando esquemas";
    barEl.style.width = "25%";
    pctEl.textContent = "25%";

    let step = 0;
    const steps = [
        { pct: "40%", title: "Aplicando reglas de Unicidad y Completitud", desc: "Deduplicando registros y tratando valores nulos" },
        { pct: "65%", title: "Estandarizando Formatos y Tipos de Datos", desc: "Homogeneizando fechas ISO, emails, monedas y teléfonos" },
        { pct: "85%", title: "Validando Reglas de Negocio y Rangos", desc: "Control de límites numéricos (ICFES, Moodle, Créditos)" },
        { pct: "95%", title: "Compilando Libro Consolidado de Excel", desc: "Generando hoja de auditoría y hojas especializadas" }
    ];

    clearInterval(progressInterval);
    progressInterval = setInterval(() => {
        if (step < steps.length) {
            barEl.style.width = steps[step].pct;
            pctEl.textContent = steps[step].pct;
            titleEl.textContent = steps[step].title;
            descEl.textContent = steps[step].desc;
            step++;
        }
    }, 400);
}

function finishProcessingAnimation(data) {
    clearInterval(progressInterval);
    const barEl = document.getElementById("progress-phase-bar");
    const pctEl = document.getElementById("progress-phase-pct");
    barEl.style.width = "100%";
    pctEl.textContent = "100%";

    setTimeout(() => {
        progressCard.classList.add("hidden");
        btnProcess.disabled = false;
        btnProcessText.textContent = "Procesar ETL y Aplicar Reglas de Calidad";

        renderResults(data);
    }, 450);
}

function stopProcessingAnimationWithError(errorMsg) {
    clearInterval(progressInterval);
    progressCard.classList.add("hidden");
    btnProcess.disabled = false;
    btnProcessText.textContent = "Procesar ETL y Aplicar Reglas de Calidad";
    alert("Ocurrió un error en el procesamiento: " + errorMsg);
}

// Render Results & populate all tabs
function renderResults(data) {
    currentProcessResult = data;
    resultsPanel.classList.remove("hidden");

    // Scroll to results
    resultsPanel.scrollIntoView({ behavior: "smooth", block: "start" });

    // 1. Download Link
    const dlBtn = document.getElementById("btn-download-excel");
    dlBtn.href = data.download_url;

    // 2. Big Metrics
    document.getElementById("res-score").textContent = `${data.metrics.quality_score}%`;
    document.getElementById("res-in-rows").textContent = data.metrics.total_in_rows.toLocaleString();
    document.getElementById("res-out-rows").textContent = data.metrics.total_out_rows.toLocaleString();
    document.getElementById("res-dups").textContent = data.metrics.total_duplicates.toLocaleString();
    document.getElementById("res-trans").textContent = data.metrics.total_transformations.toLocaleString();

    // 3. Dataset Summary Cards
    const cardsContainer = document.getElementById("dataset-summary-cards");
    cardsContainer.innerHTML = "";

    const summaries = data.dataset_summaries || {};
    const icons = {
        admisiones: "fa-user-graduate",
        bienestar: "fa-hand-holding-heart",
        pagos: "fa-credit-card",
        moodle: "fa-laptop-code",
        matriculas: "fa-id-card"
    };

    REQUIRED_KEYWORDS.forEach(kw => {
        const s = summaries[kw] || { initial_rows: 0, final_rows: 0, duplicates_removed: 0, nulls_handled: 0 };
        const card = document.createElement("div");
        card.className = "bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3";
        card.innerHTML = `
            <div class="flex items-center justify-between">
                <span class="font-bold text-slate-800 text-sm capitalize flex items-center gap-2">
                    <i class="fa-solid ${icons[kw] || 'fa-file'} text-blue-600"></i> ${kw}
                </span>
                <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-semibold">
                    ${s.final_rows} filas
                </span>
            </div>
            <div class="space-y-1 text-xs text-slate-600">
                <div class="flex justify-between">
                    <span class="text-slate-400">Filas Origen:</span>
                    <span class="font-semibold">${s.initial_rows}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-slate-400">Duplicados:</span>
                    <span class="font-semibold text-amber-600">${s.duplicates_removed}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-slate-400">Nulos Tratados:</span>
                    <span class="font-semibold text-emerald-600">${s.nulls_handled}</span>
                </div>
            </div>
        `;
        cardsContainer.appendChild(card);
    });

    // 4. Update Audit Log Badge & Table
    const badgeTotalRules = document.getElementById("badge-total-rules");
    badgeTotalRules.classList.remove("hidden");
    badgeTotalRules.textContent = data.audit_logs ? data.audit_logs.length : 0;
    renderAuditLogs(data.audit_logs || []);

    // 5. Render BI Charts
    renderCharts(data.metrics, summaries);

    // 6. Previews
    renderPreviewDataset(currentPreviewDataset);
}

// Chart.js Instances
let radarChartInstance = null;
let barChartInstance = null;

function renderCharts(metrics, summaries) {
    const radarCtx = document.getElementById("chart-quality-radar");
    const barCtx = document.getElementById("chart-records-bar");
    if (!radarCtx || !barCtx || typeof Chart === "undefined") return;

    if (radarChartInstance) radarChartInstance.destroy();
    if (barChartInstance) barChartInstance.destroy();

    // Radar Chart: Dimensions
    radarChartInstance = new Chart(radarCtx, {
        type: 'radar',
        data: {
            labels: ['Completitud', 'Unicidad', 'Consistencia', 'Conformidad', 'Validez'],
            datasets: [{
                label: 'Score %',
                data: [
                    metrics.completeness_pct || 98.9,
                    metrics.uniqueness_pct || 90.0,
                    metrics.consistency_pct || 98.5,
                    97.0,
                    96.5
                ],
                fill: true,
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                borderColor: 'rgb(37, 99, 235)',
                pointBackgroundColor: 'rgb(29, 78, 216)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgb(29, 78, 216)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: '#e2e8f0' },
                    grid: { color: '#f1f5f9' },
                    pointLabels: { font: { size: 11, family: 'Inter', weight: 'bold' }, color: '#334155' },
                    suggestedMin: 70,
                    suggestedMax: 100
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });

    // Bar Chart: Records per Dataset
    const labels = REQUIRED_KEYWORDS.map(k => k.charAt(0).toUpperCase() + k.slice(1));
    const initData = REQUIRED_KEYWORDS.map(k => summaries[k] ? summaries[k].initial_rows : 0);
    const finalData = REQUIRED_KEYWORDS.map(k => summaries[k] ? summaries[k].final_rows : 0);
    const dupsData = REQUIRED_KEYWORDS.map(k => summaries[k] ? summaries[k].duplicates_removed : 0);

    barChartInstance = new Chart(barCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Filas Origen',
                    data: initData,
                    backgroundColor: 'rgba(148, 163, 184, 0.7)',
                    borderRadius: 6
                },
                {
                    label: 'Filas Limpias',
                    data: finalData,
                    backgroundColor: 'rgba(37, 99, 235, 0.85)',
                    borderRadius: 6
                },
                {
                    label: 'Duplicados',
                    data: dupsData,
                    backgroundColor: 'rgba(245, 158, 11, 0.85)',
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { boxWidth: 12, font: { size: 10, family: 'Inter' } }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 10, family: 'Inter', weight: 'bold' } }
                },
                y: {
                    grid: { color: '#f1f5f9' },
                    ticks: { font: { size: 10, family: 'Inter' }, precision: 0 }
                }
            }
        }
    });
}

// Render Audit Logs with filtering
function renderAuditLogs(logs) {
    const tbody = document.getElementById("audit-table-body");
    tbody.innerHTML = "";

    if (!logs || logs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="p-8 text-center text-slate-400 font-sans">
                    No se encontraron transformaciones con los filtros seleccionados.
                </td>
            </tr>
        `;
        return;
    }

    const dimensionColors = {
        "Unicidad": "bg-amber-100 text-amber-800 border-amber-200",
        "Completitud": "bg-emerald-100 text-emerald-800 border-emerald-200",
        "Conformidad": "bg-blue-100 text-blue-800 border-blue-200",
        "Validez": "bg-rose-100 text-rose-800 border-rose-200",
        "Consistencia": "bg-purple-100 text-purple-800 border-purple-200"
    };

    logs.forEach(item => {
        const tr = document.createElement("tr");
        tr.className = "hover:bg-slate-50 transition border-b border-slate-100";
        const colorClass = dimensionColors[item.dimension] || "bg-slate-100 text-slate-800 border-slate-200";

        tr.innerHTML = `
            <td class="p-3 text-slate-400 whitespace-nowrap">${item.timestamp.split(" ")[1] || item.timestamp}</td>
            <td class="p-3 font-bold text-slate-800 capitalize">${item.dataset}</td>
            <td class="p-3">
                <span class="px-2 py-0.5 rounded text-[10px] font-semibold border ${colorClass}">
                    ${item.dimension}
                </span>
            </td>
            <td class="p-3 font-semibold text-slate-900">${item.rule}</td>
            <td class="p-3 text-slate-600 font-sans max-w-md">${item.description}</td>
            <td class="p-3 text-right font-bold text-blue-600">${item.affected_count.toLocaleString()}</td>
            <td class="p-3 text-slate-400 text-[11px] truncate max-w-xs">${item.sample_diff || "-"}</td>
        `;
        tbody.appendChild(tr);
    });
}

function filterAuditLogs() {
    if (!currentProcessResult || !currentProcessResult.audit_logs) return;

    const query = document.getElementById("filter-search").value.toLowerCase().trim();
    const dataset = document.getElementById("filter-dataset").value;
    const dimension = document.getElementById("filter-dimension").value;

    const filtered = currentProcessResult.audit_logs.filter(item => {
        const matchesQuery = !query || 
            item.rule.toLowerCase().includes(query) || 
            item.description.toLowerCase().includes(query) ||
            item.dataset.toLowerCase().includes(query);

        const matchesDs = !dataset || item.dataset === dataset;
        const matchesDim = !dimension || item.dimension === dimension;

        return matchesQuery && matchesDs && matchesDim;
    });

    renderAuditLogs(filtered);
}

// Render Preview Dataset Table
function renderPreviewDataset(datasetKey) {
    currentPreviewDataset = datasetKey;

    // Highlight button
    document.querySelectorAll(".prev-btn").forEach(btn => {
        if (btn.getAttribute("data-ds") === datasetKey) {
            btn.className = "prev-btn px-3 py-1.5 rounded-lg text-xs font-bold transition active bg-white shadow-sm text-blue-600";
        } else {
            btn.className = "prev-btn px-3 py-1.5 rounded-lg text-xs font-bold transition text-slate-600 hover:text-slate-900";
        }
    });

    const thead = document.getElementById("preview-table-head");
    const tbody = document.getElementById("preview-table-body");
    const label = document.getElementById("preview-stats-label");

    if (!currentProcessResult || !currentProcessResult.previews || !currentProcessResult.previews[datasetKey]) {
        thead.innerHTML = `<tr><th class="p-3">Sin datos</th></tr>`;
        tbody.innerHTML = `<tr><td class="p-8 text-center text-slate-400">Procese los archivos en la sección ETL para ver la vista previa.</td></tr>`;
        return;
    }

    const preview = currentProcessResult.previews[datasetKey];
    label.textContent = `Mostrando ${preview.rows.length} de ${preview.total_rows} filas limpias (${preview.total_cols} columnas)`;

    // Headers
    let headHtml = "<tr>";
    preview.columns.forEach(col => {
        headHtml += `<th class="p-3 whitespace-nowrap bg-slate-100">${col}</th>`;
    });
    headHtml += "</tr>";
    thead.innerHTML = headHtml;

    // Rows
    let bodyHtml = "";
    preview.rows.forEach(row => {
        bodyHtml += `<tr class="hover:bg-slate-50 transition border-b border-slate-100">`;
        preview.columns.forEach(col => {
            const val = row[col] !== undefined && row[col] !== null ? row[col] : "";
            bodyHtml += `<td class="p-3 font-mono text-slate-700 whitespace-nowrap">${val}</td>`;
        });
        bodyHtml += `</tr>`;
    });
    tbody.innerHTML = bodyHtml;
}

// Export Audit Log to JSON file
function exportAuditLogToJSON() {
    if (!currentProcessResult || !currentProcessResult.audit_logs) {
        alert("No hay registros de auditoría disponibles.");
        return;
    }
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentProcessResult.audit_logs, null, 2));
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", "Bitacora_Transformaciones_ETL.json");
    dlAnchor.click();
}

