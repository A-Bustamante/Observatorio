import os
import sqlite3
import pandas as pd

DB_FILE = os.path.join(os.path.dirname(__file__), "etl_warehouse.db")

def save_clean_data_to_db(cleaned_dict: dict, audit_logs: list = None) -> dict:
    """
    Guarda los datos limpios de los 5 archivos en la base de datos SQLite 'etl_warehouse.db'.
    Cada vez que se procesa el ETL, purga / borra completamente las tablas anteriores
    y guarda la nueva información limpia.
    """
    # Conexión a la base de datos SQLite
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    stats = {}
    tables_saved = []

    # Mapeo de nombres de tablas estándar en la base de datos
    table_names = {
        "admisiones": "admisiones",
        "bienestar": "bienestar",
        "pagos": "pagos",
        "moodle": "moodle",
        "matriculas": "matriculas"
    }

    try:
        # 1. Borrar y recrear las tablas con los datos limpios
        for ds_key, table_name in table_names.items():
            if ds_key in cleaned_dict:
                df = cleaned_dict[ds_key]
                # Borrar tabla anterior si existía
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                # Guardar nuevo DataFrame limpio en la BD
                df.to_sql(table_name, con=conn, if_exists="replace", index=False)
                count = len(df)
                stats[table_name] = count
                tables_saved.append(table_name)

        # 2. Guardar también la bitácora de auditoría de transformaciones en la BD
        if audit_logs:
            cursor.execute("DROP TABLE IF EXISTS auditoria_transformaciones")
            df_audit = pd.DataFrame(audit_logs)
            df_audit.to_sql("auditoria_transformaciones", con=conn, if_exists="replace", index=False)
            stats["auditoria_transformaciones"] = len(df_audit)

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    return {
        "db_file": DB_FILE,
        "tables_saved": tables_saved,
        "stats": stats
    }

def get_db_stats() -> dict:
    """Obtiene el conteo actual de registros por tabla en la base de datos SQLite."""
    if not os.path.exists(DB_FILE):
        return {}
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    counts = {}
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        counts[t] = cursor.fetchone()[0]
    
    conn.close()
    return counts

