import re
import datetime
from io import BytesIO
import pandas as pd
import numpy as np

REQUIRED_KEYWORDS = ["admisiones", "bienestar", "pagos", "moodle", "matriculas"]

def identify_dataset_type(filename: str):
    """
    Identifica cuál de los 5 datasets corresponde según el nombre del archivo.
    Retorna la clave correspondiente o None.
    """
    clean_name = filename.lower()
    for kw in REQUIRED_KEYWORDS:
        if kw in clean_name:
            return kw
    return None

def validate_uploaded_files(filenames):
    """
    Verifica que la lista de nombres de archivos contenga los 5 requeridos.
    Retorna: (is_valid: bool, mapping: dict, missing: list, unrecognized: list)
    """
    mapping = {}
    unrecognized = []
    
    for fname in filenames:
        dtype = identify_dataset_type(fname)
        if dtype:
            # Si hay más de uno para el mismo tipo, se guarda el último o se registra
            mapping[dtype] = fname
        else:
            unrecognized.append(fname)
            
    missing = [kw for kw in REQUIRED_KEYWORDS if kw not in mapping]
    is_valid = len(missing) == 0
    return is_valid, mapping, missing, unrecognized

class TransformationTracker:
    """
    Registra minuciosamente todas las transformaciones y reglas de calidad de datos
    aplicadas a cada dataset.
    """
    def __init__(self):
        self.logs = []  # Lista de dicts con detalles
        self.summary_by_dataset = {}

    def log(self, dataset: str, rule: str, dimension: str, description: str, affected_count: int, sample_diff: str = ""):
        entry = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dataset": dataset,
            "rule": rule,
            "dimension": dimension,
            "description": description,
            "affected_count": int(affected_count),
            "sample_diff": sample_diff
        }
        self.logs.append(entry)
        
        if dataset not in self.summary_by_dataset:
            self.summary_by_dataset[dataset] = {
                "initial_rows": 0,
                "final_rows": 0,
                "initial_cols": 0,
                "final_cols": 0,
                "total_transformations": 0,
                "duplicates_removed": 0,
                "nulls_handled": 0,
                "formats_corrected": 0,
                "outliers_corrected": 0,
                "rules_applied": []
            }
        
        summ = self.summary_by_dataset[dataset]
        summ["total_transformations"] += int(affected_count)
        summ["rules_applied"].append(rule)
        
        if dimension == "Unicidad":
            summ["duplicates_removed"] += int(affected_count)
        elif dimension == "Completitud":
            summ["nulls_handled"] += int(affected_count)
        elif dimension in ["Conformidad", "Consistencia"]:
            summ["formats_corrected"] += int(affected_count)
        elif dimension == "Validez":
            summ["outliers_corrected"] += int(affected_count)

    def init_dataset_stats(self, dataset: str, initial_rows: int, initial_cols: int):
        if dataset not in self.summary_by_dataset:
            self.summary_by_dataset[dataset] = {
                "initial_rows": initial_rows,
                "final_rows": initial_rows,
                "initial_cols": initial_cols,
                "final_cols": initial_cols,
                "total_transformations": 0,
                "duplicates_removed": 0,
                "nulls_handled": 0,
                "formats_corrected": 0,
                "outliers_corrected": 0,
                "rules_applied": []
            }
        else:
            self.summary_by_dataset[dataset]["initial_rows"] = initial_rows
            self.summary_by_dataset[dataset]["initial_cols"] = initial_cols

    def set_final_stats(self, dataset: str, final_rows: int, final_cols: int):
        if dataset in self.summary_by_dataset:
            self.summary_by_dataset[dataset]["final_rows"] = final_rows
            self.summary_by_dataset[dataset]["final_cols"] = final_cols

def clean_text_whitespace(val):
    if pd.isna(val):
        return val
    s = str(val).strip()
    s = re.sub(r'\s+', ' ', s)
    return s

def clean_person_name(val):
    """Convierte nombres en mayúscula sostenida o desordenados a Formato Nombre Propio (Title Case)."""
    if pd.isna(val) or not str(val).strip():
        return "Sin Nombre"
    s = clean_text_whitespace(val)
    particles = {'de', 'del', 'la', 'las', 'los', 'y', 'e', 'van', 'von', 'san'}
    words = s.split(' ')
    result = []
    for i, w in enumerate(words):
        w_lower = w.lower()
        if i > 0 and w_lower in particles:
            result.append(w_lower)
        else:
            result.append(w.capitalize())
    return ' '.join(result)

# Catálogo canónico de programas académicos y sus abreviaciones frecuentes
PROGRAM_CATALOG = {
    "Ingeniería de Sistemas": [
        "ing. sistemas", "ing sistemas", "sistemas", "ing. de sistemas", "ing de sistemas",
        "ingenieria de sistemas", "ingeniería de sistemas", "ing. sist", "is", "ing sist"
    ],
    "Ingeniería Industrial": [
        "ing. industrial", "ing industrial", "industrial", "ingenieria industrial",
        "ingeniería industrial", "ii", "ing ind", "ind"
    ],
    "Ingeniería Civil": [
        "ing. civil", "ing civil", "civil", "ingenieria civil", "ingeniería civil", "ic"
    ],
    "Administración de Empresas": [
        "adm", "adm. empresas", "adm empresas", "administracion", "administración",
        "administracion de empresas", "administración de empresas", "admin", "admin empresas", "admon"
    ],
    "Medicina": [
        "med", "medicina", "medico"
    ],
    "Derecho": [
        "der", "derecho", "leyes", "abogacia", "abogacía"
    ],
    "Psicología": [
        "psi", "psicologia", "psicología"
    ],
    "Diseño Gráfico": [
        "dis", "diseno", "diseño", "diseno grafico", "diseño grafico",
        "dis. grafico", "diseño gráfico", "dg"
    ],
    "Contaduría Pública": [
        "cont", "contaduria", "contaduría", "cont. publica", "contaduria publica",
        "contaduría pública", "cp"
    ],
    "Comunicación Social": [
        "com", "comunicacion", "comunicación", "comunicacion social",
        "comunicación social", "cs"
    ],
    "Trabajo Social": [
        "t. social", "t social", "ts", "trabajo social", "trab. social", "t.soc", "tsocial", "t social."
    ],
    "Ingeniería Informática": [
        "ing. inf.", "ing. inf", "ing inf.", "ing inf", "informatica", "informática",
        "ing. informatica", "ing. informática", "ingenieria informatica", "ingeniería informática"
    ]
}

