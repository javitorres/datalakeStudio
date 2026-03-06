# Datalake Studio - Documento de Funcionalidades

## 1. Gestión de Bases de Datos

### 1.1 Múltiples bases de datos locales
- Crear nuevas bases de datos DuckDB (ficheros `.db`).
- Cambiar entre bases de datos disponibles en caliente.
- La lista de bases de datos se extrae del directorio configurado en `config.yml`.
- Al cambiar de base de datos, se reconecta DuckDB y se refrescan las tablas visibles.

**Componentes**: `ChangeDatabase.vue` → `database_controller.py` → `databaseService.py`

---

## 2. Carga de Datos

### 2.1 Upload de archivos locales
- Subida de ficheros desde el navegador mediante formulario (`<input type="file">`).
- Se asigna un nombre de tabla (por defecto, el nombre del fichero sin extensión).
- Formatos soportados: CSV, TSV, Parquet, JSON, GeoJSON, GPKG, KML, SHP, ZIP (shapefiles).

### 2.2 Carga desde URL
- Descarga de ficheros desde cualquier URL pública.
- Detección automática del tipo de fichero por Content-Type y extensión.
- Soporte de GeoJSON detectado por contenido.

### 2.3 Carga desde S3
- Búsqueda de ficheros dentro de un bucket S3 (búsqueda por nombre, mínimo 3 caracteres).
- Muestra los primeros 10 resultados coincidentes.
- Carga directa del fichero S3 como tabla DuckDB usando la extensión `httpfs`.

### 2.4 Carga desde ruta del servidor
- Especificar una ruta de fichero accesible desde el servidor.
- Útil para ficheros locales en el mismo host del servidor.

**Componentes**: `LoadDataPanel.vue` (4 tabs) → `database_controller.py` → `databaseService.py`, `fileService.py`

---

## 3. Exploración de Tablas

### 3.1 Lista de tablas
- Visualización de todas las tablas disponibles como chips/badges clicables.
- Filtrado automático de tablas internas (`__queries`, `__endpoints`, `cube_index_*`).
- Selección de tabla activa para inspección.

### 3.2 Inspector de tabla (TableInspector)
Cada tabla se puede explorar en profundidad con las siguientes herramientas:

#### 3.2.1 Esquema
- Listado de campos con sus tipos de datos DuckDB.
- Selector de campos para mostrar solo columnas deseadas.

#### 3.2.2 Datos de muestra
- Muestreo configurable: primeros N, últimos N o aleatorios.
- Número de registros configurable (por defecto 1000).
- Visualización en tabla interactiva (Tabulator).
- Formato CSV parseado en cliente con PapaParse.

#### 3.2.3 Perfil estadístico
- Estadísticas por columna numérica: count, mean, std, min, p25, p50, p75, max.
- Generado con DuckDB SQL (no pandas, por rendimiento).

#### 3.2.4 Eliminación de tablas
- Borrado de tablas con confirmación.
- `DROP TABLE` directo sobre DuckDB.

#### 3.2.5 Exportación de datos
- Descarga de tablas completas en formato CSV, Parquet o Excel.
- Generación de fichero temporal en servidor y envío como `FileResponse`.

### 3.3 Conteo de filas
- Muestra el número total de registros de la tabla seleccionada.

**Componentes**: `TablesPanel.vue` + `TableInspector.vue` → `database_controller.py` → `databaseService.py`

---

## 4. Visualización de Datos

### 4.1 Mapa de puntos (Leaflet)
- Detección automática de campos de latitud/longitud.
- Visualización de puntos sobre mapa base.
- Alternancia de estilo de mapa (oscuro/claro).
- Popups informativos al hacer clic en puntos.

### 4.2 Mapa H3 avanzado (Mapbox)
- **Aggregación H3**: Heatmap con celdas hexagonales a resolución configurable (1-15).
- **Capa de puntos**: Superposición de puntos individuales sobre H3.
- **Campos de geometría**: Soporte de columnas WKT/geometría además de lat/lon.
- **Visualización 3D**: Extrusión de hexágonos según valor.
- **Controles avanzados**:
  - Gradientes de color personalizables (H3 y puntos por separado).
  - Opacidad independiente para cada capa.
  - Filtrado por rango de valores (min/max).
  - Toggle de contornos de hexágonos.
  - Selección del campo a visualizar en el gradiente.
