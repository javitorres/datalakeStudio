# Datalake Studio - Documento de Arquitectura

## 1. Visión General

Datalake Studio es una aplicación web de exploración y gestión de datos construida con una arquitectura **cliente-servidor desacoplada**. El frontend es una SPA (Single Page Application) en Vue 3, mientras que el backend es una API REST en Python con FastAPI. El motor de base de datos central es **DuckDB**, una base de datos OLAP embebida de alto rendimiento.

```
┌─────────────────────────────────────────────────────────────┐
│                       CLIENTE (Vue 3)                       │
│  Puerto 8080 │ Bootstrap 5 │ Axios │ Mapbox │ DC.js/Mosaic │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP REST (JSON/CSV/Arrow)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    SERVIDOR (FastAPI/Python)                 │
│  Puerto 8000 │ Uvicorn │ CORS abierto │ 10 routers         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ DuckDB   │  │PostgreSQL│  │ AWS S3   │  │ OpenAI API │  │
│  │(embebido)│  │ (remoto) │  │ (boto3)  │  │ (GPT/TTS)  │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
│  ┌──────────┐  ┌──────────┐                                 │
│  │ APIs ext.│  │ Mapbox   │                                 │
│  │(Swagger) │  │          │                                 │
│  └──────────┘  └──────────┘                                 │
└─────────────────────────────────────────────────────────────┘
```

## 2. Stack Tecnológico

### Frontend
| Tecnología | Versión | Propósito |
|---|---|---|
| Vue 3 | 3.4.38 | Framework SPA con Composition API (`<script setup>`) |
| Bootstrap 5 | - | Layout, componentes UI, iconos |
| Axios | - | Cliente HTTP para comunicación con backend |
| CodeMirror | - | Editor SQL con syntax highlighting |
| Mapbox GL JS | - | Mapas interactivos avanzados (H3, 3D) |
| Leaflet | - | Mapas básicos de puntos |
| DC.js / Crossfilter | - | Gráficos cross-filter interactivos |
| Mosaic/Vega-Lite | - | Visualizaciones interactivas con cross-filtering |
| Tabulator | - | Tablas de datos interactivas |
| PapaParse | - | Parseo de CSV en cliente |
| vue3-toastify | - | Notificaciones |
| DuckDB WASM | - | Conector local para Mosaic (opcional) |

### Backend
| Tecnología | Versión | Propósito |
|---|---|---|
| Python 3.12 | - | Lenguaje del servidor |
| FastAPI | 0.108.0 | Framework REST API |
| Uvicorn | 0.30.1 | Servidor ASGI |
| DuckDB | 1.4.4 | Motor OLAP embebido |
| Pandas | 2.2.2 | Manipulación de DataFrames |
| PyArrow | 17.0 | Serialización Arrow para transferencia eficiente |
| OpenAI SDK | 1.6.1 | Integración GPT-4, Whisper, TTS |
| boto3 | 1.26.133 | AWS S3 |
| psycopg2 | 2.9.9 | Conexión PostgreSQL remoto |
| GeoPandas | 0.14.4 | Datos geoespaciales |
| h3 | 3.7.7 | Indexación hexagonal H3 |
| Plotly | 5.22.0 | Visualizaciones HTML de mapas |
| pydantic | 2.5.3 | Validación de DTOs |

### Infraestructura
| Tecnología | Propósito |
|---|---|
| Docker / docker-compose | Contenedorización (2 servicios: backend + frontend) |
| AWS S3 | Almacenamiento de datos remoto |
| Mapbox | Tiles de mapas |

## 3. Arquitectura del Servidor

### 3.1 Estructura de Directorios

