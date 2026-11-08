import os
import uuid
import zipfile
from flask import Flask, render_template, request, jsonify, send_file
from io import BytesIO
from etl_engine import ETLProcessor, validate_uploaded_files, REQUIRED_KEYWORDS, identify_dataset_type
from excel_exporter import build_consolidated_clean_excel
from database_manager import save_clean_data_to_db, get_db_stats, DB_FILE

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB límite

# Almacén en memoria de resultados procesados por sesión
PROCESSED_SESSIONS = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/validate-files', methods=['POST'])
def api_validate_files():
    data = request.get_json() or {}
    filenames = data.get('filenames', [])
    is_valid, mapping, missing, unrecognized = validate_uploaded_files(filenames)
    return jsonify({
        "isValid": is_valid,
        "mapping": mapping,
        "missing": missing,
        "unrecognized": unrecognized,
        "required": REQUIRED_KEYWORDS
    })

@app.route('/api/process-etl', methods=['POST'])
def api_process_etl():
    uploaded_files = request.files.getlist('files')
    if not uploaded_files or len(uploaded_files) == 0:
        return jsonify({"error": "No se recibieron archivos para procesar."}), 400

    filenames = [f.filename for f in uploaded_files]
    is_valid, mapping, missing, unrecognized = validate_uploaded_files(filenames)

    if not is_valid:
        return jsonify({
            "error": f"Faltan archivos requeridos que contengan los siguientes nombres: {', '.join(missing)}",
            "missing": missing,
            "unrecognized": unrecognized,
            "mapping": mapping
        }), 400

    # Construir diccionario de archivos en memoria
    file_dict = {}
    for f in uploaded_files:
        dtype = identify_dataset_type(f.filename)
        if dtype and dtype not in file_dict:
            file_dict[dtype] = (f.read(), f.filename)

    try:
        processor = ETLProcessor()
        cleaned_dict, tracker, metrics = processor.process_all(file_dict)
        
        # Generar Excel en memoria
        excel_bytes = build_consolidated_clean_excel(cleaned_dict, tracker, metrics)
        session_id = str(uuid.uuid4())
        
        # Guardar en caché para descarga
        PROCESSED_SESSIONS[session_id] = {
            "excel_bytes": excel_bytes,
            "filename": "Datos_Limpios_Consolidados_ETL.xlsx"
        }

        # Guardar automáticamente en Base de Datos SQLite (borra lo anterior y guarda lo nuevo)
        db_result = save_clean_data_to_db(cleaned_dict, tracker.logs)

        # Preparar muestras de datos limpios para previsualización web (primeras 10 filas de c/u)
        previews = {}
        for ds_name, df in cleaned_dict.items():
            previews[ds_name] = {
                "columns": list(df.columns),
                "rows": df.head(15).fillna("").to_dict(orient="records"),
                "total_rows": len(df),
                "total_cols": len(df.columns)
            }

        return jsonify({
            "success": True,
            "session_id": session_id,
            "metrics": metrics,
            "dataset_summaries": tracker.summary_by_dataset,
            "audit_logs": tracker.logs,
            "previews": previews,
            "db_result": db_result,
            "download_url": f"/api/download-clean-excel/{session_id}",
            "db_download_url": "/api/download-db"
        })

    except Exception as e:
        return jsonify({"error": f"Error durante la ejecución del ETL: {str(e)}"}), 500

