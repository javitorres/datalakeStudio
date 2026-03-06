# Datalake Studio - Mejoras Propuestas

## A. Mejoras de Arquitectura

### A.1 Seguridad (Prioridad: ALTA)

#### A.1.1 Autenticación y autorización ✅ IMPLEMENTADO
- **Implementado**:
  - Autenticación JWT con registro e inicio de sesión por usuario/contraseña (bcrypt + python-jose).
  - Login con Google OAuth (Google Identity Services). Aparece automáticamente si se configura `google_client_id` en `secrets.yml`.
  - Verificación de email y recuperación de contraseña por SMTP (opcional, se activa al configurar SMTP en `secrets.yml`).
  - Aislamiento de datos por usuario: cada usuario tiene su propio espacio en `data/{username}/`.
  - Propiedad `authEnabled` en `config.yml` para activar/desactivar la autenticación. En modo desactivado, se usa el usuario `default` sin pantalla de login.
  - Interceptores Axios globales para inyección de token y manejo de 401.
  - Menú de usuario en la esquina inferior izquierda con opciones de Logout y About.

#### A.1.2 Restricción de CORS
- **Estado actual**: `allow_origins=["*"]` permite requests desde cualquier dominio.
- **Propuesta**: Restringir a los dominios permitidos, configurables en `config.yml`.

#### A.1.3 Gestión de secretos
- **Estado actual**: `secrets.yml` en texto plano en el directorio del servidor.
- **Propuesta**: Usar variables de entorno o un gestor de secretos (AWS Secrets Manager, HashiCorp Vault). El fichero YAML es aceptable para desarrollo, pero no para producción.

#### A.1.4 Sanitización de SQL
- **Estado actual**: El usuario puede ejecutar cualquier SQL, incluyendo `DROP`, `ALTER`, `CREATE`, y potencialmente leer ficheros del sistema con `read_csv()`.
- **Propuesta**:
  - Modo "read-only" opcional que prohíba DDL.
  - Sandboxing de rutas de fichero accesibles.
  - Limitar extensiones DuckDB que se pueden usar.

#### A.1.5 Rate limiting
- **Estado actual**: Sin límites en llamadas a OpenAI ni en endpoints publicados.
- **Propuesta**: Implementar rate limiting con `slowapi` o similar, especialmente para `/gpt/*` y `/api/*`.

---

### A.2 Arquitectura del Backend

#### A.2.1 Eliminar estado global mutable
- **Estado actual**: `databaseService.py` y `remoteDb_controller.py` usan variables globales para la conexión DuckDB y PostgreSQL respectivamente. Esto impide concurrencia segura.
- **Propuesta**:
  - Encapsular el estado en clases con inyección de dependencias de FastAPI (`Depends()`).
  - Usar un pool de conexiones para PostgreSQL en lugar de una conexión global.
  - Para DuckDB, evaluar un pool o al menos proteger con locks para concurrencia.

#### A.2.2 Manejo de errores consistente
- **Estado actual**: Los errores se manejan de forma inconsistente. Algunos endpoints devuelven `{"status": "error", "message": ...}`, otros lanzan excepciones sin capturar, y algunos siempre devuelven 200.
- **Propuesta**:
  - Definir un esquema de error estándar (e.g., `{"error": "code", "message": "description"}`).
  - Implementar un exception handler global en FastAPI.
  - Usar códigos HTTP apropiados de forma consistente (400, 404, 500).

#### A.2.3 Formatos de respuesta inconsistentes
- **Estado actual**: Los endpoints mezclan JSON, CSV como string, FileResponse, StreamingResponse y Arrow bytes sin un patrón claro. Algunos devuelven `{"status": "ok", "rows": data}`, otros devuelven arrays directos.
- **Propuesta**: Estandarizar los formatos de respuesta. Usar content negotiation o un parámetro `format` consistente.

#### A.2.4 Naming conventions mixtas
- **Estado actual**: Los ficheros mezclan camelCase (`remoteDb_controller.py`, `apiRetrieverService.py`) con snake_case (`queries_controller.py`). Lo mismo ocurre con nombres de endpoints (`/getTables`, `/getTableSchema`).
- **Propuesta**: Unificar a snake_case siguiendo PEP 8 para Python y convenciones REST (kebab-case o snake_case para URLs).

