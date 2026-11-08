# Plataforma Web de Calidad de Datos & Pipeline ETL

Sistema web integral de **Business Intelligence (BI)** y **Gobernanza de Calidad de Datos** diseñado para la ingesta, validación, depuración y consolidación de las 5 fuentes académicas y operativas institucionales:

1. **Admisiones** (`*admisiones*.[csv|xlsx]`)
2. **Bienestar** (`*bienestar*.[csv|xlsx]`)
3. **Pagos** (`*pagos*.[csv|xlsx]`)
4. **Moodle** (`*moodle*.[csv|xlsx]`)
5. **Matrículas** (`*matriculas*.[csv|xlsx]`)

---

## Características Principales

- **Sección ETL**:
  - Zona unificada de arrastre y soltar (*drag & drop*) y selección de archivos.
  - Validación de nombres en tiempo real: verifica que los 5 archivos contengan exactamente los nombres requeridos (`admisiones`, `bienestar`, `pagos`, `moodle`, `matriculas`).
  - Tarjetas de estado dinámicas con badges de validación, tamaño del archivo y estado de preparación.
  - Botón de carga con un clic de **Archivos de Prueba (Demo)** para demostración instantánea con datos que contienen anomalías y duplicados intencionales.
  - Botón de **Procesar ETL y Aplicar Reglas de Calidad** con animación y barra de progreso por fases.

- **Reglas de Calidad de Datos Aplicadas (DAMA-DMBOK)**:
  - **Unicidad**: Eliminación de filas duplicadas exactas y resolución de duplicados por llave de negocio (documento, código estudiantil, ID de pago).
  - **Completitud**: Depuración de filas vacías y saneamiento/imputación de valores nulos con valores por defecto normalizados.
  - **Conformidad**: Normalización de nombres de columnas a formato canónico `snake_case`, unificación de fechas a estándar ISO `YYYY-MM-DD`, validación de formato de correos electrónicos y teléfonos.
  - **Validez**: Depuración de montos monetarios (eliminación de símbolos `$`, separadores incorrectos y corrección a decimales), acotamiento de notas académicas a escala 0.0 - 5.0, control de créditos (1 a 32) y puntajes ICFES (0 a 500).
  - **Consistencia**: Estandarización de catálogos categóricos (métodos de pago: PSE, Tarjeta; jornadas: Diurna, Nocturna; estratos: 1 al 6; estados de admisión y transacción).

- **Registro de Transformaciones (Audit Log)**:
  - Bitácora completa accesible en la web y exportable en formato JSON.
  - Filtros en tiempo real por término de búsqueda, conjunto de datos y dimensión de calidad.
  - Detalle de timestamp, regla ejecutada, descripción técnica, cantidad de registros impactados y evidencia antes/después.

- **Descarga de Excel Consolidado**:
  - Generación automatizada de un libro Excel (`.xlsx`) profesionalmente estilizado con:
    - **Hoja 1 (`Auditoria_Calidad_ETL`)**: Reporte ejecutivo con KPIs de calidad, resumen por dataset y bitácora completa de reglas aplicadas.
    - **Hojas 2 a 6 (`Admisiones_Limpio`, `Bienestar_Limpio`, `Pagos_Limpio`, `Moodle_Limpio`, `Matriculas_Limpio`)**: Datos 100% limpios, con filtros automáticos, formatos numéricos y monetarios aplicados, y anchos de columna autoajustados.

- **Explorador de Datos Limpios**:
  - Previsualización interactiva en pantalla de las primeras filas de cada dataset limpio con cambio de pestañas rápido.

---

## Estructura del Proyecto

```text
Final/
├── app.py                     # Servidor Web Flask y API REST
├── etl_engine.py              # Motor ETL y reglas de calidad de datos
├── excel_exporter.py          # Generador del libro Excel consolidado con estilos
├── generate_sample_data.py    # Generador de los 5 archivos de prueba sucios
├── test_etl.py                # Script de pruebas automáticas del pipeline
├── sample_data/               # Conjunto de datos de prueba listos para usar
│   ├── admisiones_2024.csv
│   ├── bienestar_estudiantil.csv
│   ├── pagos_semestre.xlsx
│   ├── moodle_actividad.csv
│   └── matriculas_consolidadas.xlsx
├── static/
│   ├── css/
│   │   └── custom.css         # Estilos adicionales e interactividad
│   └── js/
│       └── app.js             # Lógica cliente, validaciones y renderizado
└── templates/
    └── index.html             # Interfaz web responsiva con Tailwind CSS
```

---

## Instrucciones para Ejecutar la Aplicación

1. **Requisitos previos**:
   - Python 3.10 o superior instalado.
   - Dependencias: `pandas`, `openpyxl`, `flask`, `requests`.

2. **Iniciar el servidor**:
   ```powershell
   python app.py
   ```

3. **Abrir en el navegador**:
   - Abra su navegador web en: **[http://localhost:5050](http://localhost:5050)**

4. **Flujo de uso**:
   - **Opción A (Prueba Instantánea)**: Haga clic en el botón superior **"Cargar Archivos de Prueba (Demo)"**. El sistema cargará automáticamente los 5 archivos sucios generados, ejecutará el ETL, mostrará las métricas de calidad y habilitará la descarga del Excel limpio.
   - **Opción B (Archivos Propios)**: Arrastre o seleccione sus 5 archivos en el recuadro. El sistema validará que contengan en su nombre: `admisiones`, `bienestar`, `pagos`, `moodle` y `matriculas`. Una vez validados los 5, presione **"Procesar ETL y Aplicar Reglas de Calidad"** y descargue el Excel consolidado.