@app.route('/api/load-sample-data', methods=['POST'])
def api_load_sample_data():
    """Carga los 5 archivos de prueba preconfigurados en sample_data/."""
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_data")
    if not os.path.exists(sample_dir):
        from generate_sample_data import generate_samples
        generate_samples()

    sample_files = [
        "admisiones_2024.csv",
        "bienestar_estudiantil.csv",
        "pagos_semestre.xlsx",
        "moodle_actividad.csv",
        "matriculas_consolidadas.xlsx"
    ]

    file_dict = {}
    for fname in sample_files:
        kw = identify_dataset_type(fname)
        fpath = os.path.join(sample_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "rb") as f:
                file_dict[kw] = (f.read(), fname)

    try:
        processor = ETLProcessor()
        cleaned_dict, tracker, metrics = processor.process_all(file_dict)
        excel_bytes = build_consolidated_clean_excel(cleaned_dict, tracker, metrics)
        
        session_id = str(uuid.uuid4())
        PROCESSED_SESSIONS[session_id] = {
            "excel_bytes": excel_bytes,
            "filename": "Datos_Limpios_Consolidados_ETL.xlsx"
        }

        # Guardar automáticamente en Base de Datos SQLite (borra lo anterior y guarda lo nuevo)
        db_result = save_clean_data_to_db(cleaned_dict, tracker.logs)

        previews = {}
        for ds_name, df in cleaned_dict.items():
            previews[ds_name] = {
                "columns": list(df.columns),
                "rows": df.head(15).fillna("").to_dict(orient="records"),
                "total_rows": len(df),
                "total_cols": len(df.columns)
            }

        return jsonify({
            "success": True,
            "session_id": session_id,
            "metrics": metrics,
            "dataset_summaries": tracker.summary_by_dataset,
            "audit_logs": tracker.logs,
            "previews": previews,
            "sample_files": sample_files,
            "db_result": db_result,
            "download_url": f"/api/download-clean-excel/{session_id}",
            "db_download_url": "/api/download-db"
        })
    except Exception as e:
        return jsonify({"error": f"Error al procesar muestras: {str(e)}"}), 500

@app.route('/api/download-clean-excel/<session_id>')
def api_download_clean_excel(session_id):
    if session_id not in PROCESSED_SESSIONS:
        return "El archivo solicitado ya no está disponible o la sesión expiró. Por favor vuelva a procesar.", 404
    
    item = PROCESSED_SESSIONS[session_id]
    return send_file(
        BytesIO(item["excel_bytes"]),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=item["filename"]
    )

@app.route('/api/download-samples-zip')
def api_download_samples_zip():
    """Genera y descarga un archivo .zip con los 5 archivos de prueba sucios."""
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_data")
    if not os.path.exists(sample_dir):
        from generate_sample_data import generate_samples
        generate_samples()

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, files in os.walk(sample_dir):
            for file in files:
                if file.endswith(('.csv', '.xlsx', '.xls')) and not file.startswith('Prueba_ETL'):
                    file_path = os.path.join(root, file)
                    zip_file.write(file_path, arcname=file)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="Archivos_Ejemplo_ETL.zip"
    )

@app.route('/api/download-db')
def api_download_db():
    """Descarga la base de datos SQLite 'etl_warehouse.db' con todos los datos limpios."""
    if not os.path.exists(DB_FILE):
        return "Base de datos no inicializada. Procese el ETL primero.", 404
    return send_file(
        DB_FILE,
        mimetype="application/x-sqlite3",
        as_attachment=True,
        download_name="etl_warehouse.db"
    )

@app.route('/api/db/tables')
def api_db_tables():
    """Retorna la lista de tablas disponibles en la BD con sus conteos de filas."""
    if not os.path.exists(DB_FILE):
        return jsonify({"error": "Base de datos no inicializada. Procese el ETL primero."}), 404
    stats = get_db_stats()
    return jsonify({"tables": stats})