#### A.2.5 Tests del backend
- **Estado actual**: No se observan tests automatizados para el backend (solo se menciona pytest en README).
- **Propuesta**: Añadir tests unitarios para servicios y tests de integración para endpoints usando `pytest` + `httpx` (cliente async para FastAPI).

#### A.2.6 Logging estructurado
- **Estado actual**: Logging básico con `print()` en muchos sitios y `logging` en `server.py`.
- **Propuesta**: Usar `logging` consistentemente en todo el código. Considerar logging estructurado (JSON) para producción.

---

### A.3 Arquitectura del Frontend

#### A.3.1 Estado global con Pinia
- **Estado actual**: El estado se gestiona localmente en `DatalakeStudio.vue` y se propaga via props/events. No hay store centralizado.
- **Propuesta**: Introducir **Pinia** (store oficial de Vue 3) para:
  - Lista de tablas (compartida entre componentes).
  - Base de datos activa.
  - Estado de conexión remota.
  - Configuración global (tokens, preferencias).
- **Beneficio**: Elimina prop-drilling y simplifica la comunicación entre componentes.

#### A.3.2 Router (Vue Router)
- **Estado actual**: La navegación se gestiona con un `switch` sobre `activeMenu` y `<component :is>`. No hay rutas URL.
- **Propuesta**: Introducir **Vue Router** para:
  - URLs navegables (e.g., `/tables/iris`, `/query`).
  - Deep linking y bookmarking.
  - Historial del navegador (atrás/adelante).
  - Lazy loading de componentes.

#### A.3.3 Capa de servicios HTTP
- **Estado actual**: Las llamadas Axios están dispersas directamente en cada componente Vue.
- **Propuesta**: Centralizar en un servicio API (`services/api.js`) con:
  - Instancia Axios configurada (baseURL, interceptores de error).
  - Funciones tipadas por dominio (`databaseApi.getTables()`, `gptApi.askGPT()`).
  - Manejo centralizado de errores y loading states.

#### A.3.4 URL de backend hardcodeada
- **Estado actual**: `config.js` define `http://localhost:8000`. Algunos componentes (MapH3, Mosaic) hardcodean `http://localhost:8000` directamente.
- **Propuesta**: Usar la config centralizada en todos los componentes. En producción, usar variables de entorno o configuración por proxy inverso.

#### A.3.5 TypeScript
- **Estado actual**: Todo el frontend es JavaScript plano.
- **Propuesta**: Migrar progresivamente a TypeScript para:
  - Autocompletado en IDEs.
  - Detección de errores en compilación.
  - Interfaces para DTOs del backend.

#### A.3.6 Tests del frontend
- **Estado actual**: Existen algunos tests (`__tests__/`) pero cobertura limitada. Usa vitest + MSW para mocking.
- **Propuesta**: Ampliar cobertura de tests, especialmente para componentes con lógica compleja (QueryPanel, ApiRetriever, MapH3).

---

### A.4 Infraestructura y DevOps

#### A.4.1 Proxy inverso
- **Estado actual**: Frontend y backend se exponen directamente en puertos separados (8080 y 8000).
- **Propuesta**: Añadir **Nginx** como proxy inverso en docker-compose:
  - Un solo punto de entrada (puerto 80/443).
  - Frontend servido estáticamente.
  - Backend bajo `/api/`.
  - Elimina la necesidad de CORS.

#### A.4.2 Variables de entorno para Docker
- **Estado actual**: La configuración Docker depende de ficheros YAML dentro de la imagen.
- **Propuesta**: Parametrizar via variables de entorno en `docker-compose.yml` con valores por defecto razonables.

#### A.4.3 Health check
- **Estado actual**: No existe endpoint de health check.
- **Propuesta**: Añadir `GET /health` que verifique la conexión DuckDB y devuelva estado del servidor.

#### A.4.4 CI/CD
- **Estado actual**: No se observa pipeline de CI/CD.
- **Propuesta**: GitHub Actions con:
  - Lint (eslint + black/ruff).
  - Tests (pytest + vitest).
  - Build Docker.
  - Opcional: deploy automático.

---

## B. Mejoras de Funcionalidades

### B.1 Exploración de Datos

#### B.1.1 Vista de relaciones entre tablas
- **Propuesta**: Permitir definir y visualizar relaciones (JOINs) entre tablas. Un diagrama ER automático basado en nombres de campos coincidentes.

