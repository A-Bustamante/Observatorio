import os
import pandas as pd
import numpy as np

def generate_samples():
    os.makedirs("sample_data", exist_ok=True)
    
    # 1. ADMISIONES (CSV): nombres en mayúscula sostenida, T. Social, Ing. Inf., fechas variadas (2024-11-05, 12-dic-2024, etc.)
    admisiones_data = [
        {"id_estudiante": 101, "nombre": "CARLOS ANDRES PEREZ GOMEZ", "documento": "1.020.345.678", "fecha_nacimiento": "15/04/2001", "fecha_postulacion": "2024-11-05", "email": "carlos.perez@GMAIL.COM", "telefono": "300-123-4567", "carrera": "Ing. Inf.", "puntaje_icfes_o_ingreso": 380, "estado_admision": "admitido"},
        {"id_estudiante": 102, "nombre": "MARIA LUISA JARAMILLO", "documento": "1032456789", "fecha_nacimiento": "2002-08-20", "fecha_postulacion": "12-dic-2024", "email": "maria.jaramillo@yahoo.es", "telefono": "3158976543", "carrera": "MED", "puntaje_icfes_o_ingreso": 445, "estado_admision": "ADMITIDO"},
        {"id_estudiante": 103, "nombre": "JUAN DAVID CASTRO", "documento": "CC-1098765432", "fecha_nacimiento": "02/11/2000", "fecha_postulacion": "15/10/2024", "email": "juan.castro", "telefono": "3104561122", "carrera": "ADM. EMPRESAS", "puntaje_icfes_o_ingreso": 310, "estado_admision": "en revision"},
        {"id_estudiante": 104, "nombre": "ANA SOFIA VELEZ", "documento": "1045678123", "fecha_nacimiento": "1999-12-05", "fecha_postulacion": "20-nov-2024", "email": "ana.velez@hotmail.com", "telefono": "320-776-8899", "carrera": "T. Social", "puntaje_icfes_o_ingreso": 590, "estado_admision": "ADMITIDO"},
        {"id_estudiante": 105, "nombre": "LAURA VICTORIA MORA", "documento": "1011223344", "fecha_nacimiento": "10/01/2003", "fecha_postulacion": "2024/11/08", "email": "laura.mora@gmail.com", "telefono": "3119988776", "carrera": "PSI", "puntaje_icfes_o_ingreso": -20, "estado_admision": "RECHAZADO"},
        # Duplicado exacto de 102
        {"id_estudiante": 102, "nombre": "MARIA LUISA JARAMILLO", "documento": "1032456789", "fecha_nacimiento": "2002-08-20", "fecha_postulacion": "12-dic-2024", "email": "maria.jaramillo@yahoo.es", "telefono": "3158976543", "carrera": "MED", "puntaje_icfes_o_ingreso": 445, "estado_admision": "ADMITIDO"},
        # Fila vacía
        {"id_estudiante": None, "nombre": None, "documento": None, "fecha_nacimiento": None, "fecha_postulacion": None, "email": None, "telefono": None, "carrera": None, "puntaje_icfes_o_ingreso": None, "estado_admision": None},
        {"id_estudiante": 106, "nombre": "ESTEBAN QUINTERO LOPEZ", "documento": "", "fecha_nacimiento": "25-06-2002", "fecha_postulacion": "05/11/2024", "email": None, "telefono": "3182233445", "carrera": "ING. INDUSTRIAL", "puntaje_icfes_o_ingreso": 360, "estado_admision": "admitido"},
        {"id_estudiante": 107, "nombre": "VALERIA RESTREPO MONTOYA", "documento": "1055443322", "fecha_nacimiento": "2001/03/14", "fecha_postulacion": "12-diciembre-2024", "email": "valeria.restrepo@outlook.com", "telefono": None, "carrera": "DIS. GRAFICO", "puntaje_icfes_o_ingreso": 340, "estado_admision": "ADMITIDO"}
    ]
    pd.DataFrame(admisiones_data).to_csv("sample_data/admisiones_2024.csv", index=False, encoding="utf-8")

    # 2. BIENESTAR (CSV): programa abreviado y SIN número de documento
    bienestar_data = [
        {"id_estudiante": 101, "codigo_estudiantil": "EST-101", "programa": "Ing. Inf.", "tipo_beneficio": "subsidio alimentario", "estrato_socioeconomico": "Estrato 2", "condicion_especial": None, "fecha_registro": "01/02/2024", "asistencia_talleres": "5", "estado_beneficio": "ACTIVO"},
        {"id_estudiante": 102, "codigo_estudiantil": "EST-102", "programa": "MED", "tipo_beneficio": "BECA EXCELENCIA", "estrato_socioeconomico": "3", "condicion_especial": "desplazamiento", "fecha_registro": "2024-02-05", "asistencia_talleres": "8", "estado_beneficio": "activo"},
        {"id_estudiante": 103, "codigo_estudiantil": "EST-103", "programa": "ADM", "tipo_beneficio": "monitoria academica", "estrato_socioeconomico": "DOS", "condicion_especial": None, "fecha_registro": "10/02/2024", "asistencia_talleres": 3, "estado_beneficio": "ACTIVO"},
        {"id_estudiante": 104, "codigo_estudiantil": "EST-104", "programa": "T. Social", "tipo_beneficio": "deporte formativo", "estrato_socioeconomico": "Estrato 4", "condicion_especial": "DEPORTISTA DESTACADO", "fecha_registro": "2024-02-12", "asistencia_talleres": 12, "estado_beneficio": "ACTIVO"},
        {"id_estudiante": 105, "codigo_estudiantil": "EST-105", "programa": "PSI", "tipo_beneficio": "apoyo psicologico", "estrato_socioeconomico": "1", "condicion_especial": None, "fecha_registro": "2024-02-15", "asistencia_talleres": -2, "estado_beneficio": "EN SEGUIMIENTO"},
        {"id_estudiante": 106, "codigo_estudiantil": "EST-106", "programa": "IND", "tipo_beneficio": "subsidio transporte", "estrato_socioeconomico": "estrato uno", "condicion_especial": "POBLACION INDIGENA", "fecha_registro": "2024-02-18", "asistencia_talleres": 4, "estado_beneficio": "ACTIVO"},
        # Duplicado
        {"id_estudiante": 101, "codigo_estudiantil": "EST-101", "programa": "Ing. Inf.", "tipo_beneficio": "subsidio alimentario", "estrato_socioeconomico": "Estrato 2", "condicion_especial": None, "fecha_registro": "01/02/2024", "asistencia_talleres": "5", "estado_beneficio": "ACTIVO"}
    ]
    pd.DataFrame(bienestar_data).to_csv("sample_data/bienestar_estudiantil.csv", index=False, encoding="utf-8")

    # 3. PAGOS (EXCEL): columna literalmente nombrada 'estado_pago' en mayúsculas sostenidas
    pagos_data = [
        {"id_pago": "PAG-001", "codigo_estudiantil": "EST-101", "documento_identidad": "1020345678", "concepto_pago": "Matricula Ordinaria", "monto_pagado": "$ 2.450.000", "metodo_pago": "pse", "fecha_pago": "15/01/2024", "referencia_bancaria": "REF-998811", "estado_pago": "APROBADA"},
        {"id_pago": "PAG-002", "codigo_estudiantil": "EST-102", "documento_identidad": "1032456789", "concepto_pago": "Matricula Beca Parcial", "monto_pagado": "$ 1.225.000,00", "metodo_pago": "TARJETA CREDITO", "fecha_pago": "18-01-2024", "referencia_bancaria": "REF-998812", "estado_pago": "APROBADA"},
        {"id_pago": "PAG-003", "codigo_estudiantil": "EST-103", "documento_identidad": "1098765432", "concepto_pago": "Matricula Ordinaria", "monto_pagado": "2450000", "metodo_pago": "Ventanilla Banco", "fecha_pago": "2024/01/22", "referencia_bancaria": "REF-998813", "estado_pago": "APROBADA"},
        {"id_pago": "PAG-004", "codigo_estudiantil": "EST-104", "documento_identidad": "1045678123", "concepto_pago": "Carnet y Seguro", "monto_pagado": "$ 85.000", "metodo_pago": "PSE", "fecha_pago": "25/01/2024", "referencia_bancaria": "REF-998814", "estado_pago": "APROBADA"},
        {"id_pago": "PAG-005", "codigo_estudiantil": "EST-105", "documento_identidad": "1011223344", "concepto_pago": "Derechos de Grado", "monto_pagado": "-150000", "metodo_pago": "efectivo", "fecha_pago": "28/01/2024", "referencia_bancaria": "REF-998815", "estado_pago": "RECHAZADA"},
        {"id_pago": "PAG-006", "codigo_estudiantil": "EST-106", "documento_identidad": "1088776655", "concepto_pago": "Matricula Extraordinaria", "monto_pagado": "$ 2.800.500", "metodo_pago": "TRANSFERENCIA", "fecha_pago": "02/02/2024", "referencia_bancaria": "REF-998816", "estado_pago": "APROBADA"},
        # Duplicado
        {"id_pago": "PAG-001", "codigo_estudiantil": "EST-101", "documento_identidad": "1020345678", "concepto_pago": "Matricula Ordinaria", "monto_pagado": "$ 2.450.000", "metodo_pago": "pse", "fecha_pago": "15/01/2024", "referencia_bancaria": "REF-998811", "estado_pago": "APROBADA"}
    ]
    pd.DataFrame(pagos_data).to_excel("sample_data/pagos_semestre.xlsx", index=False)

    # 4. MOODLE (CSV)
    moodle_data = [
        {"id_registro_moodle": 501, "codigo_estudiantil": "EST-101", "codigo_curso": "INF-301", "nombre_curso": "  Bases de Datos I ", "ultimo_acceso_plataforma": "12/03/2024", "tareas_entregadas": 10, "calificacion_promedio": 4.5, "tiempo_sesion_minutos": 450.5, "estado_participacion": "ACTIVO"},
        {"id_registro_moodle": 502, "codigo_estudiantil": "EST-102", "codigo_curso": "MED-204", "nombre_curso": "Anatomia Humana", "ultimo_acceso_plataforma": "2024-03-14", "tareas_entregadas": 14, "calificacion_promedio": 95.0, "tiempo_sesion_minutos": 820.0, "estado_participacion": "ACTIVO"},
        {"id_registro_moodle": 503, "codigo_estudiantil": "EST-103", "codigo_curso": "ADM-102", "nombre_curso": "Contabilidad Financiera", "ultimo_acceso_plataforma": "10/03/2024", "tareas_entregadas": 6, "calificacion_promedio": "3,8", "tiempo_sesion_minutos": 210, "estado_participacion": "REGULAR"},
        {"id_registro_moodle": 504, "codigo_estudiantil": "EST-104", "codigo_curso": "DER-201", "nombre_curso": "Derecho Constitucional", "ultimo_acceso_plataforma": "15/03/2024", "tareas_entregadas": 12, "calificacion_promedio": 4.8, "tiempo_sesion_minutos": 615.2, "estado_participacion": "ACTIVO"},
        {"id_registro_moodle": 505, "codigo_estudiantil": "EST-105", "codigo_curso": "PSI-105", "nombre_curso": "Psicologia General", "ultimo_acceso_plataforma": "01/03/2024", "tareas_entregadas": 2, "calificacion_promedio": 1.5, "tiempo_sesion_minutos": -30, "estado_participacion": "EN RIESGO"},
        {"id_registro_moodle": 506, "codigo_estudiantil": "EST-106", "codigo_curso": "IND-302", "nombre_curso": "Investigacion de Operaciones", "ultimo_acceso_plataforma": "14/03/2024", "tareas_entregadas": 8, "calificacion_promedio": None, "tiempo_sesion_minutos": 340, "estado_participacion": "ACTIVO"}
    ]
    pd.DataFrame(moodle_data).to_csv("sample_data/moodle_actividad.csv", index=False, encoding="utf-8")

    # 5. MATRICULAS (EXCEL): 2025-2 y 2025-II en periodo, programas abreviados y completos
    matriculas_data = [
        {"id_matricula": "MAT-2025-01", "codigo_estudiantil": "EST-101", "documento_identidad": "1020345678", "periodo_academico": "2025-2", "programa_academico": "Ing. Inf.", "semestre_actual": 3, "creditos_inscritos": 18, "jornada": "diurna", "fecha_matricula": "16/01/2025", "estado_matricula": "MATRICULADO"},
        {"id_matricula": "MAT-2025-02", "codigo_estudiantil": "EST-102", "documento_identidad": "1032456789", "periodo_academico": "2025-II", "programa_academico": "Medicina", "semestre_actual": 4, "creditos_inscritos": 22, "jornada": "D", "fecha_matricula": "2025-01-19", "estado_matricula": "MATRICULADO"},
        {"id_matricula": "MAT-2025-03", "codigo_estudiantil": "EST-103", "documento_identidad": "1098765432", "periodo_academico": "2025_II", "programa_academico": "ADM. EMPRESAS", "semestre_actual": 2, "creditos_inscritos": 16, "jornada": "nocturna", "fecha_matricula": "23/01/2025", "estado_matricula": "MATRICULADO"},
        {"id_matricula": "MAT-2025-04", "codigo_estudiantil": "EST-104", "documento_identidad": "1045678123", "periodo_academico": "2025-2", "programa_academico": "T. Social", "semestre_actual": 5, "creditos_inscritos": 50, "jornada": "Diurna", "fecha_matricula": "26/01/2025", "estado_matricula": "MATRICULADO"},
        {"id_matricula": "MAT-2025-05", "codigo_estudiantil": "EST-105", "documento_identidad": "1011223344", "periodo_academico": "2025-II", "programa_academico": "PSI", "semestre_actual": 1, "creditos_inscritos": 14, "jornada": "VIRTUAL", "fecha_matricula": "30/01/2025", "estado_matricula": "MATRICULADO"},
        {"id_matricula": "MAT-2025-06", "codigo_estudiantil": "EST-106", "documento_identidad": "1088776655", "periodo_academico": "2025-1", "programa_academico": "ING. INDUSTRIAL", "semestre_actual": 3, "creditos_inscritos": 18, "jornada": "sabatina", "fecha_matricula": "03/02/2025", "estado_matricula": "MATRICULADO"},
        # Duplicado
        {"id_matricula": "MAT-2025-01", "codigo_estudiantil": "EST-101", "documento_identidad": "1020345678", "periodo_academico": "2025-2", "programa_academico": "Ing. Inf.", "semestre_actual": 3, "creditos_inscritos": 18, "jornada": "diurna", "fecha_matricula": "16/01/2025", "estado_matricula": "MATRICULADO"}
    ]
    pd.DataFrame(matriculas_data).to_excel("sample_data/matriculas_consolidadas.xlsx", index=False)
    print("Archivos de muestra creados exitosamente en 'sample_data/'.")

if __name__ == "__main__":
    generate_samples()