```
server/
├── server.py              # Entry point, FastAPI app, middleware CORS, routers
├── config.py              # Singleton de configuración (config.yml + secrets.yml)
├── ServerStatus.py        # Singleton de estado del servidor, inicialización
├── requirements.txt       # Dependencias Python
│
├── routes/                # Controladores (FastAPI Routers)
│   ├── database_controller.py     # /database - CRUD tablas, queries, export
│   ├── remoteDb_controller.py     # /remotedb - Conexión PostgreSQL remoto
│   ├── s3_controller.py           # /s3 - Exploración buckets S3
│   ├── gpt_controller.py          # /gpt - ChatGPT, Whisper, TTS
│   ├── apiretriever_controller.py # /apiRetriever - Descubrimiento y enriquecimiento APIs
│   ├── profiler_controller.py     # /profiler - Perfilado de datos (desactivado)
│   ├── queries_controller.py      # /queries - CRUD queries guardadas
│   ├── apiserver_controller.py    # /apiserver - Gestión endpoints publicados
│   ├── api_controller.py          # /api - Router dinámico para endpoints publicados
│   └── maps_controller.py         # /maps - GeoJSON, H3, Mapbox HTML
│
├── services/              # Lógica de negocio
│   ├── databaseService.py       # Core DuckDB: cargar datos, queries, export, perfil
│   ├── remoteDbService.py       # Conexión PostgreSQL vía pgpass
│   ├── s3Service.py             # Operaciones S3 (browse, preview, metadata)
│   ├── chatGPTService.py        # OpenAI: GPT-4, Whisper, TTS
│   ├── apiRetrieverService.py   # Descubrimiento Swagger, enriquecimiento API
│   ├── profilerService.py       # Perfilado con pandas describe()
│   ├── queriesService.py        # Persistencia de queries en DuckDB (__queries)
│   ├── apiServerService.py      # Endpoints publicados en DuckDB (__endpoints)
│   ├── fileService.py           # Descarga de archivos por URL
│   └── mapsService.py           # Inicialización token Mapbox
│
└── model/                 # DTOs (Pydantic)
    ├── QueryRequestDTO.py
    ├── SaveQueryRequestDTO.py
    ├── PublishEndpointRequestDTO.py
    ├── apiEnrichmentRequestDTO.py
    └── Metadata.py
```

### 3.2 Patrón Controlador-Servicio

El backend sigue un patrón de dos capas:

1. **Controladores (routes/)**: Definen endpoints HTTP, validan entrada, formatean respuesta (JSON, CSV, Arrow, FileResponse, StreamingResponse).
2. **Servicios (services/)**: Contienen la lógica de negocio, interactúan con DuckDB y servicios externos.

Los controladores se registran como **FastAPI Routers** con prefijos de URL y se incluyen en `server.py`.

### 3.3 Gestión de Estado del Servidor

- **Config (Singleton)**: Carga `config.yml` (puerto, ruta BD) y `secrets.yml` (API keys, credenciales S3/Mapbox/OpenAI).
- **ServerStatus (Singleton)**: Inicializa DuckDB al arrancar, mantiene el estado de la base de datos activa.
- **Conexión DuckDB**: Variable global en `databaseService.py`. Una única conexión compartida.
- **Conexión PostgreSQL remota**: Variable global en `remoteDb_controller.py`. Se establece bajo demanda.

### 3.4 Motor de Base de Datos (DuckDB)

DuckDB es el **corazón del sistema**. Se usa como:

- **Almacén de datos**: Todas las tablas cargadas (CSV, Parquet, JSON, GeoJSON, SHP, etc.)
- **Motor de queries**: Ejecución SQL estándar y geoespacial
- **Almacén de metadatos**: Tablas internas `__queries` y `__endpoints` para queries guardadas y endpoints publicados
- **Motor de exportación**: CSV, Parquet con Apache Arrow
- **Motor geoespacial**: Extensiones `spatial` y `h3` para operaciones geográficas

**Extensiones DuckDB cargadas:**
- `httpfs` - Lectura de archivos remotos (S3, HTTP)
- `spatial` - Funciones geoespaciales (ST_AsText, ST_Transform, etc.)
- `h3` - Indexación hexagonal H3

**Formatos de datos soportados:** CSV, TSV, Parquet, JSON, GeoJSON, GPKG, KML, SHP, ZIP (shapefiles comprimidos)

### 3.5 Tablas Internas de Metadatos

| Tabla | Campos | Propósito |
|---|---|---|
| `__queries` | id, name, query, description | Queries SQL guardadas por el usuario |
| `__endpoints` | id, query_id, path, parameters, description, query, test_string, status | Endpoints REST publicados |
| `__lastQuery` | (dinámico) | Resultado temporal de la última query ejecutada |

## 4. Arquitectura del Cliente

### 4.1 Estructura de Directorios

```
client/src/
├── main.js                    # Entry point Vue 3
├── App.vue                    # Root component (solo monta DatalakeStudio)
│
├── components/
│   ├── DatalakeStudio.vue     # Layout principal: sidebar + panel dinámico
│   ├── Welcome.vue            # Página de bienvenida
│   ├── ChangeDatabase.vue     # Selector de base de datos
│   ├── LoadDataPanel.vue      # Carga de datos (Upload, S3, URL, Path)
│   ├── TablesPanel.vue        # Lista de tablas + TableInspector
│   ├── TableInspector.vue     # Explorador detallado de tabla
│   ├── QueryPanel.vue         # Editor SQL + resultados + ChatGPT
│   ├── RemoteDbPanel.vue      # Conexión a bases de datos remotas
│   ├── ApiRetriever.vue       # Enriquecimiento de datos desde APIs
│   ├── ApiServer.vue          # Publicación de endpoints REST
│   ├── S3Explorer.vue         # Navegador de buckets S3
│   ├── ChatGptAgent.vue       # Chat con IA + voz
│   ├── Map.vue                # Mapa Leaflet de puntos
│   ├── MapH3.vue              # Mapa Mapbox con H3 y 3D
│   ├── GenericCross.vue       # Gráficos DC.js cross-filter
│   ├── Mosaic.vue             # Visualizaciones Mosaic/Vega-Lite
│   ├── CodeEditor.vue         # Editor SQL (CodeMirror wrapper)
│   ├── RecorderWidget.vue     # Grabadora de audio
│   └── DataSelector.vue       # Visualización de distribución
│
├── lib/
│   ├── Recorder.js            # Web Audio API recorder
│   └── Utils.js               # Utilidades (formateo tiempo)
│
└── services/
    └── databaseService.js     # (vacío/mínimo)
```

