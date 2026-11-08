import os
import sqlite3
import pandas as pd
import numpy as np

FACULTAD_MAPPING = {
    "Ingeniería Industrial": "Facultad de Ingeniería",
    "Ingeniería Informática": "Facultad de Ingeniería",
    "Ingeniería de Sistemas": "Facultad de Ingeniería",
    "Ingeniería Civil": "Facultad de Ingeniería",
    "Administración de Empresas": "Facultad de Ciencias Económicas y Administrativas",
    "Contaduría Pública": "Facultad de Ciencias Económicas y Administrativas",
    "Psicología": "Facultad de Ciencias Sociales y Humanas",
    "Trabajo Social": "Facultad de Ciencias Sociales y Humanas",
    "Comunicación Social": "Facultad de Ciencias Sociales y Humanas",
    "Derecho": "Facultad de Ciencias Sociales y Humanas",
    "Medicina": "Facultad de Ciencias de la Salud",
    "Diseño Gráfico": "Facultad de Artes y Diseño"
}

# Metas institucionales y rangos de semáforo (Verde, Amarillo, Rojo)
METAS_CONFIG = {
    "absorcion": {
        "meta": 80.0,
        "unidad": "%",
        "descripcion": "Estudiantes de la cohorte 2025-1 ÷ admitidos únicos.",
        "eval": lambda val: "verde" if val >= 80.0 else ("amarillo" if val >= 70.0 else "rojo")
    },
    "retencion": {
        "meta": 82.0,
        "unidad": "%",
        "descripcion": "Estudiantes matriculados y con pago 'Pagado' en 2025-2 ÷ estudiantes cohorte 2025-1.",
        "eval": lambda val: "verde" if val >= 82.0 else ("amarillo" if val >= 72.0 else "rojo")
    },
    "desercion": {
        "meta": 18.0,
        "unidad": "%",
        "descripcion": "100% - Retención (Tasa de abandono o matrícula no pagada al primer período).",
        "eval": lambda val: "verde" if val <= 18.0 else ("amarillo" if val <= 25.0 else "rojo")
    },
    "promedio_cohorte": {
        "meta": 3.60,
        "unidad": "/ 5.0",
        "descripcion": "Promedio acumulado de calificaciones de la cohorte.",
        "eval": lambda val: "verde" if val >= 3.60 else ("amarillo" if val >= 3.20 else "rojo")
    },
    "precision_alerta": {
        "meta": 40.0,
        "unidad": "%",
        "descripcion": "Alertados que desertaron ÷ Total de alertados.",
        "eval": lambda val: "verde" if val >= 40.0 else ("amarillo" if val >= 30.0 else "rojo")
    },
    "cobertura_alerta": {
        "meta": 65.0,
        "unidad": "%",
        "descripcion": "Alertados que desertaron ÷ Total de desertores reales.",
        "eval": lambda val: "verde" if val >= 65.0 else ("amarillo" if val >= 50.0 else "rojo")
    }
}