- **Metadatos de rendimiento**: Muestra número de registros, tamaño de datos, tiempo de ejecución.

### 4.3 Cross-filter (DC.js)
- Dashboard interactivo con múltiples gráficos enlazados.
- Tipos de gráficos: barras, pastel, líneas, scatter, burbujas.
- Filtrado cruzado: al seleccionar en un gráfico, todos los demás se actualizan.
- Configuración automática de gráficos según tipos de datos.
- Resumen de filtros activos visible.

### 4.4 Mosaic (Vega-Lite)
- Visualizaciones interactivas con cross-filtering basado en Mosaic/Vega-Lite.
- Tres modos de conectividad: REST, WebSocket, WASM (DuckDB local).
- Utiliza el endpoint `/database/restConnector` para enviar queries SQL.
- Soporte de "cubos" de datos para queries eficientes.

**Componentes**: `Map.vue`, `MapH3.vue`, `GenericCross.vue`, `Mosaic.vue`, `DataSelector.vue`

---

## 5. Consultas SQL

### 5.1 Editor SQL
- Editor CodeMirror con syntax highlighting SQL.
- **6 pestañas de queries** (principal + 5 auxiliares) para trabajo simultáneo.
- Ejecución de queries con resultados tabulados.
- Límite configurable de filas de resultado (por defecto 1000).

### 5.2 Creación de tablas desde queries
- Convertir el resultado de cualquier query en una nueva tabla DuckDB.
- Nombre de tabla personalizable.

### 5.3 Guardado y recuperación de queries
- Guardar queries con nombre y descripción.
- Búsqueda de queries guardadas por nombre/descripción (case-insensitive).
- Eliminación de queries guardadas.
- Las queries se persisten en la tabla interna `__queries`.

### 5.4 Asistente ChatGPT para SQL
- Integrado en el panel de queries.
- El usuario describe lo que quiere en lenguaje natural.
- ChatGPT recibe el esquema de las tablas disponibles como contexto.
- Genera una query SQL que el usuario puede ejecutar directamente.
- Usa el modelo GPT-4 (gpt-4-1106-preview).

**Componentes**: `QueryPanel.vue` + `CodeEditor.vue` → `database_controller.py`, `gpt_controller.py`, `queries_controller.py`

---

## 6. Agente Conversacional (ChatGPT)

### 6.1 Chat interactivo
- Interfaz de chat con historial de conversación.
- Entrada por texto o por voz.
- Flujo: Pregunta → SQL (GPT-4) → Ejecución → Resultado → Interpretación verbal (GPT o3-mini).

### 6.2 Entrada por voz
- Grabación de audio con micrófono del navegador (Web Audio API).
- Transcripción con OpenAI Whisper.
- Detección de silencio (devuelve "EMPTY_AUDIO").

### 6.3 Salida por voz (TTS)
- Conversión de la respuesta textual a audio con OpenAI TTS.
- Reproducción automática del audio.
- Toggle para activar/desactivar TTS.

### 6.4 Modo ciego
- Modo especial que omite la visualización de datos y prioriza la respuesta verbal.

**Componentes**: `ChatGptAgent.vue` + `RecorderWidget.vue` → `gpt_controller.py` → `chatGPTService.py`

---

## 7. Conexión a Bases de Datos Remotas (PostgreSQL)

### 7.1 Descubrimiento de bases de datos
- Búsqueda por texto en las conexiones definidas en el fichero `.pgpass`.
- Listado de bases de datos que coinciden con la búsqueda.

### 7.2 Conexión y exploración
- Conexión a base de datos remota PostgreSQL.
- Navegación por esquemas y tablas.
- Ejecución de queries remotas con resultados tabulados.

### 7.3 Importación de datos
- Crear tabla local DuckDB a partir del resultado de una query remota.
- Transferencia de datos PostgreSQL → DuckDB via pandas DataFrame.

**Componentes**: `RemoteDbPanel.vue` → `remoteDb_controller.py` → `remoteDbService.py`

---

## 8. Enriquecimiento de Datos desde APIs

