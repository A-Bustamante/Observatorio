// ===================== BASE DE DATOS INTERACTIVA =====================
let dbCurrentPage = 1;
let dbCurrentTotal = 0;
let dbCurrentTotalPages = 1;
let dbSearchDebounceTimer = null;

function debouncedDbSearch() {
    clearTimeout(dbSearchDebounceTimer);
    dbSearchDebounceTimer = setTimeout(() => {
        dbCurrentPage = 1;
        loadDatabaseTable();
    }, 350);
}

function dbChangePage(delta) {
    const newPage = dbCurrentPage + delta;
    if (newPage >= 1 && newPage <= dbCurrentTotalPages) {
        dbCurrentPage = newPage;
        loadDatabaseTable(false);
    }
}

async function loadDatabaseTable(resetPage = true) {
    if (resetPage) dbCurrentPage = 1;

    const tableSelect = document.getElementById('db-table-select');
    const searchInput = document.getElementById('db-search-input');
    const statsLabel = document.getElementById('db-stats-label');
    const tableHead = document.getElementById('db-table-head');
    const tableBody = document.getElementById('db-table-body');

    if (!tableSelect) return;
    const table = tableSelect.value;
    const search = searchInput ? searchInput.value.trim() : '';

    statsLabel.textContent = 'Cargando...';
    tableHead.innerHTML = '<tr><th class="p-3 text-slate-400 font-sans font-normal">Cargando tabla...</th></tr>';
    tableBody.innerHTML = '<tr><td class="p-6 text-center"><div class="animate-spin inline-block w-5 h-5 border-2 border-purple-500 border-t-transparent rounded-full"></div></td></tr>';

    try {
        const params = new URLSearchParams({ table, page: dbCurrentPage, per_page: 20 });
        if (search) params.set('search', search);

        const resp = await fetch(`/api/db/query?${params}`);
        if (!resp.ok) {
            const err = await resp.json();
            tableHead.innerHTML = '<tr><th class="p-3">Error</th></tr>';
            tableBody.innerHTML = `<tr><td class="p-8 text-center text-rose-500 font-sans">${err.error || 'Error al cargar datos. Procese el ETL primero.'}</td></tr>`;
            statsLabel.textContent = 'Error al consultar.';
            return;
        }

        const data = await resp.json();
        dbCurrentTotal = data.total;
        dbCurrentTotalPages = data.total_pages;

        // Render headers
        const headerRow = data.columns.map(col =>
            `<th class="p-3 whitespace-nowrap">${col}</th>`
        ).join('');
        tableHead.innerHTML = `<tr>${headerRow}</tr>`;

        // Render rows
        if (data.rows.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="${data.columns.length}" class="p-8 text-center text-slate-400 font-sans">No se encontraron registros${search ? ' para "' + search + '"' : ''}.</td></tr>`;
        } else {
            tableBody.innerHTML = data.rows.map(row => {
                const cells = data.columns.map(col => {
                    const val = (row[col] !== null && row[col] !== undefined) ? String(row[col]) : '';
                    const escaped = val.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
                    return `<td class="p-2.5 max-w-[200px] truncate" title="${escaped}">${val || '<span class="text-slate-300 italic">—</span>'}</td>`;
                }).join('');
                return `<tr class="hover:bg-slate-50 transition">${cells}</tr>`;
            }).join('');
        }

        // Update stats label
        const start = (dbCurrentPage - 1) * 20 + 1;
        const end = Math.min(dbCurrentPage * 20, dbCurrentTotal);
        const displayEnd = dbCurrentTotal === 0 ? 0 : end;
        statsLabel.textContent = `Mostrando ${dbCurrentTotal === 0 ? 0 : start}–${displayEnd} de ${dbCurrentTotal} registros en "${data.table}"${search ? ' (búsqueda activa)' : ''}`;

        // Pagination controls
        document.getElementById('db-page-info').textContent = `Página ${dbCurrentPage} de ${dbCurrentTotalPages}`;
        document.getElementById('db-prev-btn').disabled = dbCurrentPage <= 1;
        document.getElementById('db-next-btn').disabled = dbCurrentPage >= dbCurrentTotalPages;

    } catch (err) {
        tableHead.innerHTML = '<tr><th class="p-3">Error</th></tr>';
        tableBody.innerHTML = `<tr><td class="p-8 text-center text-rose-500 font-sans">Error de conexión: ${err.message}</td></tr>`;
        statsLabel.textContent = 'Error de conexión.';
    }
}

async function loadDbStats() {
    const statsCards = document.getElementById('db-stats-cards');
    statsCards.classList.remove('hidden');
    statsCards.innerHTML = '<div class="col-span-6 text-xs text-slate-400 p-3">Cargando estadísticas...</div>';

    try {
        const resp = await fetch('/api/db/tables');
        if (!resp.ok) {
            statsCards.innerHTML = '<div class="col-span-6 text-xs text-rose-500 p-3">Error al cargar estadísticas. Procese el ETL primero.</div>';
            return;
        }
        const data = await resp.json();
        const tables = data.tables || {};
        const colorMap = {
            admisiones: 'blue',
            bienestar: 'emerald',
            pagos: 'amber',
            moodle: 'indigo',
            matriculas: 'cyan',
            auditoria_transformaciones: 'rose'
        };
        const labelMap = {
            admisiones: 'Admisiones',
            bienestar: 'Bienestar',
            pagos: 'Pagos',
            moodle: 'Moodle',
            matriculas: 'Matrículas',
            auditoria_transformaciones: 'Auditoría'
        };
        const colorClasses = {
            blue:    { border: 'border-blue-100',    bg: 'bg-blue-50',    title: 'text-blue-700',   val: 'text-blue-800',   sub: 'text-blue-500',   hover: 'hover:border-blue-300'   },
            emerald: { border: 'border-emerald-100', bg: 'bg-emerald-50', title: 'text-emerald-700',val: 'text-emerald-800',sub: 'text-emerald-500', hover: 'hover:border-emerald-300' },
            amber:   { border: 'border-amber-100',   bg: 'bg-amber-50',   title: 'text-amber-700',  val: 'text-amber-800',  sub: 'text-amber-500',  hover: 'hover:border-amber-300'   },
            indigo:  { border: 'border-indigo-100',  bg: 'bg-indigo-50',  title: 'text-indigo-700', val: 'text-indigo-800', sub: 'text-indigo-500', hover: 'hover:border-indigo-300'  },
            cyan:    { border: 'border-cyan-100',    bg: 'bg-cyan-50',    title: 'text-cyan-700',   val: 'text-cyan-800',   sub: 'text-cyan-500',   hover: 'hover:border-cyan-300'    },
            rose:    { border: 'border-rose-100',    bg: 'bg-rose-50',    title: 'text-rose-700',   val: 'text-rose-800',   sub: 'text-rose-500',   hover: 'hover:border-rose-300'    }
        };

        statsCards.innerHTML = Object.entries(tables).map(([tbl, count]) => {
            const color = colorMap[tbl] || 'slate';
            const cls = colorClasses[color] || colorClasses.blue;
            const label = labelMap[tbl] || tbl;
            return `<div class="p-3 rounded-xl border ${cls.border} ${cls.bg} text-center cursor-pointer ${cls.hover} transition"
                         onclick="document.getElementById('db-table-select').value='${tbl}'; loadDatabaseTable();">
                <p class="text-[11px] font-semibold ${cls.title}">${label}</p>
                <p class="text-xl font-extrabold ${cls.val} mt-0.5">${count}</p>
                <p class="text-[10px] ${cls.sub}">registros</p>
            </div>`;
        }).join('');
    } catch (e) {
        statsCards.innerHTML = '<div class="col-span-6 text-xs text-rose-500 p-3">Error de conexión.</div>';
    }
}