def load_cohort_base_dataframe(conn):
    """
    Carga y cruza la base de datos completa de la cohorte 2025-1 con pagos y alertas tempranas.
    Aplica la regla de negocio: 'matriculado en 2025-2 requiere haber pagado (estado_pago = Pagado)'.
    """
    # 1. Admitidos
    df_adm = pd.read_sql("""
        SELECT DISTINCT documento_identidad, nombre_completo, programa_academico, estrato 
        FROM admisiones
    """, conn)
    df_adm["facultad"] = df_adm["programa_academico"].map(lambda p: FACULTAD_MAPPING.get(p, "Otras Facultades"))

    # 2. Matriculas 2025-1 (Cohorte inicial)
    df_mat1 = pd.read_sql("""
        SELECT codigo, documento, correo_institucional, programa, tipo_ingreso, creditos, promedio_periodo 
        FROM matriculas 
        WHERE periodo = '2025-1'
    """, conn)
    
    # Conversión robusta de promedio_periodo
    def safe_num(v):
        if pd.isna(v) or v is None:
            return np.nan
        try:
            s = str(v).replace(',', '.')
            val = float(s)
            if 5.0 < val <= 50.0:
                val = val / 10.0
            elif 50.0 < val <= 100.0:
                val = val / 20.0
            return max(0.0, min(5.0, round(val, 2)))
        except Exception:
            return np.nan

    df_mat1["promedio_num"] = df_mat1["promedio_periodo"].apply(safe_num)
    df_mat1["facultad"] = df_mat1["programa"].map(lambda p: FACULTAD_MAPPING.get(p, "Otras Facultades"))

    # Cruce de datos de admisiones (nombre y estrato)
    adm_subset = df_adm[["documento_identidad", "nombre_completo", "estrato"]].drop_duplicates(subset=["documento_identidad"])
    df_mat1 = df_mat1.merge(adm_subset, left_on="documento", right_on="documento_identidad", how="left")
    df_mat1["nombre_completo"] = df_mat1["nombre_completo"].fillna("Estudiante " + df_mat1["codigo"].astype(str))

    # 3. Matriculas y Pagos en 2025-2
    # REGLA DEL USUARIO: "cuando hablan de matriculados se refieren a que también hayan pagado"
    df_pagos_2 = pd.read_sql("""
        SELECT documento, estado_pago 
        FROM pagos 
        WHERE periodo = '2025-2'
    """, conn)
    # Diccionario de pagos en 2025-2
    pagos_map = {}
    for _, r in df_pagos_2.iterrows():
        doc = str(r["documento"]).strip()
        pagos_map[doc] = str(r["estado_pago"]).strip()

    df_mat2 = pd.read_sql("SELECT DISTINCT documento FROM matriculas WHERE periodo = '2025-2'", conn)
    matriculados_2025_2 = set(str(d).strip() for d in df_mat2["documento"].dropna())

    # Determinar estado de retención y pago en 2025-2
    estado_pago_list = []
    retenido_list = []

    for doc in df_mat1["documento"].astype(str):
        doc_clean = doc.strip()
        is_enrolled_2 = doc_clean in matriculados_2025_2
        payment_status = pagos_map.get(doc_clean, "Sin Registro")

        estado_pago_list.append(payment_status if is_enrolled_2 else "No Renovó Matrícula")
        
        # Está retenido si y solo si está en matriculas 2025-2 Y su pago está aprobado/pagado
        is_paid = (payment_status.lower() in ["pagado", "aprobada", "aprobado"])
        retenido_list.append(is_enrolled_2 and is_paid)

    df_mat1["estado_pago_2025_2"] = estado_pago_list
    df_mat1["retenido"] = retenido_list
    df_mat1["deserto"] = ~df_mat1["retenido"]

    # 4. Moodle - Alertas tempranas
    # Asignar clave única con ocurrencia para manejar emails compartidos entre estudiantes
    df_mat1['moodle_join_key'] = df_mat1['correo_institucional'] + "_" + df_mat1.groupby('correo_institucional').cumcount().astype(str)

    # Extraer directamente de Moodle las semanas 4, 7 y 8
    try:
        df_moodle = pd.read_sql("""
            SELECT correo, semana, CAST(accesos AS INT) as accesos, CAST(nota_parcial_0_100 AS FLOAT) as nota 
            FROM moodle 
            WHERE semana IN (4, 7, 8)
        """, conn)
    except Exception:
        df_moodle = pd.DataFrame(columns=['correo', 'semana', 'accesos', 'nota'])

    if not df_moodle.empty and 'semana' in df_moodle.columns:
        df_moodle['occ'] = df_moodle.groupby(['correo', 'semana']).cumcount()
        df_moodle['join_key'] = df_moodle['correo'] + "_" + df_moodle['occ'].astype(str)

        piv_notas = df_moodle.pivot(index='join_key', columns='semana', values='nota')
        piv_accesos = df_moodle.pivot(index='join_key', columns='semana', values='accesos')

        moodle_stats = pd.DataFrame(index=df_moodle['join_key'].unique())
        nota4 = (piv_notas[4] / 20.0) if 4 in piv_notas.columns else np.nan
        nota8 = (piv_notas[8] / 20.0) if 8 in piv_notas.columns else np.nan
        
        # Promedio parcial de notas en semanas 4 y 8 (convertido a escala 0.0 a 5.0)
        moodle_stats['prom_parcial_moodle'] = ((nota4.fillna(0) + nota8.fillna(0)) / 2.0).round(2)
        
        # Accesos sumando semanas 7 y 8
        acc7 = piv_accesos[7].fillna(0) if 7 in piv_accesos.columns else 0
        acc8 = piv_accesos[8].fillna(0) if 8 in piv_accesos.columns else 0
        moodle_stats['accesos_sem7_8_moodle'] = (acc7 + acc8).astype(int)

        # Regla institucional: promedio semanas 4 y 8 < 3.0 O accesos semanas 7 y 8 == 0
        cond_nota = moodle_stats['prom_parcial_moodle'] < 3.0
        cond_acc = moodle_stats['accesos_sem7_8_moodle'] == 0
        moodle_stats['alertado'] = cond_nota | cond_acc

        motivos = []
        for idx in moodle_stats.index:
            cn = cond_nota.get(idx, False)
            ca = cond_acc.get(idx, False)
            pr = moodle_stats.loc[idx, 'prom_parcial_moodle']
            ac = moodle_stats.loc[idx, 'accesos_sem7_8_moodle']
            if cn and ca:
                motivos.append(f"Bajo rendimiento LMS ({pr:.2f} < 3.0) y Cero accesos sem. 7-8")
            elif cn:
                motivos.append(f"Bajo rendimiento LMS sem 4 y 8 ({pr:.2f} < 3.0)")
            elif ca:
                motivos.append(f"Cero accesos LMS sem. 7-8 (0 ingresos)")
            else:
                motivos.append("Sin alerta LMS (Rendimiento adecuado)")
        moodle_stats['motivo_alerta'] = motivos

        df_mat1 = df_mat1.merge(moodle_stats[['prom_parcial_moodle', 'accesos_sem7_8_moodle', 'alertado', 'motivo_alerta']], 
                                left_on='moodle_join_key', right_index=True, how='left')
    else:
        df_mat1['prom_parcial_moodle'] = 0.0
        df_mat1['accesos_sem7_8_moodle'] = 0
        df_mat1['alertado'] = False
        df_mat1['motivo_alerta'] = "Sin datos Moodle"

    df_mat1['alertado'] = df_mat1['alertado'].fillna(False)
    df_mat1['motivo_alerta'] = df_mat1['motivo_alerta'].fillna("Sin alerta")
    df_mat1['prom_parcial_moodle'] = df_mat1['prom_parcial_moodle'].fillna(0.0)
    df_mat1['accesos_sem7_8_moodle'] = df_mat1['accesos_sem7_8_moodle'].fillna(0).astype(int)

    return df_adm, df_mat1