### 8.1 Descubrimiento de APIs
- Búsqueda de servicios en AWS CodeCommit.
- Extracción automática de endpoints desde definiciones Swagger 2.0 y OpenAPI 3.0.
- Visualización de información del método: parámetros, respuesta, URL.

### 8.2 Modo manual (URL directa)
- Especificar directamente la URL de un API endpoint.
- Probar la llamada con datos de muestra.

### 8.3 Mapeo de parámetros
- Mapear campos de la tabla DuckDB a parámetros de la API.
- El sistema itera sobre las filas de la tabla, haciendo una llamada por cada registro.

### 8.4 Mapeo de respuesta
- Configurar qué campos de la respuesta JSON se extraen.
- Asignar nombres de columnas nuevas para los campos extraídos.
- Especificar número de registros a procesar.

### 8.5 Resultado
- Se genera una nueva tabla con los datos originales enriquecidos con las columnas de la API.

**Componentes**: `ApiRetriever.vue` → `apiretriever_controller.py` → `apiRetrieverService.py`

---

## 9. Publicación de APIs

### 9.1 Creación de endpoints
- Crear endpoint REST a partir de queries SQL guardadas.
- Definir ruta del endpoint (e.g., `/api/buscarMarca`).
- Definir parámetros con valores de ejemplo.
- La query SQL usa placeholders `{param_name}` que se sustituyen en runtime.

### 9.2 Testing
- Probar el endpoint con parámetros de ejemplo antes de publicar.
- Preview de la respuesta (limitada a 10 filas).

### 9.3 Gestión de endpoints
- Listar todos los endpoints publicados.
- Editar configuración de endpoints existentes.
- Eliminar endpoints.
- Estado DEV/PROD.

### 9.4 Ejecución dinámica
- Router catch-all (`/api/{path}`) que despacha requests a queries DuckDB.
- Soporte de GET y POST.
- Formatos de respuesta: JSON (defecto) o CSV.
- Generación automática de definiciones OpenAPI (accediendo a la ruta con `/` final).

**Componentes**: `ApiServer.vue` → `apiserver_controller.py`, `api_controller.py` → `apiServerService.py`

---

## 10. Explorador S3

### 10.1 Navegación de buckets
- Especificar nombre del bucket.
- Navegación jerárquica de carpetas y ficheros.
- Vista de tamaño y última modificación.

### 10.2 Preview de ficheros
- Vista previa de los primeros 1000 bytes de ficheros (CSV, JSON, TXT).

### 10.3 Gestión de metadatos
- Editar descripción, propietario y esquema de carpetas S3.
- Los metadatos se almacenan como `metadata.json` dentro de cada carpeta S3.

### 10.4 Carga de ficheros S3
- Cargar cualquier fichero S3 directamente como tabla DuckDB.
- Usa la extensión `httpfs` de DuckDB para lectura directa.

**Componentes**: `S3Explorer.vue` → `s3_controller.py` → `s3Service.py`

---

## 11. Conector Mosaic/REST

### 11.1 Conector REST para Mosaic
- Endpoint `/database/restConnector` que procesa queries SQL desde el framework Mosaic.
- Tres tipos de comando: `exec` (DDL), `arrow` (datos binarios Arrow), `json` (datos JSON).
- Log de queries lentas (>5 segundos).

### 11.2 Gestión de cubos
- Endpoint `/database/dropCubes` para limpiar tablas temporales de cubos de datos (`cube_index_*`).

**Componentes**: `Mosaic.vue` → `database_controller.py` → `databaseService.py`

---

## 12. Geoespacial

### 12.1 Detección automática de campos geográficos
- El inspector de tabla detecta automáticamente campos con nombres tipo `latitude`, `longitude`, `lat`, `lon`, `geom`, etc.

### 12.2 Queries geoespaciales
- Filtrado por bounding box (bbox).
- Transformación de proyecciones (ST_Transform a EPSG:4326).
- Indexación H3 con agregaciones (count, avg).
- Generación de GeoJSON desde DuckDB.

### 12.3 Mapas HTML
- Generación de mapas Plotly interactivos con cloroplethos H3.
- Centro por defecto: Madrid.

**Componentes**: `Map.vue`, `MapH3.vue` → `maps_controller.py` → `databaseService.py`, `mapsService.py`
