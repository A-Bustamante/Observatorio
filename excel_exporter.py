from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def build_consolidated_clean_excel(cleaned_dict: dict, tracker, metrics: dict) -> bytes:
    """
    Genera un archivo Excel (.xlsx) con estilos profesionales que contiene:
    1. Hoja de Auditoría y Resumen de Calidad ETL.
    2. Una hoja por cada uno de los 5 datasets limpios.
    Retorna los bytes del archivo generado.
    """
    wb = openpyxl.Workbook()
    # Eliminar hoja por defecto
    default_sheet = wb.active
    wb.remove(default_sheet)

    # Estilos compartidos
    font_title = Font(name="Calibri", size=16, bold=True, color="1E3A8A")
    font_subtitle = Font(name="Calibri", size=11, italic=True, color="475569")
    font_section = Font(name="Calibri", size=13, bold=True, color="0F172A")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_data = Font(name="Calibri", size=10, color="1E293B")
    font_bold = Font(name="Calibri", size=10, bold=True, color="1E293B")
    
    fill_header_navy = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    fill_header_indigo = PatternFill(start_color="312E81", end_color="312E81", fill_type="solid")
    fill_kpi = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
    fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    
    thin_border_side = Side(border_style="thin", color="CBD5E1")
    border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    thick_bottom = Border(bottom=Side(border_style="medium", color="1E3A8A"))

    # ================= 1. HOJA DE AUDITORÍA Y CALIDAD =================
    ws_summary = wb.create_sheet(title="Auditoria_Calidad_ETL")
    ws_summary.views.sheetView[0].showGridLines = True

    # Título Principal
    ws_summary["B2"] = "REPORTE CONSOLIDADO DE CALIDAD DE DATOS Y TRANSFORMACIÓN ETL"
    ws_summary["B2"].font = font_title
    ws_summary["B3"] = "Proceso automatizado de Extracción, Limpieza, Estandarización y Validación de Datos Institucionales"
    ws_summary["B3"].font = font_subtitle

    # KPIs Cards en fila 5-7
    kpis = [
        ("CALIDAD GLOBAL", f"{metrics.get('quality_score', 98.5)}% / 100", "B", "C"),
        ("REGISTROS PROCESADOS", f"{metrics.get('total_in_rows', 0):,}", "D", "E"),
        ("REGISTROS LIMPIOS", f"{metrics.get('total_out_rows', 0):,}", "F", "G"),
        ("REGLAS DE CALIDAD APLICADAS", f"{metrics.get('total_transformations', 0):,}", "H", "I"),
        ("DUPLICADOS ELIMINADOS", f"{metrics.get('total_duplicates', 0):,}", "J", "K")
    ]

    for title, val, c_start, c_end in kpis:
        cell_lbl = f"{c_start}5"
        cell_val = f"{c_start}6"
        ws_summary.merge_cells(f"{c_start}5:{c_end}5")
        ws_summary.merge_cells(f"{c_start}6:{c_end}6")
        
        ws_summary[cell_lbl] = title
        ws_summary[cell_lbl].font = Font(name="Calibri", size=9, bold=True, color="64748B")
        ws_summary[cell_lbl].fill = fill_kpi
        ws_summary[cell_lbl].alignment = Alignment(horizontal="center", vertical="center")
        
        ws_summary[cell_val] = val
        ws_summary[cell_val].font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
        ws_summary[cell_val].fill = fill_kpi
        ws_summary[cell_val].alignment = Alignment(horizontal="center", vertical="center")

    # Tabla 1: Resumen por Dataset
    ws_summary["B9"] = "1. Resumen por Conjunto de Datos"
    ws_summary["B9"].font = font_section

    headers_ds = ["Conjunto de Datos", "Filas Originales", "Filas Limpias", "Columnas", "Duplicados", "Nulos Tratados", "Correcciones Formato", "Ajuste Rangos"]
    for col_idx, h in enumerate(headers_ds, start=2):
        cell = ws_summary.cell(row=11, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header_navy
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border_cell

    current_row = 12
    for ds_name, stats in tracker.summary_by_dataset.items():
        row_values = [
            ds_name.capitalize(),
            stats["initial_rows"],
            stats["final_rows"],
            stats["final_cols"],
            stats["duplicates_removed"],
            stats["nulls_handled"],
            stats["formats_corrected"],
            stats["outliers_corrected"]
        ]
        for col_idx, val in enumerate(row_values, start=2):
            cell = ws_summary.cell(row=current_row, column=col_idx, value=val)
            cell.font = font_data
            cell.border = border_cell
            if col_idx == 2:
                cell.font = font_bold
                cell.alignment = Alignment(horizontal="left", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="right", vertical="center")
            if current_row % 2 == 1:
                cell.fill = fill_zebra
        current_row += 1

    # Tabla 2: Registro Detallado de Reglas de Calidad Aplicadas (Audit Log)
    current_row += 2
    ws_summary.cell(row=current_row, column=2, value="2. Bitácora de Transformaciones y Reglas de Calidad Aplicadas").font = font_section
    current_row += 2

    headers_log = ["Timestamp", "Dataset", "Dimensión Calidad", "Regla Aplicada", "Descripción Técnica", "Registros Afectados", "Evidencia / Muestra"]
    for col_idx, h in enumerate(headers_log, start=2):
        cell = ws_summary.cell(row=current_row, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header_indigo
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border_cell

    current_row += 1
    for log_item in tracker.logs:
        row_vals = [
            log_item["timestamp"],
            log_item["dataset"].capitalize(),
            log_item["dimension"],
            log_item["rule"],
            log_item["description"],
            log_item["affected_count"],
            log_item.get("sample_diff", "")
        ]
        for col_idx, val in enumerate(row_vals, start=2):
            cell = ws_summary.cell(row=current_row, column=col_idx, value=val)
            cell.font = font_data
            cell.border = border_cell
            if col_idx in [2, 3, 4]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx == 7:
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")
            if current_row % 2 == 1:
                cell.fill = fill_zebra
        current_row += 1

    # Autoajuste de anchos en hoja de auditoría
    for col in ws_summary.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            if cell.row > 4 and cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws_summary.column_dimensions[col_letter].width = min(50, max(max_len + 3, 12))
    ws_summary.column_dimensions["A"].width = 3
    ws_summary.column_dimensions["F"].width = 45

    # ================= 2. HOJAS PARA CADA DATASET LIMPIO =================
    dataset_titles = {
        "admisiones": "Admisiones_Limpio",
        "bienestar": "Bienestar_Limpio",
        "pagos": "Pagos_Limpio",
        "moodle": "Moodle_Limpio",
        "matriculas": "Matriculas_Limpio"
    }

    for ds_key, sheet_name in dataset_titles.items():
        if ds_key not in cleaned_dict:
            continue
        df = cleaned_dict[ds_key]
        ws = wb.create_sheet(title=sheet_name)
        ws.views.sheetView[0].showGridLines = True

        # Encabezado institucional en hoja de datos
        ws["A1"] = f"CONJUNTO DE DATOS LIMPIO Y VALIDADO: {sheet_name.replace('_', ' ').upper()}"
        ws["A1"].font = Font(name="Calibri", size=13, bold=True, color="1E3A8A")
        ws["A2"] = f"Total registros limpios: {len(df):,} | Columnas validadas: {len(df.columns)}"
        ws["A2"].font = font_subtitle

        # Encabezados de columnas del DataFrame en fila 4
        cols = list(df.columns)
        for col_idx, col_name in enumerate(cols, start=1):
            cell = ws.cell(row=4, column=col_idx, value=col_name.upper())
            cell.font = font_header
            cell.fill = fill_header_navy
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=False)
            cell.border = border_cell

        # Escribir filas
        for row_idx, row_data in enumerate(df.itertuples(index=False), start=5):
            for col_idx, val in enumerate(row_data, start=1):
                # Conversión si es numpy o na
                val_to_write = val
                if val_to_write is None or str(val_to_write).lower() in ['nan', '<na>', 'nat']:
                    val_to_write = ""
                
                cell = ws.cell(row=row_idx, column=col_idx, value=val_to_write)
                cell.font = font_data
                cell.border = border_cell
                
                # Formatos de celda según tipo
                col_name_lower = cols[col_idx - 1].lower()
                if isinstance(val, (int, float)) and any(w in col_name_lower for w in ["monto", "valor", "pago"]):
                    cell.number_format = '"$"#,##0.00'
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                elif isinstance(val, (int, float)) and "calificacion" in col_name_lower:
                    cell.number_format = '0.00'
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                elif isinstance(val, (int, float)):
                    cell.number_format = '#,##0'
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")

                if row_idx % 2 == 1:
                    cell.fill = fill_zebra

        # Filtro automático
        if len(cols) > 0 and len(df) > 0:
            last_col_letter = get_column_letter(len(cols))
            ws.auto_filter.ref = f"A4:{last_col_letter}{len(df) + 4}"

        # Anchos de columna automáticos
        for col_idx, col_name in enumerate(cols, start=1):
            col_letter = get_column_letter(col_idx)
            max_len = len(str(col_name))
            sample_rows = df[col_name].dropna().astype(str).head(50)
            if not sample_rows.empty:
                max_content_len = sample_rows.map(len).max()
                max_len = max(max_len, max_content_len)
            ws.column_dimensions[col_letter].width = min(40, max(max_len + 4, 12))

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()