def get_bi_cohort_dashboard(db_path='etl_warehouse.db', filter_programa=None, filter_facultad=None, filter_estrato=None):
    """Calcula métricas y KPIs para el tablero principal."""
    conn = sqlite3.connect(db_path)
    df_adm, df_mat1 = load_cohort_base_dataframe(conn)
    conn.close()

    # Listas de filtros globales
    programas_disponibles = sorted([p for p in df_mat1["programa"].dropna().unique().tolist() if p])
    facultades_disponibles = sorted(list(set(FACULTAD_MAPPING.get(p, "Otras Facultades") for p in programas_disponibles)))
    estratos_disponibles = sorted([int(e) for e in df_adm["estrato"].dropna().unique().tolist() if str(e).isdigit()])

    # APLICACIÓN DE FILTROS DINÁMICOS
    df_adm_fil = df_adm.copy()
    df_mat_fil = df_mat1.copy()

    if filter_facultad and filter_facultad != "TODAS":
        df_adm_fil = df_adm_fil[df_adm_fil["facultad"] == filter_facultad]
        df_mat_fil = df_mat_fil[df_mat_fil["facultad"] == filter_facultad]

    if filter_programa and filter_programa != "TODOS":
        df_adm_fil = df_adm_fil[df_adm_fil["programa_academico"] == filter_programa]
        df_mat_fil = df_mat_fil[df_mat_fil["programa"] == filter_programa]

    if filter_estrato and str(filter_estrato) != "TODOS":
        try:
            est_val = int(filter_estrato)
            df_adm_fil = df_adm_fil[df_adm_fil["estrato"] == est_val]
            df_mat_fil = df_mat_fil[df_mat_fil["estrato"] == est_val]
        except (ValueError, TypeError):
            pass

    # CÁLCULO DE KPIS
    total_admitidos = int(len(df_adm_fil))
    total_cohorte = int(len(df_mat_fil))
    
    # Absorción: Cohorte 2025-1 ÷ Admitidos únicos
    absorcion_pct = round((total_cohorte / max(1, total_admitidos)) * 100.0, 2) if total_admitidos > 0 else 0.0
    
    # Retención y Deserción considerando pago efectivo
    total_retenidos = int(df_mat_fil["retenido"].sum())
    total_desertores = int(df_mat_fil["deserto"].sum())
    
    retencion_pct = round((total_retenidos / max(1, total_cohorte)) * 100.0, 2) if total_cohorte > 0 else 0.0
    desercion_pct = round(100.0 - retencion_pct, 2) if total_cohorte > 0 else 0.0
    
    promedio_cohorte = round(float(df_mat_fil["promedio_num"].mean()), 2) if total_cohorte > 0 and pd.notna(df_mat_fil["promedio_num"].mean()) else 0.0
    
    # Alerta temprana:
    total_alertados = int(df_mat_fil["alertado"].sum())
    alertados_que_desertaron = int((df_mat_fil["alertado"] & df_mat_fil["deserto"]).sum())
    alertados_que_retuvieron = total_alertados - alertados_que_desertaron
    no_alertados_que_desertaron = total_desertores - alertados_que_desertaron
    no_alertados_que_retuvieron = total_retenidos - alertados_que_retuvieron
    
    precision_pct = round((alertados_que_desertaron / max(1, total_alertados)) * 100.0, 2) if total_alertados > 0 else 0.0
    cobertura_pct = round((alertados_que_desertaron / max(1, total_desertores)) * 100.0, 2) if total_desertores > 0 else 0.0

    kpis = {
        "absorcion": {
            "nombre": "Absorción",
            "valor": absorcion_pct,
            "unidad": "%",
            "numerador": total_cohorte,
            "denominador": total_admitidos,
            "meta": METAS_CONFIG["absorcion"]["meta"],
            "semaforo": METAS_CONFIG["absorcion"]["eval"](absorcion_pct),
            "formula": METAS_CONFIG["absorcion"]["descripcion"],
            "id_metrica": "absorcion"
        },
        "retencion": {
            "nombre": "Retención de 1er Período (Matriculados & Pagados)",
            "valor": retencion_pct,
            "unidad": "%",
            "numerador": total_retenidos,
            "denominador": total_cohorte,
            "meta": METAS_CONFIG["retencion"]["meta"],
            "semaforo": METAS_CONFIG["retencion"]["eval"](retencion_pct),
            "formula": METAS_CONFIG["retencion"]["descripcion"],
            "id_metrica": "retencion"
        },
        "desercion": {
            "nombre": "Deserción de 1er Período (Sin Matrícula o Sin Pago)",
            "valor": desercion_pct,
            "unidad": "%",
            "numerador": total_desertores,
            "denominador": total_cohorte,
            "meta": METAS_CONFIG["desercion"]["meta"],
            "semaforo": METAS_CONFIG["desercion"]["eval"](desercion_pct),
            "formula": METAS_CONFIG["desercion"]["descripcion"],
            "id_metrica": "desercion"
        },
        "promedio_cohorte": {
            "nombre": "Promedio de la Cohorte",
            "valor": promedio_cohorte,
            "unidad": "/ 5.0",
            "meta": METAS_CONFIG["promedio_cohorte"]["meta"],
            "semaforo": METAS_CONFIG["promedio_cohorte"]["eval"](promedio_cohorte),
            "formula": METAS_CONFIG["promedio_cohorte"]["descripcion"],
            "id_metrica": "promedio"
        },
        "alertados": {
            "nombre": "Número de Alertados",
            "valor": total_alertados,
            "unidad": "estudiantes",
            "total_cohorte": total_cohorte,
            "tasa_alertados": round((total_alertados / max(1, total_cohorte)) * 100.0, 1),
            "semaforo": "verde" if total_alertados > 0 else "amarillo",
            "formula": "Nota parcial semanas 4 y 8 < 3.0 o 0 accesos en semanas 7 y 8.",
            "id_metrica": "alertados"
        },
        "precision_alerta": {
            "nombre": "Precisión de la Alerta",
            "valor": precision_pct,
            "unidad": "%",
            "numerador": alertados_que_desertaron,
            "denominador": total_alertados,
            "meta": METAS_CONFIG["precision_alerta"]["meta"],
            "semaforo": METAS_CONFIG["precision_alerta"]["eval"](precision_pct),
            "formula": METAS_CONFIG["precision_alerta"]["descripcion"],
            "id_metrica": "precision"
        },
        "cobertura_alerta": {
            "nombre": "Cobertura de la Alerta",
            "valor": cobertura_pct,
            "unidad": "%",
            "numerador": alertados_que_desertaron,
            "denominador": total_desertores,
            "meta": METAS_CONFIG["cobertura_alerta"]["meta"],
            "semaforo": METAS_CONFIG["cobertura_alerta"]["eval"](cobertura_pct),
            "formula": METAS_CONFIG["cobertura_alerta"]["descripcion"],
            "id_metrica": "cobertura"
        }
    }

    # DESGLOSE POR PROGRAMA
    desglose = []
    if len(df_mat_fil) > 0:
        prog_grouped = df_mat_fil.groupby("programa")
        for prog_name, grp in prog_grouped:
            c_cohorte = int(len(grp))
            c_retenidos = int(grp["retenido"].sum())
            c_desertores = int(grp["deserto"].sum())
            c_ret_pct = round((c_retenidos / max(1, c_cohorte)) * 100.0, 1)
            c_des_pct = round(100.0 - c_ret_pct, 1)
            c_prom = round(float(grp["promedio_num"].mean()), 2) if pd.notna(grp["promedio_num"].mean()) else 0.0
            c_alertados = int(grp["alertado"].sum())
            c_al_des = int((grp["alertado"] & grp["deserto"]).sum())
            c_prec = round((c_al_des / max(1, c_alertados)) * 100.0, 1) if c_alertados > 0 else 0.0
            c_cob = round((c_al_des / max(1, c_desertores)) * 100.0, 1) if c_desertores > 0 else 0.0

            desglose.append({
                "programa": prog_name,
                "facultad": FACULTAD_MAPPING.get(prog_name, "Otras Facultades"),
                "cohorte": c_cohorte,
                "retenidos": c_retenidos,
                "desertores": c_desertores,
                "retencion_pct": c_ret_pct,
                "desercion_pct": c_des_pct,
                "promedio": c_prom,
                "alertados": c_alertados,
                "precision_pct": c_prec,
                "cobertura_pct": c_cob,
                "semaforo_desercion": METAS_CONFIG["desercion"]["eval"](c_des_pct),
                "semaforo_retencion": METAS_CONFIG["retencion"]["eval"](c_ret_pct),
                "semaforo_promedio": METAS_CONFIG["promedio_cohorte"]["eval"](c_prom),
                "semaforo_precision": METAS_CONFIG["precision_alerta"]["eval"](c_prec),
                "semaforo_cobertura": METAS_CONFIG["cobertura_alerta"]["eval"](c_cob)
            })

    desglose.sort(key=lambda x: x["desercion_pct"], reverse=True)

    matriz_confusion = {
        "verdaderos_positivos": alertados_que_desertaron,
        "falsos_positivos": alertados_que_retuvieron,
        "falsos_negativos": no_alertados_que_desertaron,
        "verdaderos_negativos": no_alertados_que_retuvieron
    }

    return {
        "kpis": kpis,
        "desglose_programas": desglose,
        "matriz_confusion": matriz_confusion,
        "filtros_activos": {
            "facultad": filter_facultad or "TODAS",
            "programa": filter_programa or "TODOS",
            "estrato": filter_estrato or "TODOS"
        },
        "catalogos": {
            "programas": programas_disponibles,
            "facultades": facultades_disponibles,
            "estratos": estratos_disponibles,
            "facultad_mapping": FACULTAD_MAPPING
        }
    }