#### B.1.2 Filtros interactivos en la tabla de datos
- **Estado actual**: La tabla de muestra es de solo lectura.
- **Propuesta**: Añadir filtros por columna en la tabla Tabulator (texto, rango numérico, selección de valores únicos) que se traduzcan a cláusulas WHERE.

#### B.1.3 Perfil de datos mejorado
- **Estado actual**: Solo estadísticas numéricas básicas (count, mean, std, min, percentiles, max).
- **Propuesta**:
  - Histogramas visuales por campo.
  - Detección de valores nulos/vacíos con porcentaje.
  - Cardinalidad (valores únicos).
  - Distribución de valores para campos categóricos (top N valores).
  - Detección automática de tipos semánticos (email, teléfono, URL, fecha, coordenada).
  - Correlaciones entre campos numéricos.

#### B.1.4 Previsualización de transformaciones
- **Propuesta**: Antes de crear una tabla nueva desde query, mostrar una preview del resultado con estadísticas de lo que se va a generar.

---

### B.2 Consultas SQL

#### B.2.1 Autocompletado SQL contextual
- **Estado actual**: CodeMirror tiene syntax highlighting pero no autocompletado de tablas/campos.
- **Propuesta**: Alimentar CodeMirror con la lista de tablas y sus campos para autocompletado inteligente.

#### B.2.2 Historial de queries
- **Estado actual**: Solo se guardan queries manualmente con nombre.
- **Propuesta**: Historial automático de queries ejecutadas con timestamp, duración y número de filas.

#### B.2.3 Ejecución parcial de queries
- **Propuesta**: Permitir seleccionar un fragmento de SQL y ejecutar solo la selección (como en DBeaver o DataGrip).

#### B.2.4 Explain plan
- **Propuesta**: Botón para ver el plan de ejecución de una query (DuckDB soporta `EXPLAIN`).

#### B.2.5 Múltiples resultados
- **Estado actual**: Solo se muestra el resultado de la última query.
- **Propuesta**: Mantener pestañas de resultados para poder comparar.

---

### B.3 Inteligencia Artificial

#### B.3.1 Soporte multi-LLM
- **Estado actual**: Solo OpenAI (GPT-4, Whisper, TTS).
- **Propuesta**: Abstraer la capa de IA para soportar:
  - Anthropic Claude (API nativa).
  - Modelos locales (Ollama, llama.cpp).
  - Azure OpenAI.
  - Selector de modelo en la configuración.

#### B.3.2 Contexto mejorado para IA
- **Estado actual**: Se envía el esquema de tablas a GPT.
- **Propuesta**:
  - Incluir datos de muestra (primeras filas) en el prompt.
  - Incluir descripción de tablas/campos si la tiene (metadatos).
  - Few-shot examples con queries exitosas previas.
  - Sintaxis específica de DuckDB en el system prompt (funciones disponibles, extensiones cargadas).

#### B.3.3 Corrección iterativa de queries IA
- **Propuesta**: Si la query generada por GPT falla al ejecutarse, enviar el error de vuelta a GPT para que corrija automáticamente.

#### B.3.4 Generación de visualizaciones con IA
- **Propuesta**: Pedir a la IA que sugiera el tipo de gráfico más apropiado para los datos y genere la configuración de Vega-Lite o DC.js.

#### B.3.5 Resumen automático de datos
- **Propuesta**: Botón "Describe esta tabla" que use la IA para generar un resumen en lenguaje natural del contenido de la tabla, patrones detectados y posibles problemas de calidad.

---

### B.4 Visualización

#### B.4.1 Builder de gráficos
- **Estado actual**: Los gráficos de DC.js se configuran automáticamente pero con opciones limitadas.
- **Propuesta**: Un constructor visual de gráficos donde el usuario seleccione:
  - Tipo de gráfico.
  - Ejes X/Y.
  - Agrupaciones y agregaciones.
  - Colores y estilos.
  - Similar a Tableau o Metabase.

#### B.4.2 Dashboards
- **Propuesta**: Permitir componer paneles de visualización con múltiples gráficos, guardarlos y compartirlos.

#### B.4.3 Exportación de gráficos
- **Propuesta**: Botón para exportar visualizaciones como PNG, SVG o PDF.

#### B.4.4 Más tipos de mapas
- **Propuesta**:
  - Mapas de calor (heatmap continuo, además de H3).
  - Clustering de puntos (Mapbox cluster).
  - Líneas y polígonos (no solo puntos y hexágonos).
  - Mapas de coropletas con regiones administrativas.