@app.route('/api/db/query')
def api_db_query():
    """
    Consulta una tabla con búsqueda y paginación.
    Params: table, search (opcional), page (default 1), per_page (default 20)
    """
    import sqlite3
    table = request.args.get('table', 'admisiones')
    search = request.args.get('search', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(100, max(5, int(request.args.get('per_page', 20))))

    allowed_tables = ['admisiones', 'bienestar', 'pagos', 'moodle', 'matriculas', 'auditoria_transformaciones']
    if table not in allowed_tables:
        return jsonify({"error": f"Tabla '{table}' no permitida."}), 400

    if not os.path.exists(DB_FILE):
        return jsonify({"error": "Base de datos no inicializada. Procese el ETL primero."}), 404

    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA table_info({table})")
        columns_info = cursor.fetchall()
        columns = [col['name'] for col in columns_info]

        if not columns:
            conn.close()
            return jsonify({"error": f"Tabla '{table}' vacía o no encontrada."}), 404

        offset = (page - 1) * per_page
        if search:
            where_clauses = [f"CAST({col} AS TEXT) LIKE ?" for col in columns]
            where_sql = " OR ".join(where_clauses)
            params_search = [f"%{search}%"] * len(columns)
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {where_sql}", params_search)
            total = cursor.fetchone()[0]
            cursor.execute(f"SELECT * FROM {table} WHERE {where_sql} LIMIT ? OFFSET ?",
                           params_search + [per_page, offset])
        else:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            total = cursor.fetchone()[0]
            cursor.execute(f"SELECT * FROM {table} LIMIT ? OFFSET ?", [per_page, offset])

        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()

        total_pages = max(1, (total + per_page - 1) // per_page)
        return jsonify({
            "table": table,
            "columns": columns,
            "rows": rows,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "search": search
        })
    except Exception as e:
        return jsonify({"error": f"Error al consultar BD: {str(e)}"}), 500

@app.route('/api/bi/cohort-dashboard')
def api_bi_cohort_dashboard():
    """
    Retorna el tablero analítico de la cohorte con absorción, retención, deserción,
    promedio de cohorte, alertados, precisión y cobertura de alerta con semáforos,
    admitiendo filtros de programa, facultad y estrato.
    """
    if not os.path.exists(DB_FILE):
        return jsonify({"error": "Base de datos no inicializada. Procese el ETL primero."}), 404

    filter_programa = request.args.get('programa', 'TODOS').strip()
    filter_facultad = request.args.get('facultad', 'TODAS').strip()
    filter_estrato = request.args.get('estrato', 'TODOS').strip()

    try:
        from bi_dashboard_manager import get_bi_cohort_dashboard
        dashboard_data = get_bi_cohort_dashboard(
            db_path=DB_FILE,
            filter_programa=filter_programa,
            filter_facultad=filter_facultad,
            filter_estrato=filter_estrato
        )
        return jsonify(dashboard_data)
    except Exception as e:
        return jsonify({"error": f"Error al calcular indicadores del tablero BI: {str(e)}"}), 500

@app.route('/api/bi/drilldown')
def api_bi_drilldown():
    """
    Retorna la lista de registros individuales (estudiantes) que sustentan el cálculo
    de la métrica clickeada (drilldown).
    Params: metrica, programa, facultad, estrato
    """
    if not os.path.exists(DB_FILE):
        return jsonify({"error": "Base de datos no inicializada. Procese el ETL primero."}), 404

    metrica = request.args.get('metrica', 'retencion').strip()
    filter_programa = request.args.get('programa', 'TODOS').strip()
    filter_facultad = request.args.get('facultad', 'TODAS').strip()
    filter_estrato = request.args.get('estrato', 'TODOS').strip()

    try:
        from bi_dashboard_manager import get_bi_drilldown
        drilldown_data = get_bi_drilldown(
            db_path=DB_FILE,
            metrica=metrica,
            filter_programa=filter_programa,
            filter_facultad=filter_facultad,
            filter_estrato=filter_estrato
        )
        return jsonify(drilldown_data)
    except Exception as e:
        return jsonify({"error": f"Error al consultar detalle drilldown: {str(e)}"}), 500

@app.route('/api/bi/improved-alert', methods=['GET'])
def api_bi_improved_alert():
    """Retorna las métricas comparativas y la matriz de confusión de la nueva regla de alerta mejorada."""
    if not os.path.exists(DB_FILE):
        return jsonify({"error": "Base de datos no inicializada. Procese el ETL primero."}), 404

    try:
        from bi_dashboard_manager import compute_improved_alert_metrics
        res = compute_improved_alert_metrics(db_path=DB_FILE)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": f"Error al calcular regla mejorada: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print(f"Iniciando Servidor Web ETL en http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)