def get_bi_drilldown(metrica='retencion', db_path='etl_warehouse.db', filter_programa=None, filter_facultad=None, filter_estrato=None):
    """
    Retorna la lista detallada de estudiantes individuales que sustentan el valor de la métrica clickeada.
    """
    # Si por compatibilidad alguien llama pasando db_path en primera posición
    if metrica.endswith('.db') or os.path.exists(metrica):
        actual_db = metrica
        actual_met = db_path if db_path != 'etl_warehouse.db' else 'retencion'
        db_path = actual_db
        metrica = actual_met

    conn = sqlite3.connect(db_path)
    df_adm, df_mat1 = load_cohort_base_dataframe(conn)
    conn.close()

    # Filtros
    df_sub = df_mat1.copy()
    if filter_facultad and filter_facultad != "TODAS":
        df_sub = df_sub[df_sub["facultad"] == filter_facultad]
    if filter_programa and filter_programa != "TODOS":
        df_sub = df_sub[df_sub["programa"] == filter_programa]
    if filter_estrato and str(filter_estrato) != "TODOS":
        try:
            est_val = int(filter_estrato)
            df_sub = df_sub[df_sub["estrato"] == est_val]
        except Exception:
            pass

    metrica_lower = metrica.lower()
    titulo = "Registros de Estudiantes"
    subtitulo = ""

    if metrica_lower == "retencion":
        df_res = df_sub[df_sub["retenido"]]
        titulo = "Estudiantes Retenidos (Matriculados con Pago Aprobado en 2025-2)"
        subtitulo = f"{len(df_res)} estudiantes renovaron matrícula y completaron su pago."
    elif metrica_lower == "desercion":
        df_res = df_sub[df_sub["deserto"]]
        titulo = "Estudiantes en Deserción (No Renovaron o Pago Pendiente/Sin Pago en 2025-2)"
        subtitulo = f"{len(df_res)} estudiantes no continuaron o tienen estado de pago pendiente."
    elif metrica_lower == "alertados":
        df_res = df_sub[df_sub["alertado"]]
        titulo = "Estudiantes con Alerta Temprana Activa"
        subtitulo = f"{len(df_res)} estudiantes con promedio parcial < 3.0 o sin accesos en semanas 7 y 8."
    elif metrica_lower == "precision":
        # Alertados que desertaron (Aciertos de la alerta)
        df_res = df_sub[df_sub["alertado"] & df_sub["deserto"]]
        titulo = "Aciertos de la Alerta: Alertados que Efectivamente Desertaron"
        subtitulo = f"{len(df_res)} casos donde la alerta temprana predijo correctamente la deserción."
    elif metrica_lower == "cobertura":
        # Desertores detectados por la alerta
        df_res = df_sub[df_sub["deserto"]]
        titulo = "Universo de Desertores y su Captura por Alerta Temprana"
        subtitulo = f"{len(df_res)} desertores en total. Verifique la columna de alerta para medir la cobertura."
    elif metrica_lower == "promedio":
        df_res = df_sub.sort_values(by="promedio_num", ascending=True)
        titulo = "Rendimiento Académico de la Cohorte 2025-1"
        subtitulo = f"{len(df_res)} estudiantes con promedio del período evaluado."
    elif metrica_lower == "absorcion":
        # Para absorción mostramos admitidos y si ingresaron o no a la cohorte
        conn = sqlite3.connect(db_path)
        df_adm_all = pd.read_sql("SELECT DISTINCT documento_identidad, nombre_completo, programa_academico, estrato FROM admisiones", conn)
        conn.close()
        df_adm_all["facultad"] = df_adm_all["programa_academico"].map(lambda p: FACULTAD_MAPPING.get(p, "Otras Facultades"))
        if filter_facultad and filter_facultad != "TODAS":
            df_adm_all = df_adm_all[df_adm_all["facultad"] == filter_facultad]
        if filter_programa and filter_programa != "TODOS":
            df_adm_all = df_adm_all[df_adm_all["programa_academico"] == filter_programa]
        if filter_estrato and str(filter_estrato) != "TODOS":
            try:
                df_adm_all = df_adm_all[df_adm_all["estrato"] == int(filter_estrato)]
            except Exception:
                pass
        
        cohorte_docs = set(df_mat1["documento"].astype(str))
        df_adm_all["matriculado_cohorte"] = df_adm_all["documento_identidad"].astype(str).isin(cohorte_docs)
        
        registros_adm = []
        for _, r in df_adm_all.iterrows():
            registros_adm.append({
                "documento": str(r["documento_identidad"]),
                "nombre_completo": str(r["nombre_completo"]),
                "programa": str(r["programa_academico"]),
                "facultad": str(r["facultad"]),
                "estrato": int(r["estrato"]) if pd.notna(r["estrato"]) else "N/D",
                "promedio_moodle": "—",
                "accesos_moodle": "—",
                "promedio": "—",
                "estado_pago_2025_2": "—",
                "alertado": False,
                "motivo_alerta": "—",
                "estado_cohorte": "Matriculado en Cohorte" if r["matriculado_cohorte"] else "Admitido No Matriculado"
            })
        return {
            "metrica": metrica,
            "titulo": "Auditoría de Absorción: Admitidos vs. Matriculados Cohorte 2025-1",
            "subtitulo": f"{len(registros_adm)} aspirantes admitidos evaluados.",
            "total": len(registros_adm),
            "registros": registros_adm
        }
    else:
        # Por programa específico
        df_res = df_sub

    registros = []
    for _, r in df_res.iterrows():
        ret = bool(r["retenido"])
        pago_status = str(r["estado_pago_2025_2"])
        
        estado_label = "🟢 Retenido (Pagado)" if ret else ("🔴 Deserción (No Renovó)" if pago_status == "No Renovó Matrícula" else f"🟡 Deserción ({pago_status})")
        
        registros.append({
            "documento": str(r["documento"]),
            "nombre_completo": str(r["nombre_completo"]),
            "programa": str(r["programa"]),
            "facultad": str(r["facultad"]),
            "estrato": int(r["estrato"]) if pd.notna(r["estrato"]) else "N/D",
            "promedio_moodle": round(float(r["prom_parcial_moodle"]), 2) if pd.notna(r.get("prom_parcial_moodle")) else "—",
            "accesos_moodle": int(r["accesos_sem7_8_moodle"]) if pd.notna(r.get("accesos_sem7_8_moodle")) else 0,
            "promedio": round(float(r["promedio_num"]), 2) if pd.notna(r["promedio_num"]) else "—",
            "estado_pago_2025_2": pago_status,
            "alertado": bool(r["alertado"]),
            "motivo_alerta": str(r["motivo_alerta"]),
            "estado_cohorte": estado_label
        })

    return {
        "metrica": metrica,
        "titulo": titulo,
        "subtitulo": subtitulo,
        "total": len(registros),
        "registros": registros
    }

