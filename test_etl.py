import os
from etl_engine import ETLProcessor, validate_uploaded_files
from excel_exporter import build_consolidated_clean_excel

def test_pipeline():
    sample_files = [
        "admisiones_2024.csv",
        "bienestar_estudiantil.csv",
        "pagos_semestre.xlsx",
        "moodle_actividad.csv",
        "matriculas_consolidadas.xlsx"
    ]
    
    is_valid, mapping, missing, unrecognized = validate_uploaded_files(sample_files)
    print("Validación de nombres:", is_valid, "Mapping:", mapping, "Missing:", missing)
    assert is_valid, "Deberían ser válidos los 5 archivos"

    file_dict = {}
    for kw, fname in mapping.items():
        path = os.path.join("sample_data", fname)
        with open(path, "rb") as f:
            file_dict[kw] = (f.read(), fname)

    processor = ETLProcessor()
    cleaned_dict, tracker, metrics = processor.process_all(file_dict)
    
    print("\n--- RESUMEN DE PROCESAMIENTO ---")
    print(f"Total registros entrada: {metrics['total_in_rows']}")
    print(f"Total registros salida:  {metrics['total_out_rows']}")
    print(f"Transformaciones:        {metrics['total_transformations']}")
    print(f"Duplicados eliminados:   {metrics['total_duplicates']}")
    print(f"Score de calidad:        {metrics['quality_score']}%")
    print(f"Total reglas en log:     {len(tracker.logs)}")

    excel_bytes = build_consolidated_clean_excel(cleaned_dict, tracker, metrics)
    print(f"Excel generado correctamente, tamaño: {len(excel_bytes)} bytes")
    with open("sample_data/Prueba_ETL_Consolidado_Limpio.xlsx", "wb") as f:
        f.write(excel_bytes)
    print("Guardado en 'sample_data/Prueba_ETL_Consolidado_Limpio.xlsx'")

if __name__ == "__main__":
    test_pipeline()

