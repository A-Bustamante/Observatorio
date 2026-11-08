import os
import openpyxl
from etl_engine import ETLProcessor
from excel_exporter import build_consolidated_clean_excel
from database_manager import save_clean_data_to_db, get_db_stats

sample_files = [
    'admisiones_2024.csv',
    'bienestar_estudiantil.csv',
    'pagos_semestre.xlsx',
    'moodle_actividad.csv',
    'matriculas_consolidadas.xlsx'
]

file_dict = {}
for fname in sample_files:
    from etl_engine import identify_dataset_type
    kw = identify_dataset_type(fname)
    with open(os.path.join('sample_data', fname), 'rb') as f:
        file_dict[kw] = (f.read(), fname)

processor = ETLProcessor()
cleaned_dict, tracker, metrics = processor.process_all(file_dict)

print('=== 1. VERIFICACIÓN ADMISIONES ===')
adm = cleaned_dict['admisiones']
print('Columnas en Admisiones:', list(adm.columns))
for _, r in adm[['id_estudiante', 'documento_identidad', 'nombre_completo', 'programa_academico']].iterrows():
    print('  ID:', r['id_estudiante'], '- Doc:', r['documento_identidad'], '- Nombre:', r['nombre_completo'], '- Prog:', r['programa_academico'])

print('\n=== 2. VERIFICACIÓN PAGOS (ESTADO_PAGO) ===')
pag = cleaned_dict['pagos']
print('Columnas en Pagos:', list(pag.columns))
for c in [col for col in pag.columns if 'estado' in col]:
    print(f'Valores en columna {c}:', pag[c].tolist())

print('\n=== 3. VERIFICACIÓN BIENESTAR ===')
bie = cleaned_dict['bienestar']
print('Columnas en Bienestar:', list(bie.columns))
for _, r in bie[['id_estudiante', 'codigo_estudiantil', 'documento_identidad', 'programa_academico']].iterrows():
    print('  ID:', r['id_estudiante'], '- Cod:', r['codigo_estudiantil'], '- Doc:', r['documento_identidad'], '- Prog:', r['programa_academico'])

print('\n=== 4. VERIFICACIÓN HOJAS EXCEL ===')
excel_bytes = build_consolidated_clean_excel(cleaned_dict, tracker, metrics)
wb = openpyxl.load_workbook(openpyxl.reader.excel.BytesIO(excel_bytes))
print('Hojas presentes en el Excel:', wb.sheetnames)
assert 'Vista_Estudiante_360' not in wb.sheetnames, 'ERROR: Vista_Estudiante_360 no debe estar'

print('\n=== 5. VERIFICACIÓN BASE DE DATOS SQLITE ===')
db_res = save_clean_data_to_db(cleaned_dict, tracker.logs)
print('Tablas creadas y actualizadas en SQLite:', db_res['tables_saved'])
print('Conteo de registros en SQLite:', get_db_stats())
print('\nTODO VERIFICADO EXITOSAMENTE!')