### 4.2 Patrón de Navegación

`DatalakeStudio.vue` actúa como **orquestador central**:

1. **Sidebar lateral** con iconos Bootstrap Icons para cada sección.
2. **`<component :is>` dinámico** con `<keep-alive>` para cambiar entre paneles sin destruir estado.
3. **Props computados** (`currentProps`) y **listeners computados** (`currentListeners`) inyectan datos y callbacks según el panel activo.
4. **Estado compartido**: La lista de `tables` se gestiona en DatalakeStudio y se propaga como prop a los componentes que la necesitan.

### 4.3 Comunicación Cliente-Servidor

- **Protocolo**: HTTP REST sobre Axios
- **Formatos de respuesta**: JSON, CSV (parseado con PapaParse en cliente), Apache Arrow (para Mosaic), FileResponse (binarios de export), StreamingResponse (audio TTS)
- **URL base**: Configurada en `client/config.js` → `http://localhost:8000`
- **CORS**: Abierto a todos los orígenes (`*`)

### 4.4 Flujo de Datos

```
Carga de datos ─── LoadDataPanel / S3Explorer / RemoteDbPanel
      │
      ▼
  DuckDB (tablas)
      │
      ├── TablesPanel → TableInspector ─┬── Datos de muestra
      │                                 ├── Perfil estadístico
      │                                 ├── Map (Leaflet)
      │                                 ├── MapH3 (Mapbox + H3)
      │                                 ├── GenericCross (DC.js)
      │                                 └── Mosaic (Vega-Lite)
      │
      ├── QueryPanel ──── SQL / ChatGPT → Nuevas tablas
      │
      ├── ApiRetriever ── Enriquecimiento → Nuevas tablas
      │
      └── ApiServer ───── Publicar queries como endpoints REST
```

## 5. Despliegue

### Docker Compose

```yaml
services:
  backend:   # Puerto 8000, Dockerfile en ./server, monta ~/.aws como read-only
  frontend:  # Puerto 8080, Dockerfile en ./client
```

### Sin Docker

- **Servidor**: `pip install -r requirements.txt` → `python3 server.py`
- **Cliente**: `npm install` → `npm run dev -- --port 8080`

### Configuración

| Fichero | Ubicación | Contenido |
|---|---|---|
| `config.yml` | server/ | Puerto, ruta base de datos, base de datos por defecto |
| `secrets.yml` | server/ | API keys (OpenAI, Mapbox), credenciales S3, fichero pgpass |
| `config.js` | client/ | Host y puerto del backend |

## 6. Integración con Servicios Externos

| Servicio | Uso | Configuración |
|---|---|---|
| **OpenAI GPT-4** | Generación SQL desde lenguaje natural | `openai_api_key` en secrets.yml |
| **OpenAI Whisper** | Transcripción voz → texto | Mismo API key |
| **OpenAI TTS** | Texto → voz | Mismo API key |
| **AWS S3** | Exploración y carga de archivos | Credenciales en secrets.yml o AWS default chain |
| **PostgreSQL** | Bases de datos remotas | Fichero pgpass |
| **Mapbox** | Tiles de mapas | `mapbox_access_token` en secrets.yml |
| **APIs externas** | Enriquecimiento de datos (Swagger/OpenAPI) | Descubrimiento dinámico vía CodeCommit |

## 7. Seguridad

### Estado actual
- **CORS abierto** (`allow_origins=["*"]`) - Sin restricción de orígenes.
- **Sin autenticación** - No hay mecanismo de login ni tokens.
- **Sin autorización** - Todos los endpoints son públicos.
- **Credenciales en fichero YAML** - `secrets.yml` no cifrado.
- **Queries SQL directas** - El usuario puede ejecutar SQL arbitrario, incluyendo DDL.
- **No hay rate limiting** en las llamadas a OpenAI ni en los endpoints publicados.