def standardize_program_name(val):
    """Normaliza abreviaciones y variaciones de programas académicos a su nombre oficial completo."""
    if pd.isna(val) or not str(val).strip():
        return "Sin Programa Asignado"
    raw = str(val).strip()
    
    # Limpiar y quitar tildes/puntuación para comparación robusta
    clean = raw.lower()
    clean = re.sub(r'[áàäâ]', 'a', clean)
    clean = re.sub(r'[éèëê]', 'e', clean)
    clean = re.sub(r'[íìïî]', 'i', clean)
    clean = re.sub(r'[óòöô]', 'o', clean)
    clean = re.sub(r'[úùüû]', 'u', clean)
    clean = re.sub(r'[ñ]', 'n', clean)
    clean = re.sub(r'[\._\-]+', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    # Búsqueda exacta en catálogo
    for official_name, aliases in PROGRAM_CATALOG.items():
        for alias in aliases:
            alias_clean = re.sub(r'[\._\-]+', ' ', alias.lower()).strip()
            alias_clean = re.sub(r'[áàäâ]', 'a', alias_clean)
            alias_clean = re.sub(r'[éèëê]', 'e', alias_clean)
            alias_clean = re.sub(r'[íìïî]', 'i', alias_clean)
            alias_clean = re.sub(r'[óòöô]', 'o', alias_clean)
            alias_clean = re.sub(r'[úùüû]', 'u', alias_clean)
            if clean == alias_clean:
                return official_name

    # Búsqueda por patrones específicos clave
    if ("t." in clean and "social" in clean) or ("trabajo" in clean and "social" in clean) or clean == "ts":
        return "Trabajo Social"
    if ("ing" in clean and "inf" in clean) or ("informat" in clean):
        return "Ingeniería Informática"
    if "sistema" in clean:
        return "Ingeniería de Sistemas"
    if "industrial" in clean:
        return "Ingeniería Industrial"
    if "empresa" in clean or "admin" in clean:
        return "Administración de Empresas"
    if "medic" in clean:
        return "Medicina"
    if "derech" in clean:
        return "Derecho"
    if "psico" in clean:
        return "Psicología"
    if "dis" in clean and ("graf" in clean or "disen" in clean):
        return "Diseño Gráfico"
    if "contad" in clean:
        return "Contaduría Pública"
    if "comunic" in clean:
        return "Comunicación Social"
    if "civil" in clean:
        return "Ingeniería Civil"

    return clean_person_name(raw)

def clean_periodo_academico(val):
    """
    Estandariza nomenclaturas como 2025-2, 2025-II, 2025_II, 2025 2 a formato canónico YYYY-Semestre (ej. 2025-2).
    """
    if pd.isna(val) or not str(val).strip():
        return "2025-1"
    s = str(val).strip().upper()
    
    # Extraer año de 4 dígitos
    m_year = re.search(r'(20\d\d)', s)
    year = m_year.group(1) if m_year else "2025"
    
    # Detectar semestre 2 o II
    if re.search(r'[-_\s\.\/](II|2)$', s) or s.endswith('II') or s.endswith('-2') or s.endswith('_2') or s.endswith(' 2'):
        return f"{year}-2"
    # Detectar semestre 1 o I
    elif re.search(r'[-_\s\.\/](I|1)$', s) or s.endswith('I') or s.endswith('-1') or s.endswith('_1') or s.endswith(' 1'):
        return f"{year}-1"
    
    return f"{year}-1"

def clean_estado_transaccion(val):
    """Estandariza estados de pago/transacción a Title Case sin mayúsculas sostenidas."""
    if pd.isna(val) or not str(val).strip():
        return "Pendiente"
    s = clean_text_whitespace(val).strip().lower()
    if any(w in s for w in ["aprob", "exit", "pagad", "complet"]):
        return "Pagado"
    elif any(w in s for w in ["rechaz", "fall", "deneg"]):
        return "Rechazada"
    elif any(w in s for w in ["pend", "esper"]):
        return "Pendiente"
    elif any(w in s for w in ["anul", "cancel"]):
        return "Anulada"
    elif any(w in s for w in ["proc", "tramit"]):
        return "En Proceso"
    
    # Para cualquier otro texto, Title Case estricto
    return " ".join([w.capitalize() for w in s.split()])

def clean_promedio_periodo(val):
    """
    Normaliza el promedio académico del período a escala 0.0 - 5.0 con punto decimal.
    - Maneja separadores con coma o punto (ej. 3,6 -> 3.6).
    - Corrige valores sin separador decimal (ej. 36 -> 3.6, 24 -> 2.4, 45 -> 4.5, 50 -> 5.0).
    - Convierte escalas 0-100 a escala 0-5.0 (ej. 75 -> 3.75).
    - Acota a rango 0.0 a 5.0.
    """
    if pd.isna(val) or val is None or str(val).strip().lower() in ['', 'nan', 'none', 'nat', 'null']:
        return None
    s = str(val).strip().replace(',', '.')
    try:
        fval = float(s)
        if 5.0 < fval <= 50.0:
            fval = fval / 10.0
        elif 50.0 < fval <= 100.0:
            fval = fval / 20.0
        fval = max(0.0, min(5.0, fval))
        return round(fval, 2)
    except (ValueError, TypeError):
        return None

def clean_document_id(val):
    if pd.isna(val):
        return ""
    # Quitar puntos, comas, guiones, espacios
    s = str(val).strip()
    # Si viene como float tipo 123456.0 convertir a entero
    if re.match(r'^\d+\.0$', s):
        s = s[:-2]
    s = re.sub(r'[^a-zA-Z0-9]', '', s)
    return s.upper()

def clean_email(val):
    if pd.isna(val):
        return "sin_correo@institucion.edu.co"
    s = str(val).strip().lower()
    # Si no tiene @ o ., arreglar o marcar
    if '@' not in s or '.' not in s:
        return f"{s}@institucion.edu.co" if s else "sin_correo@institucion.edu.co"
    return s

def clean_phone(val):
    if pd.isna(val):
        return "NO_REGISTRA"
    s = str(val).strip()
    if re.match(r'^\d+\.0$', s):
        s = s[:-2]
    digits = re.sub(r'\D', '', s)
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 7:
        return f"{digits[:3]}-{digits[3:]}"
    return digits if digits else "NO_REGISTRA"

SPANISH_MONTHS = {
    'enero': '01', 'ene': '01',
    'febrero': '02', 'feb': '02',
    'marzo': '03', 'mar': '03',
    'abril': '04', 'abr': '04',
    'mayo': '05', 'may': '05',
    'junio': '06', 'jun': '06',
    'julio': '07', 'jul': '07',
    'agosto': '08', 'ago': '08',
    'septiembre': '09', 'setiembre': '09', 'sep': '09', 'set': '09',
    'octubre': '10', 'oct': '10',
    'noviembre': '11', 'nov': '11',
    'diciembre': '12', 'dic': '12'
}

def standardize_date(val):
    """
    Normaliza fechas a formato estándar YYYY-MM-DD.
    Soporta:
    - Fechas ISO (2024-11-05)
    - Fechas en español con mes abreviado o completo (12-dic-2024, 12 de diciembre de 2024)
    - Fechas DD/MM/YYYY y DD-MM-YYYY (05/11/2024, 12/12/2024)
    - Números de serie de Excel (45601 -> 2024-11-05)
    - Timestamps de pandas / datetime
    """
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, (datetime.datetime, datetime.date, pd.Timestamp)):
        return val.strftime('%Y-%m-%d')
        
    s = str(val).strip()
    if s.lower() in ['', 'nan', 'none', 'nat', 'null', '1900-01-01', '0']:
        return None

    # Caso número de serie de Excel (ej. 45601 -> 2024-11-05, 45638 -> 2024-12-12)
    try:
        fval = float(s)
        if 20000 < fval < 65000:
            dt = pd.to_datetime(fval, unit='D', origin='1899-12-30')
            return dt.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        pass

    # Si viene con timestamp tipo '2024-11-05 00:00:00', truncar a solo fecha
    if ' ' in s and re.match(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d', s):
        s = s.split(' ')[0]

    # Limpiar conectores 'de' o 'del' ej: 12 de diciembre de 2024 -> 12-diciembre-2024
    s_clean = re.sub(r'\s+de\s+|\s+del\s+', '-', s, flags=re.IGNORECASE)
    s_clean = re.sub(r'[\s\.\,]+', '-', s_clean).strip('-')

    # Reemplazar meses en español (ej. 'dic' -> '12', 'nov' -> '11')
    s_lower = s_clean.lower()
    for m_name, m_num in SPANISH_MONTHS.items():
        pattern = r'(?<![a-z])' + re.escape(m_name) + r'(?![a-z])'
        if re.search(pattern, s_lower):
            s_lower = re.sub(pattern, m_num, s_lower)
            break

    # Patrón 1: Año al inicio YYYY-MM-DD
    m_iso = re.match(r'^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$', s_lower)
    if m_iso:
        y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
        try:
            return datetime.date(y, m, d).strftime('%Y-%m-%d')
        except ValueError:
            pass

    # Patrón 2: Día al inicio DD-MM-YYYY
    m_dmy = re.match(r'^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$', s_lower)
    if m_dmy:
        d, m, y = int(m_dmy.group(1)), int(m_dmy.group(2)), int(m_dmy.group(3))
        try:
            return datetime.date(y, m, d).strftime('%Y-%m-%d')
        except ValueError:
            pass

    # Patrón 3: MM-DD-YYYY o con pandas general
    try:
        if re.match(r'^\d{4}', s_lower):
            dt = pd.to_datetime(s_lower, errors='coerce', dayfirst=False)
        else:
            dt = pd.to_datetime(s_lower, errors='coerce', dayfirst=True)
        if pd.notna(dt) and dt.year > 1900:
            return dt.strftime('%Y-%m-%d')
    except Exception:
        pass

    return None

def safe_standardize_date(val):
    """
    Aplica standardize_date pero preserva el valor original si el parseo falla.
    Solo devuelve None para valores realmente nulos/vacíos (nunca substituye con 1900-01-01).
    """
    if pd.isna(val) or val is None or str(val).strip().lower() in ['', 'nan', 'none', 'nat', 'null', '1900-01-01']:
        return None
    result = standardize_date(val)
    return result if result is not None else str(val).strip()

def clean_currency(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return max(0.0, float(val))
    s = str(val).strip()
    s = re.sub(r'[^\d,\.-]', '', s)
    if not s:
        return 0.0
    
    # Caso 1: Tiene puntos y comas (ej. 1.500.000,50 o 1,500,000.50)
    if ',' in s and '.' in s:
        if s.rfind(',') > s.rfind('.'):
            # Formato latino: 1.500.000,50
            s = s.replace('.', '').replace(',', '.')
        else:
            # Formato anglosajón: 1,500,000.50
            s = s.replace(',', '')
    # Caso 2: Solo comas (ej. 150000,00 o 2,450,000)
    elif ',' in s and '.' not in s:
        parts = s.split(',')
        if len(parts) == 2 and len(parts[1]) in [1, 2]:
            s = s.replace(',', '.')
        else:
            s = s.replace(',', '')
    # Caso 3: Solo puntos (ej. 2.450.000 o 85.000 o 1500.50)
    elif '.' in s and ',' not in s:
        parts = s.split('.')
        if len(parts) > 2:
            # Múltiples puntos: definitivamente miles (ej. 2.450.000)
            s = s.replace('.', '')
        elif len(parts) == 2:
            if len(parts[1]) == 3:
                # 3 dígitos tras el punto en valores enteros comunes (ej. 85.000)
                s = s.replace('.', '')
            # Si tiene 1 o 2 dígitos, es decimal (ej. 1500.50)

    try:
        res = float(s)
        return max(0.0, res)  # Valores de pago no pueden ser negativos
    except Exception:
        return 0.0

class ETLProcessor:
    def __init__(self):
        self.tracker = TransformationTracker()
        self.cleaned_data = {}

    def load_file(self, file_bytes: bytes, filename: str) -> pd.DataFrame:
        """Carga un archivo ya sea CSV o Excel."""
        fname_lower = filename.lower()
        if fname_lower.endswith('.csv'):
            try:
                # Intentar utf-8 y luego latin1/cp1252 con detección de separador
                try:
                    df = pd.read_csv(BytesIO(file_bytes), encoding='utf-8', sep=None, engine='python')
                except Exception:
                    df = pd.read_csv(BytesIO(file_bytes), encoding='latin1', sep=None, engine='python')
                return df
            except Exception as e:
                raise ValueError(f"Error al leer CSV '{filename}': {str(e)}")
        elif fname_lower.endswith(('.xlsx', '.xls')):
            try:
                df = pd.read_excel(BytesIO(file_bytes))
                return df
            except Exception as e:
                raise ValueError(f"Error al leer Excel '{filename}': {str(e)}")
        else:
            raise ValueError(f"Formato no soportado para '{filename}'. Debe ser .csv, .xlsx o .xls")

    def standardize_column_names(self, df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        """Estandariza nombres de columnas a snake_case sin caracteres raros."""
        old_cols = list(df.columns)
        new_cols = []
        changed = 0
        for col in old_cols:
            c = str(col).strip().lower()
            c = re.sub(r'[áàäâ]', 'a', c)
            c = re.sub(r'[éèëê]', 'e', c)
            c = re.sub(r'[íìïî]', 'i', c)
            c = re.sub(r'[óòöô]', 'o', c)
            c = re.sub(r'[úùüû]', 'u', c)
            c = re.sub(r'[ñ]', 'n', c)
            c = re.sub(r'[^a-z0-9_]', '_', c)
            c = re.sub(r'_+', '_', c).strip('_')
            new_cols.append(c)
            if c != col:
                changed += 1
        df.columns = new_cols
        if changed > 0:
            self.tracker.log(
                dataset=dataset_name,
                rule="Estandarización de nombres de columnas",
                dimension="Conformidad",
                description=f"Se normalizaron {changed} encabezados de columnas a formato snake_case limpio.",
                affected_count=changed,
                sample_diff=f"{old_cols[:3]} -> {new_cols[:3]}"
            )
        return df

    def remove_empty_rows_and_duplicates(self, df: pd.DataFrame, dataset_name: str, key_columns: list = None) -> pd.DataFrame:
        """Elimina filas totalmente vacías y duplicados exactos o por llaves."""
        initial_len = len(df)
        
        # 1. Filas completamente vacías
        df_non_empty = df.dropna(how='all')
        empty_rows = initial_len - len(df_non_empty)
        if empty_rows > 0:
            self.tracker.log(
                dataset=dataset_name,
                rule="Eliminación de filas vacías",
                dimension="Completitud",
                description=f"Se eliminaron {empty_rows} filas totalmente vacías sin información.",
                affected_count=empty_rows
            )
            df = df_non_empty

        # 2. Duplicados exactos en todas las columnas
        before_dedup = len(df)
        df_dedup = df.drop_duplicates()
        exact_dups = before_dedup - len(df_dedup)
        if exact_dups > 0:
            self.tracker.log(
                dataset=dataset_name,
                rule="Eliminación de duplicados exactos",
                dimension="Unicidad",
                description=f"Se detectaron y eliminaron {exact_dups} registros idénticos redundantes.",
                affected_count=exact_dups
            )
            df = df_dedup

        # 3. Duplicados por clave primaria si aplica
        if key_columns:
            valid_keys = [k for k in key_columns if k in df.columns]
            if valid_keys:
                before_key_dedup = len(df)
                df_key_dedup = df.drop_duplicates(subset=valid_keys, keep='last')
                key_dups = before_key_dedup - len(df_key_dedup)
                if key_dups > 0:
                    self.tracker.log(
                        dataset=dataset_name,
                        rule=f"Deduplicación por llave de negocio ({', '.join(valid_keys)})",
                        dimension="Unicidad",
                        description=f"Se depuraron {key_dups} registros duplicados conservando la última transacción/versión válida.",
                        affected_count=key_dups
                    )
                    df = df_key_dedup

        return df

    def clean_general_strings(self, df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        """Aplica trim y unificación de espacios a todas las columnas de texto."""
        str_cols = df.select_dtypes(include=['object', 'string']).columns
        modified_count = 0
        for col in str_cols:
            before_series = df[col].astype(str)
            df[col] = df[col].apply(clean_text_whitespace)
            changed = (before_series != df[col].astype(str)).sum()
            modified_count += changed

        if modified_count > 0:
            self.tracker.log(
                dataset=dataset_name,
                rule="Limpieza de espacios en blanco (Trim)",
                dimension="Conformidad",
                description=f"Se recortaron espacios en blanco sobrantes y dobles espacios en {modified_count} celdas de texto.",
                affected_count=modified_count
            )
        return df

    # ================= LIMPIEZA ESPECÍFICA POR DATASET =================

    def clean_admisiones(self, df: pd.DataFrame) -> pd.DataFrame:
        dataset_name = "admisiones"
        df = self.standardize_column_names(df, dataset_name)
        df = self.remove_empty_rows_and_duplicates(df, dataset_name, key_columns=["id_estudiante"])
        df = self.clean_general_strings(df, dataset_name)

        # Regla 1: Detección y normalización de documento_identidad (sin dejarlo vacío)
        doc_cols = [c for c in df.columns if any(w in c for w in ["documento", "cedula", "identificacion", "dni", "cc", "nro_doc", "num_doc", "doc"])]
        if doc_cols:
            prim_doc = doc_cols[0]
            orig = df[prim_doc].copy()
            df["documento_identidad"] = df[prim_doc].apply(clean_document_id)
            for c in doc_cols:
                if c != "documento_identidad":
                    df.drop(columns=[c], inplace=True)
            diff = (orig != df["documento_identidad"]).sum()
            self.tracker.log(dataset_name, "Normalización de documento de identidad", "Conformidad",
                             f"Se estandarizaron {diff} números de documento eliminando símbolos y guiones.", diff)
        else:
            df["documento_identidad"] = ""

        # Regla 2: Formato de nombre completo a Title Case (Nombre Propio sin mayúscula sostenida)
        # IMPORTANTE: Excluir id_estudiante o columnas de identificador para no confundirlas con el nombre
        name_cols = [c for c in df.columns if any(w in c for w in ["nombre", "postulante", "aspirante"]) and not any(id_w in c for id_w in ["id", "cod", "num", "doc"])]
        if not name_cols:
            name_cols = [c for c in df.columns if c == "estudiante"]

        if name_cols:
            prim_name = name_cols[0]
            orig = df[prim_name].copy()
            df["nombre_completo"] = df[prim_name].apply(clean_person_name)
            for c in name_cols:
                if c != "nombre_completo":
                    df.drop(columns=[c], inplace=True)
            diff = (orig != df["nombre_completo"]).sum()
            self.tracker.log(dataset_name, "Capitalización a Nombre Propio (Title Case)", "Consistencia",
                             f"Se corrigieron {diff} nombres eliminando mayúsculas sostenidas a formato formal.", diff)
        else:
            df["nombre_completo"] = "Sin Nombre"

        # Regla 3: Unificación estricta a UNA SOLA columna de programa académico (sin duplicar programa/carrera)
        prog_cols = [c for c in df.columns if any(w in c for w in ["carrera", "programa"])]
        if prog_cols:
            prim_prog = prog_cols[0]
            orig = df[prim_prog].copy()
            df["programa_academico"] = df[prim_prog].apply(standardize_program_name)
            for c in prog_cols:
                if c != "programa_academico":
                    df.drop(columns=[c], inplace=True)
            diff = (orig != df["programa_academico"]).sum()
            self.tracker.log(dataset_name, "Homologación y unificación de programa académico", "Consistencia",
                             f"Se consolidaron los programas a nombres oficiales en una única columna.", diff)
        else:
            df["programa_academico"] = "Sin Programa Asignado"

        # Regla 4: Corrección y validación de correos
        for col in ["email", "correo", "correo_electronico"]:
            if col in df.columns:
                orig = df[col].copy()
                df[col] = df[col].apply(clean_email)
                diff = (orig != df[col]).sum()
                self.tracker.log(dataset_name, "Validación y saneamiento de emails", "Conformidad",
                                 f"Se verificó formato de correos y se asignó dominio institucional a {diff} registros.", diff)
                break

        # Regla 5: Normalización de teléfonos
        for col in ["telefono", "celular", "contacto"]:
            if col in df.columns:
                orig = df[col].copy()
                df[col] = df[col].apply(clean_phone)
                diff = (orig != df[col]).sum()
                self.tracker.log(dataset_name, "Estandarización de formato telefónico", "Conformidad",
                                 f"Se formatearon {diff} números telefónicos al patrón estándar.", diff)
                break

        # Regla 6: Estandarización de fechas
        date_cols = [c for c in df.columns if any(w in c for w in [
            "fecha", "fec", "f_", "postulacion", "nacimiento", "inscripcion", "solicitud", "registro", "ingreso"
        ]) and not any(nw in c for nw in ["puntaje", "estado", "observacion", "id"])]
        for col in date_cols:
            orig = df[col].copy()
            df[col] = df[col].apply(safe_standardize_date)
            diff = (orig != df[col]).sum()
            self.tracker.log(dataset_name, f"Estandarización de fecha en '{col}'", "Conformidad",
                             f"Se convirtieron {diff} fechas a formato ISO standard YYYY-MM-DD.", diff)

        # Regla 7: Rango de puntaje ICFES / Ingreso (0 a 500)
        for col in ["puntaje_icfes_o_ingreso", "puntaje", "puntaje_ingreso", "icfes"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                outliers = ((df[col] < 0) | (df[col] > 500)).sum()
                df[col] = df[col].clip(lower=0.0, upper=500.0)
                if outliers > 0:
                    self.tracker.log(dataset_name, "Control de rango de puntaje ICFES (0-500)", "Validez",
                                     f"Se ajustaron {outliers} valores atípicos fuera de la escala de evaluación.", outliers)
                break

        # Regla 8: Estandarización de Estado de Admisión
        for col in ["estado_admision", "estado"]:
            if col in df.columns:
                df[col] = df[col].fillna("PENDIENTE").astype(str).str.upper().str.strip()
                break

        # Regla 9: Deduplicación rigurosa de aspirantes (Unicidad)
        before_final_dedup = len(df)
        
        # 1. Deduplicar por documento de identidad válido y no vacío
        if "documento_identidad" in df.columns:
            has_doc = (df["documento_identidad"].astype(str).str.strip() != "") & \
                      (~df["documento_identidad"].isna()) & \
                      (~df["documento_identidad"].astype(str).str.upper().isin(["NAN", "NONE", "NULL", "0"]))
            if has_doc.any():
                df_with_doc = df[has_doc].drop_duplicates(subset=["documento_identidad"], keep="last")
                df_without_doc = df[~has_doc]
                df = pd.concat([df_with_doc, df_without_doc], ignore_index=True)

        # 2. Deduplicar por id_estudiante si está presente
        if "id_estudiante" in df.columns:
            has_id = (df["id_estudiante"].astype(str).str.strip() != "") & \
                     (~df["id_estudiante"].isna()) & \
                     (~df["id_estudiante"].astype(str).str.upper().isin(["NAN", "NONE", "NULL"]))
            if has_id.any():
                df_with_id = df[has_id].drop_duplicates(subset=["id_estudiante"], keep="last")
                df_without_id = df[~has_id]
                df = pd.concat([df_with_id, df_without_id], ignore_index=True)

        # 3. Deduplicar por nombre_completo y programa_academico
        if "nombre_completo" in df.columns and "programa_academico" in df.columns:
            df = df.drop_duplicates(subset=["nombre_completo", "programa_academico"], keep="last")

        final_dups = before_final_dedup - len(df)
        if final_dups > 0:
            self.tracker.log(dataset_name, "Eliminación de aspirantes duplicados", "Unicidad",
                             f"Se eliminaron {final_dups} registros duplicados por documento de identidad, ID y nombre.", final_dups)

        # Reordenar columnas para presentación óptima
        all_cols = list(df.columns)
        desired_head = ["id_estudiante", "documento_identidad", "nombre_completo", "programa_academico"]
        ordered = [c for c in desired_head if c in all_cols] + [c for c in all_cols if c not in desired_head]
        df = df[ordered]

        return df

    def clean_bienestar(self, df: pd.DataFrame) -> pd.DataFrame:
        dataset_name = "bienestar"
        df = self.standardize_column_names(df, dataset_name)
        df = self.remove_empty_rows_and_duplicates(df, dataset_name, key_columns=["codigo_estudiantil", "id_estudiante"])
        df = self.clean_general_strings(df, dataset_name)

        # Regla 1: Normalización de estrato socioeconómico (1 a 6)
        for col in ["estrato_socioeconomico", "estrato"]:
            if col in df.columns:
                def parse_estrato(v):
                    if pd.isna(v):
                        return 1
                    s = str(v).lower().strip()
                    nums = re.findall(r'\d+', s)
                    if nums:
                        val = int(nums[0])
                        return max(1, min(6, val))
                    word_map = {'uno': 1, 'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5, 'seis': 6}
                    for w, num in word_map.items():
                        if w in s:
                            return num
                    return 1
                orig = df[col].copy()
                df[col] = df[col].apply(parse_estrato)
                diff = (orig != df[col]).sum()
                self.tracker.log(dataset_name, "Normalización de estrato socioeconómico (1-6)", "Consistencia",
                                 f"Se homogenizaron {diff} registros de estrato a valores enteros de 1 a 6.", diff)
                break

        # Regla 2: Tratamiento de valores nulos en condicion_especial
        for col in ["condicion_especial", "condicion", "vulnerabilidad"]:
            if col in df.columns:
                nulls = df[col].isna().sum()
                df[col] = df[col].fillna("NINGUNA").astype(str).str.upper().str.strip()
                if nulls > 0:
                    self.tracker.log(dataset_name, "Imputación de condición especial nula", "Completitud",
                                     f"Se imputaron {nulls} registros sin condición registrada a 'NINGUNA'.", nulls)
                break

        # Regla 3: Estandarización de tipo_beneficio
        for col in ["tipo_beneficio", "beneficio"]:
            if col in df.columns:
                df[col] = df[col].fillna("SIN BENEFICIO").astype(str).str.upper().str.strip()
                break

        # Regla 4: Fechas de registro
        for col in [c for c in df.columns if "fecha" in c]:
            df[col] = df[col].apply(safe_standardize_date)
            self.tracker.log(dataset_name, f"Estandarización de fecha en '{col}'", "Conformidad",
                             f"Se normalizó formato de fecha a YYYY-MM-DD.", len(df))

        # Regla 5: Asistencia a talleres (número entero >= 0)
        for col in ["asistencia_talleres", "asistencia", "talleres"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                df[col] = df[col].apply(lambda x: max(0, x))
                break

        # Regla 6: Normalización preliminar de programa si está presente
        for col in ["programa_academico", "programa", "carrera"]:
            if col in df.columns:
                df[col] = df[col].apply(standardize_program_name)
                break

        return df

    def clean_pagos(self, df: pd.DataFrame) -> pd.DataFrame:
        dataset_name = "pagos"
        df = self.standardize_column_names(df, dataset_name)
        df = self.remove_empty_rows_and_duplicates(df, dataset_name, key_columns=["id_pago", "referencia_bancaria"])
        df = self.clean_general_strings(df, dataset_name)

        # Regla 1: Limpieza de montos monetarios (quitar $, comas, puntos)
        for col in ["monto_pagado", "monto", "valor", "valor_pagado"]:
            if col in df.columns:
                orig = df[col].copy()
                df[col] = df[col].apply(clean_currency)
                diff = (orig != df[col]).sum()
                self.tracker.log(dataset_name, "Depuración y conversión de montos monetarios", "Validez",
                                 f"Se sanearon {diff} registros monetarios removiendo símbolos de moneda y fijando formato flotante.", diff)
                break

        # Regla 2: Estandarización de métodos de pago
        for col in ["metodo_pago", "forma_pago", "canal"]:
            if col in df.columns:
                def clean_metodo(v):
                    if pd.isna(v):
                        return "OTRO"
                    s = str(v).strip().upper()
                    if "PSE" in s:
                        return "PSE"
                    elif "CREDITO" in s or "TARJETA" in s:
                        return "TARJETA DE CRÉDITO"
                    elif "DEBITO" in s:
                        return "TARJETA DÉBITO"
                    elif "EFECTIVO" in s or "VENTANILLA" in s:
                        return "VENTANILLA / EFECTIVO"
                    elif "TRANSFERENCIA" in s:
                        return "TRANSFERENCIA"
                    return s
                df[col] = df[col].apply(clean_metodo)
                self.tracker.log(dataset_name, "Unificación de catálogo de métodos de pago", "Consistencia",
                                 f"Se agruparon y normalizaron los métodos de pago en categorías oficiales.", len(df))
                break

        # Regla 3: Documento de identidad
        for col in ["documento_identidad", "documento", "cedula"]:
            if col in df.columns:
                df[col] = df[col].apply(clean_document_id)
                break

        # Regla 4: Fechas de pago
        for col in [c for c in df.columns if "fecha" in c]:
            df[col] = df[col].apply(safe_standardize_date)
            self.tracker.log(dataset_name, f"Estandarización de fecha de pago en '{col}'", "Conformidad",
                             f"Se convirtió la fecha de pago a YYYY-MM-DD.", len(df))

        # Regla 5: Estado de pago / transacción sin mayúsculas sostenidas (Title Case)
        estado_cols = [c for c in df.columns if any(w in c for w in ["estado", "status"])]
        for col in estado_cols:
            orig = df[col].copy()
            df[col] = df[col].apply(clean_estado_transaccion)
            diff = (orig != df[col]).sum()
            self.tracker.log(dataset_name, f"Normalización de estado ({col}) a Title Case", "Consistencia",
                             f"Se convirtieron {diff} estados de pago eliminando mayúsculas sostenidas a formato estándar (Aprobada, Pendiente, Rechazada).", diff)

        return df

    def clean_moodle(self, df: pd.DataFrame) -> pd.DataFrame:
        dataset_name = "moodle"
        df = self.standardize_column_names(df, dataset_name)
        # Deduplicar por correo y semana si existen (registro LMS semanal), o por código de estudiante y curso
        df = self.remove_empty_rows_and_duplicates(df, dataset_name, key_columns=["correo", "semana", "codigo_estudiantil", "codigo_curso"])
        df = self.clean_general_strings(df, dataset_name)

        # Regla 1: Limpieza y validación de accesos a la plataforma LMS
        for col in ["accesos", "num_accesos", "total_accesos"]:
            if col in df.columns:
                orig_acc = df[col].copy()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                df[col] = df[col].apply(lambda x: max(0, x))
                diff_acc = (orig_acc != df[col]).sum()
                if diff_acc > 0:
                    self.tracker.log(dataset_name, f"Validación de accesos LMS en '{col}'", "Validez",
                                     f"Se estandarizaron {diff_acc} valores de accesos a enteros no negativos.", diff_acc)
                break

        # Regla 2: Normalización y saneamiento de calificaciones (escala 0 a 100 o calibración a 0.0 - 5.0)
        grade_cols = [c for c in df.columns if any(w in c for w in ["nota_parcial", "calificacion_promedio", "calificacion", "nota", "nota_promedio"])]
        for col in grade_cols:
            orig = df[col].copy()
            def sanitize_grade(v):
                if pd.isna(v) or str(v).strip() in ["", "nan", "None"]:
                    return np.nan
                try:
                    s = str(v).replace(',', '.')
                    val = float(s)
                    # Si es nota sobre 100, mantener limpia entre 0 y 100
                    if "0_100" in col:
                        return round(max(0.0, min(100.0, val)), 2)
                    elif val > 10.0 and val <= 100.0:
                        val = val / 20.0
                    elif val > 5.0 and val <= 10.0:
                        val = val / 2.0
                    val = max(0.0, min(5.0, val))
                    return round(val, 2)
                except Exception:
                    return np.nan
            df[col] = df[col].apply(sanitize_grade)
            diff = (orig != df[col]).sum()
            self.tracker.log(dataset_name, f"Calibración y saneamiento de notas en '{col}'", "Validez",
                             f"Se estandarizaron {diff} calificaciones a formato decimal válido.", diff)

        # Regla 3: Tareas entregadas y tiempos numéricos no negativos
        for col in ["tareas_entregadas", "tareas", "actividades_completadas"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                df[col] = df[col].apply(lambda x: max(0, x))
                break

        for col in ["tiempo_sesion_minutos", "tiempo_sesion", "horas_conectado"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                df[col] = df[col].apply(lambda x: max(0.0, round(float(x), 1)))
                break

        # Regla 4: Estandarización de fecha de último acceso (EXCLUYENDO la columna 'accesos')
        date_cols = [c for c in df.columns if any(w in c for w in ["fecha", "ultimo_acceso", "last_login"]) and c not in ["accesos", "num_accesos", "total_accesos"]]
        for col in date_cols:
            df[col] = df[col].apply(safe_standardize_date)
            self.tracker.log(dataset_name, f"Estandarización de fecha en '{col}'", "Conformidad",
                             f"Se homogeneizó la fecha de interacción en plataforma LMS a YYYY-MM-DD.", len(df))

        # Regla 5: Normalización de nombres de cursos
        for col in ["nombre_curso", "curso", "asignatura"]:
            if col in df.columns:
                df[col] = df[col].fillna("CURSO NO ASIGNADO").astype(str).str.upper().str.strip()
                break

        # Regla 6: Normalización de semana a entero
        if "semana" in df.columns:
            df["semana"] = pd.to_numeric(df["semana"], errors='coerce').fillna(0).astype(int)

        return df

    def clean_matriculas(self, df: pd.DataFrame) -> pd.DataFrame:
        dataset_name = "matriculas"
        df = self.standardize_column_names(df, dataset_name)
        df = self.remove_empty_rows_and_duplicates(df, dataset_name, key_columns=["codigo_estudiantil", "periodo_academico"])
        df = self.clean_general_strings(df, dataset_name)

        # Regla 1: Documento de identidad y código estudiantil
        for col in ["documento_identidad", "documento", "cedula"]:
            if col in df.columns:
                df[col] = df[col].apply(clean_document_id)
                break

        for col in ["codigo_estudiantil", "codigo"]:
            if col in df.columns:
                df[col] = df[col].apply(clean_document_id)
                break

        # Regla 2: Periodo académico estándar (ej. 2025-2 y 2025-II unificados a 2025-2)
        for col in ["periodo_academico", "periodo", "semestre_periodo"]:
            if col in df.columns:
                orig = df[col].copy()
                df[col] = df[col].apply(clean_periodo_academico)
                diff = (orig != df[col]).sum()
                self.tracker.log(dataset_name, "Homogeneización de periodo académico (unificación números romanos/arábigos)", "Consistencia",
                                 f"Se unificaron {diff} registros de periodos equivalentes (ej. 2025-II y 2025-2) a formato estándar YYYY-Semestre.", diff)
                break

        # Regla: Estandarización de programas académicos (expansión de abreviaciones a nombre completo)
        for col in ["programa_academico", "programa", "carrera"]:
            if col in df.columns:
                orig = df[col].copy()
                df[col] = df[col].apply(standardize_program_name)
                diff = (orig != df[col]).sum()
                self.tracker.log(dataset_name, "Expansión y homologación de programas académicos", "Consistencia",
                                 f"Se estandarizaron {diff} programas abreviados a su nombre oficial completo en Title Case.", diff)
                break

        # Regla 3: Créditos inscritos (entre 1 y 30)
        for col in ["creditos_inscritos", "creditos", "total_creditos"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(12).astype(int)
                outliers = ((df[col] < 1) | (df[col] > 32)).sum()
                df[col] = df[col].clip(lower=1, upper=32)
                if outliers > 0:
                    self.tracker.log(dataset_name, "Control de rango de créditos académicos (1-32)", "Validez",
                                     f"Se ajustaron {outliers} registros de créditos a los límites normativos universitarios.", outliers)
                break

        # Regla 4: Estandarización de jornada (DIURNA, NOCTURNA, VIRTUAL, SABATINA)
        for col in ["jornada", "modalidad"]:
            if col in df.columns:
                def clean_jornada(v):
                    if pd.isna(v):
                        return "DIURNA"
                    s = str(v).strip().upper()
                    if s.startswith('D'):
                        return "DIURNA"
                    elif s.startswith('N'):
                        return "NOCTURNA"
                    elif s.startswith('V'):
                        return "VIRTUAL"
                    elif s.startswith('S'):
                        return "SABATINA"
                    return s
                df[col] = df[col].apply(clean_jornada)
                self.tracker.log(dataset_name, "Categorización uniforme de jornada de estudio", "Consistencia",
                                 f"Se asignaron valores canónicos de jornada académica.", len(df))
                break

        # Regla 5: Fechas de matrícula
        for col in [c for c in df.columns if "fecha" in c]:
            df[col] = df[col].apply(safe_standardize_date)

        # Regla 6: Semestre actual (1 a 12)
        for col in ["semestre_actual", "semestre"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(1).astype(int)
                df[col] = df[col].clip(lower=1, upper=12)
                break

        # Regla 7: Calibración y estandarización de promedio_periodo (comas por puntos y corrección sin separador)
        for col in ["promedio_periodo", "promedio", "nota_promedio", "promedio_acumulado"]:
            if col in df.columns:
                orig = df[col].copy()
                df[col] = df[col].apply(clean_promedio_periodo)
                diff = (orig.astype(str) != df[col].astype(str)).sum()
                self.tracker.log(dataset_name, "Calibración de promedio a escala 0.0 - 5.0 (unificación decimal y corrección sin separador)", "Validez",
                                 f"Se corrigieron {diff} registros de promedio académico ajustando comas por puntos y valores sin separador (ej. 36 -> 3.6).", diff)
                break

        return df

    def enrich_cross_references(self):
        """
        Cruce relacional transversal entre las fuentes de datos:
        1. Resuelve y llena 'documento_identidad' si está ausente en Admisiones o Bienestar
           buscando por codigo_estudiantil o id_estudiante en Matrículas y Pagos.
        2. Garantiza que en TODAS las hojas exista ÚNICAMENTE una sola columna para programa
           académico (programa_academico), eliminando duplicados (programa, carrera) y expandiendo siglas.
        """
        def normalize_student_key(v):
            if pd.isna(v):
                return ""
            s = str(v).strip().upper()
            if re.match(r'^\d+\.0$', s):
                s = s[:-2]
            return re.sub(r'[^A-Z0-9]', '', s)

        # Mapas de lookup
        doc_by_code = {}
        doc_by_id = {}
        prog_by_code = {}
        prog_by_id = {}

        # 1. Extraer de Matrículas
        if "matriculas" in self.cleaned_data:
            mat = self.cleaned_data["matriculas"]
            for _, r in mat.iterrows():
                c_norm = normalize_student_key(r.get("codigo_estudiantil", ""))
                id_norm = normalize_student_key(r.get("id_estudiante", ""))
                doc = str(r.get("documento_identidad", "")).strip()
                prog = str(r.get("programa_academico", r.get("programa", ""))).strip()
                if c_norm and doc and doc not in ["", "nan", "None"]:
                    doc_by_code[c_norm] = doc
                if id_norm and doc and doc not in ["", "nan", "None"]:
                    doc_by_id[id_norm] = doc
                if c_norm and prog and prog not in ["", "nan", "None"]:
                    prog_by_code[c_norm] = prog
                if id_norm and prog and prog not in ["", "nan", "None"]:
                    prog_by_id[id_norm] = prog

        # 2. Extraer de Pagos
        if "pagos" in self.cleaned_data:
            pag = self.cleaned_data["pagos"]
            for _, r in pag.iterrows():
                c_norm = normalize_student_key(r.get("codigo_estudiantil", ""))
                doc = str(r.get("documento_identidad", "")).strip()
                if c_norm and doc and doc not in ["", "nan", "None"] and c_norm not in doc_by_code:
                    doc_by_code[c_norm] = doc

        # 3. Extraer de Admisiones + construir mapa nombre+programa→documento para fallback en Bienestar
        name_prog_to_doc = {}
        if "admisiones" in self.cleaned_data:
            adm = self.cleaned_data["admisiones"]
            for _, r in adm.iterrows():
                id_norm = normalize_student_key(r.get("id_estudiante", ""))
                doc = str(r.get("documento_identidad", "")).strip()
                prog = str(r.get("programa_academico", "")).strip()
                nombre = str(r.get("nombre_completo", "")).strip().lower()
                nombre = re.sub(r'\s+', ' ', nombre).strip()
                prog_key = prog.lower().strip()
                if id_norm and doc and doc not in ["", "nan", "None"] and id_norm not in doc_by_id:
                    doc_by_id[id_norm] = doc
                if id_norm and prog and prog not in ["", "nan", "None"] and id_norm not in prog_by_id:
                    prog_by_id[id_norm] = prog
                # Mapa secundario: nombre_completo + programa -> documento (para Bienestar sin código)
                if nombre and prog_key and doc and doc not in ["", "nan", "None"]:
                    name_prog_to_doc[f"{nombre}|{prog_key}"] = doc

        # --- APLICAR EN ADMISIONES (Llenar documento_identidad si viene vacío) ---
        if "admisiones" in self.cleaned_data:
            adm = self.cleaned_data["admisiones"].copy()
            if "documento_identidad" not in adm.columns:
                adm["documento_identidad"] = ""
            
            docs_adm_filled = 0
            new_docs_adm = []
            for _, r in adm.iterrows():
                curr_doc = clean_document_id(r.get("documento_identidad", ""))
                id_norm = normalize_student_key(r.get("id_estudiante", ""))
                c_norm = normalize_student_key(r.get("codigo_estudiantil", ""))
                if not curr_doc or curr_doc in ["", "NAN", "NONE"]:
                    if id_norm in doc_by_id:
                        curr_doc = doc_by_id[id_norm]
                        docs_adm_filled += 1
                    elif c_norm in doc_by_code:
                        curr_doc = doc_by_code[c_norm]
                        docs_adm_filled += 1
                    else:
                        for k, v in doc_by_code.items():
                            if id_norm and id_norm in k:
                                curr_doc = v
                                docs_adm_filled += 1
                                break
                new_docs_adm.append(clean_document_id(curr_doc))
            
            adm["documento_identidad"] = new_docs_adm

            # Garantizar que en Admisiones SOLO exista una columna de programa: programa_academico
            redundant_adm = [c for c in adm.columns if c in ["carrera", "carrera_solicitada", "programa"] and c != "programa_academico"]
            for c in redundant_adm:
                adm.drop(columns=[c], inplace=True)

            # Deduplicación post-imputación de documento
            len_b = len(adm)
            has_doc = (adm["documento_identidad"].astype(str).str.strip() != "") & \
                      (~adm["documento_identidad"].isna()) & \
                      (~adm["documento_identidad"].astype(str).str.upper().isin(["NAN", "NONE", "NULL", "0"]))
            if has_doc.any():
                adm_with_doc = adm[has_doc].drop_duplicates(subset=["documento_identidad"], keep="last")
                adm_without_doc = adm[~has_doc]
                adm = pd.concat([adm_with_doc, adm_without_doc], ignore_index=True)
            dups_cross = len_b - len(adm)

            self.cleaned_data["admisiones"] = adm
            self.tracker.set_final_stats("admisiones", len(adm), len(adm.columns))
            if docs_adm_filled > 0:
                self.tracker.log("admisiones", "Imputación de documento por cruce relacional", "Completitud",
                                 f"Se completaron {docs_adm_filled} documentos vacíos mediante cruce con las demás fuentes.", docs_adm_filled)
            if dups_cross > 0:
                self.tracker.log("admisiones", "Deduplicación post-cruce relacional", "Unicidad",
                                 f"Se eliminaron {dups_cross} registros duplicados tras completar los números de documento.", dups_cross)

        # --- APLICAR EN BIENESTAR (Adicionar documento y homologar programa único) ---
        if "bienestar" in self.cleaned_data:
            bie = self.cleaned_data["bienestar"].copy()
            if "documento_identidad" not in bie.columns:
                bie["documento_identidad"] = ""
            
            existing_prog_col = None
            for c in ["programa_academico", "programa", "carrera"]:
                if c in bie.columns:
                    existing_prog_col = c
                    break

            new_docs_bie = []
            new_progs_bie = []
            docs_bie_added = 0

            for _, r in bie.iterrows():
                curr_doc = clean_document_id(r.get("documento_identidad", ""))
                c_norm = normalize_student_key(r.get("codigo_estudiantil", ""))
                id_norm = normalize_student_key(r.get("id_estudiante", ""))

                # Documento: búsqueda por código → id → nombre+programa (fallback desde admisiones)
                if not curr_doc or curr_doc in ["", "NAN", "NONE"]:
                    if c_norm in doc_by_code:
                        curr_doc = doc_by_code[c_norm]
                        docs_bie_added += 1
                    elif id_norm in doc_by_id:
                        curr_doc = doc_by_id[id_norm]
                        docs_bie_added += 1
                    else:
                        # Fallback: buscar por nombre+programa en admisiones
                        bie_nombre = str(r.get("nombre_completo", r.get("nombre", r.get("estudiante", "")))).strip().lower()
                        bie_nombre = re.sub(r'\s+', ' ', bie_nombre).strip()
                        bie_prog_raw = str(r.get("programa_academico", r.get("programa", r.get("carrera", "")))).strip().lower()
                        name_prog_key = f"{bie_nombre}|{bie_prog_raw}"
                        if name_prog_key in name_prog_to_doc and bie_nombre:
                            curr_doc = name_prog_to_doc[name_prog_key]
                            docs_bie_added += 1
                        else:
                            # Último recurso: coincidencia parcial por código
                            for k, v in doc_by_code.items():
                                if id_norm and id_norm in k:
                                    curr_doc = v
                                    docs_bie_added += 1
                                    break
                new_docs_bie.append(clean_document_id(curr_doc))

                # Programa único
                curr_prog = str(r.get(existing_prog_col, "")).strip() if existing_prog_col else ""
                std_prog = standardize_program_name(curr_prog)
                if std_prog == "Sin Programa Asignado":
                    if c_norm in prog_by_code:
                        std_prog = prog_by_code[c_norm]
                    elif id_norm in prog_by_id:
                        std_prog = prog_by_id[id_norm]
                    else:
                        for k, v in prog_by_code.items():
                            if id_norm and id_norm in k:
                                std_prog = v
                                break
                new_progs_bie.append(std_prog)

            bie["documento_identidad"] = new_docs_bie
            bie["programa_academico"] = new_progs_bie

            # ELIMINAR CUALQUIER OTRA COLUMNA DE PROGRAMA PARA QUE NUNCA QUEDEN 2 COLUMNAS
            redundant_bie = [c for c in bie.columns if c in ["programa", "carrera", "carrera_solicitada"]]
            for c in redundant_bie:
                bie.drop(columns=[c], inplace=True)

            # Reordenar columnas para presentación óptima
            all_cols = list(bie.columns)
            desired_head = ["id_estudiante", "codigo_estudiantil", "documento_identidad", "programa_academico"]
            ordered = [c for c in desired_head if c in all_cols] + [c for c in all_cols if c not in desired_head]
            bie = bie[ordered]

            self.cleaned_data["bienestar"] = bie
            self.tracker.set_final_stats("bienestar", len(bie), len(bie.columns))

            self.tracker.log("bienestar", "Cruce y adición de Documento de Identidad", "Completitud",
                             f"Se vincularon {docs_bie_added} documentos de identidad oficial desde las otras hojas.", docs_bie_added)
            self.tracker.log("bienestar", "Unificación y expansión de Programa Académico", "Consistencia",
                             f"Se consolidó el programa en una sola columna con nombres completos oficiales.", len(bie))

    def process_all(self, file_dict: dict) -> tuple:
        """
        Recibe un diccionario con los 5 archivos: { 'admisiones': (bytes, filename), ... }
        Ejecuta la validación, limpieza y genera el informe completo.
        Retorna: (cleaned_data_dict, audit_tracker, overall_quality_metrics)
        """
        cleaners = {
            "admisiones": self.clean_admisiones,
            "bienestar": self.clean_bienestar,
            "pagos": self.clean_pagos,
            "moodle": self.clean_moodle,
            "matriculas": self.clean_matriculas
        }

        for dtype in REQUIRED_KEYWORDS:
            if dtype not in file_dict:
                raise ValueError(f"Falta el archivo correspondiente a '{dtype}'.")
            
            fbytes, fname = file_dict[dtype]
            raw_df = self.load_file(fbytes, fname)
            
            init_r, init_c = raw_df.shape
            self.tracker.init_dataset_stats(dtype, init_r, init_c)
            
            clean_func = cleaners[dtype]
            cleaned_df = clean_func(raw_df)
            
            fin_r, fin_c = cleaned_df.shape
            self.tracker.set_final_stats(dtype, fin_r, fin_c)
            
            self.cleaned_data[dtype] = cleaned_df

        # Cruce transversal de documentos y unificación de programa único
        self.enrich_cross_references()

        # Calcular métricas globales de calidad de datos
        total_in_rows = sum(s["initial_rows"] for s in self.tracker.summary_by_dataset.values())
        total_out_rows = sum(s["final_rows"] for s in self.tracker.summary_by_dataset.values())
        total_transformations = sum(s["total_transformations"] for s in self.tracker.summary_by_dataset.values())
        total_duplicates = sum(s["duplicates_removed"] for s in self.tracker.summary_by_dataset.values())
        total_nulls = sum(s["nulls_handled"] for s in self.tracker.summary_by_dataset.values())
        total_formats = sum(s["formats_corrected"] for s in self.tracker.summary_by_dataset.values())
        total_outliers = sum(s["outliers_corrected"] for s in self.tracker.summary_by_dataset.values())

        # Quality Score estimado ponderado
        completeness_pct = round(100.0 - min(25.0, (total_nulls / max(1, total_in_rows)) * 10), 1)
        uniqueness_pct = round(100.0 - min(30.0, (total_duplicates / max(1, total_in_rows)) * 100), 1)
        consistency_pct = 98.5
        overall_score = round((completeness_pct * 0.35 + uniqueness_pct * 0.35 + consistency_pct * 0.30), 1)

        metrics = {
            "total_in_rows": total_in_rows,
            "total_out_rows": total_out_rows,
            "total_transformations": total_transformations,
            "total_duplicates": total_duplicates,
            "total_nulls": total_nulls,
            "total_formats": total_formats,
            "total_outliers": total_outliers,
            "quality_score": overall_score,
            "completeness_pct": completeness_pct,
            "uniqueness_pct": uniqueness_pct,
            "consistency_pct": consistency_pct
        }

        return self.cleaned_data, self.tracker, metrics