---

### B.5 Conectividad y Datos

#### B.5.1 Más fuentes de datos remotas
- **Estado actual**: Solo PostgreSQL remoto.
- **Propuesta**: Soporte para:
  - MySQL / MariaDB.
  - SQLite.
  - BigQuery.
  - Snowflake.
  - APIs GraphQL.
  - Google Sheets.
  - Excel remoto (OneDrive, SharePoint).

#### B.5.2 Soporte de más formatos
- **Estado actual**: CSV, TSV, Parquet, JSON, GeoJSON, GPKG, KML, SHP, ZIP.
- **Propuesta**: Añadir:
  - Excel (.xlsx, .xls).
  - Avro.
  - ORC.
  - XML.
  - NDJSON (JSON Lines).
  - Delta Lake.
  - Iceberg.

#### B.5.3 Actualización periódica de datos
- **Propuesta**: Programar recargas automáticas de tablas desde su fuente original (URL, S3, base de datos remota) con cron-like scheduling.

#### B.5.4 Streaming/ingesta incremental
- **Propuesta**: Capacidad de añadir datos a tablas existentes (INSERT INTO) además de crear tablas nuevas.

---

### B.6 API Server

#### B.6.1 Documentación automática OpenAPI
- **Estado actual**: Genera definición OpenAPI básica, pero no integrada con Swagger UI.
- **Propuesta**: Exponer Swagger UI integrado en `/api/docs` para los endpoints publicados, con ejemplos de request/response.

#### B.6.2 Caché de respuestas
- **Propuesta**: Caché configurable (TTL) para endpoints publicados, evitando re-ejecutar queries costosas en cada request.

#### B.6.3 Paginación
- **Estado actual**: Los endpoints devuelven todos los resultados de la query.
- **Propuesta**: Soporte de paginación estándar (`?page=1&size=50`) con cabeceras de total.

#### B.6.4 API keys para endpoints publicados
- **Propuesta**: Generar API keys para controlar el acceso a endpoints publicados. Métricas de uso por key.

---

### B.7 UX / Interfaz

#### B.7.1 Tema oscuro
- **Propuesta**: Toggle de tema claro/oscuro. El editor SQL ya tiene soporte; falta el resto de la interfaz.

#### B.7.2 Layouts responsivos
- **Estado actual**: Diseño principalmente desktop. Sidebar fija a 4rem.
- **Propuesta**: Sidebar colapsable, layout responsive para tablets.

#### B.7.3 Atajos de teclado
- **Propuesta**:
  - `Ctrl+Enter`: Ejecutar query.
  - `Ctrl+S`: Guardar query.
  - `Ctrl+Shift+E`: Exportar tabla.
  - Navegación entre paneles.

#### B.7.4 Drag & drop
- **Estado actual**: La carga de ficheros usa un formulario estándar.
- **Propuesta**: Zona de drag & drop para cargar ficheros arrastrándolos al navegador.

#### B.7.5 Indicadores de progreso
- **Estado actual**: Las operaciones largas (enriquecimiento API, carga de datos grandes) no muestran progreso.
- **Propuesta**: Barras de progreso o spinners con porcentaje para operaciones asíncronas. WebSockets o SSE para progreso en tiempo real.

#### B.7.6 Notificaciones mejoradas
- **Estado actual**: Toasts básicos para éxito/error.
- **Propuesta**: Centro de notificaciones con historial, y notificaciones persistentes para operaciones largas.

---

### B.8 Colaboración y Productividad

#### B.8.1 Compartir queries y dashboards
- **Propuesta**: URLs compartibles para queries guardadas y configuraciones de visualización.

#### B.8.2 Anotaciones en tablas
- **Propuesta**: Permitir añadir descripciones a tablas y campos (metadatos semánticos) que enriquezcan el contexto para IA y para otros usuarios.

#### B.8.3 Notebooks/workspaces
- **Propuesta**: Un modo "notebook" donde se combinen queries SQL, resultados, visualizaciones y texto explicativo en un flujo lineal (similar a Jupyter pero para SQL).

#### B.8.4 Exportación de sesión
- **Propuesta**: Exportar el estado completo (base de datos + queries + endpoints + configuración de visualizaciones) como un paquete redistribuible.