def compute_improved_alert_metrics(db_path='etl_warehouse.db'):
    """
    Calcula la nueva regla de alerta temprana optimizada para la capacidad de consejería (<= 120 estudiantes).
    Utiliza telemetría de Moodle de las semanas 1 a 8.
    """
    conn = sqlite3.connect(db_path)
    
    # Matrículas 2025-1
    df_mat = pd.read_sql("SELECT codigo, documento, correo_institucional, programa FROM matriculas WHERE periodo = '2025-1' AND tipo_ingreso = 'Nuevo'", conn)
    df_mat['occ'] = df_mat.groupby('correo_institucional').cumcount()
    df_mat['join_key'] = df_mat['correo_institucional'] + '_' + df_mat['occ'].astype(str)

    # Matrículas 2025-2 y Pagos
    df_mat2 = pd.read_sql("SELECT DISTINCT documento FROM matriculas WHERE periodo = '2025-2'", conn)
    mat2_docs = set(df_mat2['documento'].dropna().astype(str).str.strip())
    df_pag = pd.read_sql("SELECT documento, estado_pago FROM pagos WHERE periodo = '2025-2'", conn)
    pagos_map = dict(zip(df_pag['documento'].astype(str).str.strip(), df_pag['estado_pago']))

    retenido_pago = []
    for doc in df_mat['documento'].astype(str).str.strip():
        enr = doc in mat2_docs
        st = pagos_map.get(doc, 'Sin Registro')
        retenido_pago.append(enr and (st.lower() in ['pagado', 'aprobada', 'aprobado']))

    df_mat['deserto'] = [1 if not x else 0 for x in retenido_pago]
    tot_des = int(df_mat['deserto'].sum())
    tot_ret = len(df_mat) - tot_des

    # Moodle semanas 1 a 8
    df_m = pd.read_sql("SELECT correo, semana, CAST(accesos AS INT) as accesos, CAST(nota_parcial_0_100 AS FLOAT) as nota FROM moodle WHERE semana <= 8", conn)
    df_m['occ'] = df_m.groupby(['correo', 'semana']).cumcount()
    df_m['join_key'] = df_m['correo'] + '_' + df_m['occ'].astype(str)

    # Nombres y estratos desde admisiones
    df_adm = pd.read_sql("SELECT DISTINCT documento_identidad, nombre_completo, estrato, programa_academico FROM admisiones", conn)
    adm_map = df_adm.set_index('documento_identidad').to_dict('index')

    conn.close()

    piv_notas = df_m.pivot(index='join_key', columns='semana', values='nota')
    piv_accesos = df_m.pivot(index='join_key', columns='semana', values='accesos')

    m_df = pd.DataFrame(index=df_m['join_key'].unique())
    m_df['nota_sem_4'] = (piv_notas[4] / 20.0).round(2)
    m_df['nota_sem_8'] = (piv_notas[8] / 20.0).round(2)
    m_df['prom_sem_4_8'] = ((m_df['nota_sem_4'] + m_df['nota_sem_8']) / 2.0).round(2)
    m_df['acc_tot_sem_1_8'] = piv_accesos[[w for w in range(1, 9)]].sum(axis=1)
    m_df['acc_sem_7_8'] = piv_accesos[7].fillna(0) + piv_accesos[8].fillna(0)

    df = df_mat.merge(m_df, left_on='join_key', right_index=True, how='left')

    # Regla Actual
    r_act = (df['prom_sem_4_8'] < 3.0) | (df['acc_sem_7_8'] == 0)
    tp_act = int((r_act & (df['deserto'] == 1)).sum())
    fp_act = int((r_act & (df['deserto'] == 0)).sum())
    fn_act = int(((~r_act) & (df['deserto'] == 1)).sum())
    tn_act = int(((~r_act) & (df['deserto'] == 0)).sum())

    # Regla Nueva Optimizada (<= 120 consejeros)
    cond1 = df['acc_sem_7_8'] == 0
    cond2 = (df['acc_sem_7_8'].between(1, 2)) & (df['prom_sem_4_8'] > 2.70)
    cond3 = (df['acc_sem_7_8'] > 2) & (df['acc_tot_sem_1_8'] <= 30) & (df['prom_sem_4_8'] <= 2.60) & (df['nota_sem_4'] <= 2.60)
    
    r_new = cond1 | cond2 | cond3
    tp_new = int((r_new & (df['deserto'] == 1)).sum())
    fp_new = int((r_new & (df['deserto'] == 0)).sum())
    fn_new = int(((~r_new) & (df['deserto'] == 1)).sum())
    tn_new = int(((~r_new) & (df['deserto'] == 0)).sum())

    n_new = int(r_new.sum())
    n_act = int(r_act.sum())

    motivos = []
    for idx, row in df[r_new].iterrows():
        c1 = cond1.loc[idx]
        c2 = cond2.loc[idx]
        c3 = cond3.loc[idx]
        if c1:
            m = "Inactividad Crítica Reciente: Cero accesos en semanas 7 y 8"
        elif c2:
            m = f"Desconexión Súbita: Solo {int(row['acc_sem_7_8'])} accesos en sem 7-8 y notas irregulares (Promedio: {row['prom_sem_4_8']})"
        elif c3:
            m = f"Bajo Compromiso Acumulado: {int(row['acc_tot_sem_1_8'])} accesos totales (sem 1-8) y Promedio Parcial {row['prom_sem_4_8']} <= 2.60"
        else:
            m = "Riesgo Focalizado LMS"
        
        doc = str(row['documento'])
        adm_info = adm_map.get(doc, {})
        motivos.append({
            "codigo": str(row['codigo']),
            "documento": doc,
            "nombre_completo": adm_info.get('nombre_completo', 'Estudiante Cohorte'),
            "programa": str(row['programa']),
            "estrato": adm_info.get('estrato', 'N/D'),
            "prom_moodle_4_8": float(row['prom_sem_4_8']),
            "nota_sem_4": float(row['nota_sem_4']),
            "nota_sem_8": float(row['nota_sem_8']),
            "acc_sem_7_8": int(row['acc_sem_7_8']),
            "acc_tot_1_8": int(row['acc_tot_sem_1_8']),
            "motivo_alerta": m,
            "deserto_real": bool(row['deserto'] == 1),
            "estado_real": "🔴 Desertó" if row['deserto'] == 1 else "🟢 Retenido"
        })

    return {
        "regla_actual": {
            "nombre": "Regla Actual: Promedio(Sem 4,8) < 3.0 O Accesos(Sem 7,8) == 0",
            "formula_corta": "Prom_4_8 < 3.0 ∨ Acc_7_8 == 0",
            "n_alertados": n_act,
            "tp": tp_act,
            "fp": fp_act,
            "fn": fn_act,
            "tn": tn_act,
            "precision": round((tp_act / n_act) * 100, 2),
            "cobertura": round((tp_act / tot_des) * 100, 2)
        },
        "regla_nueva": {
            "nombre": "Regla Focalizada de Capacidad (Semanas 1 a 8)",
            "formula_corta": "(Acc_7_8 == 0) ∨ (Acc_7_8 ∈ [1,2] ∧ Prom_4_8 > 2.70) ∨ (Acc_Tot_1_8 ≤ 30 ∧ Prom_4_8 ≤ 2.60 ∧ Nota_4 ≤ 2.60)",
            "n_alertados": n_new,
            "tp": tp_new,
            "fp": fp_new,
            "fn": fn_new,
            "tn": tn_new,
            "precision": round((tp_new / n_new) * 100, 2),
            "cobertura": round((tp_new / tot_des) * 100, 2),
            "capacidad_maxima": 120,
            "meta_cobertura_minima": 35.0,
            "cumple_capacidad": n_new <= 120,
            "cumple_cobertura": (tp_new / tot_des) * 100 >= 35.0,
            "total_desertores": tot_des,
            "total_retenidos": tot_ret,
            "total_cohorte": len(df)
        },
        "estudiantes_alertados": motivos
    }
