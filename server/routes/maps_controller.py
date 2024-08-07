import logging as log
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from shapely import wkt
from geojson import Feature, FeatureCollection
import plotly.express as px
from services import databaseService
from services import mapsService
import time

router = APIRouter(prefix="/maps")


def getData(table: str, aggFields: list, level: int = 5, lat_min: float = 26.5, lat_max: float = 44.5,
            lon_min: float = -19.3, lon_max: float = 7.8):
    # Si no se proporcionan campos de agregación, usamos un campo predeterminado
    if aggFields is None:
        aggFields = ['anyoConst']

    # Aplicamos la función de agregación 'avg' a cada campo de aggFields
    aggFields_sql = ', '.join([f'avg({field}) as avg_{field}' for field in aggFields])

    # La consulta completa
    query = f"""
    SELECT h3_cell, h3_cell_to_boundary_wkt(h3_cell) geom, count(*) as count, {aggFields_sql} FROM
    (SELECT *, h3_latlng_to_cell(latitud, longitud, {level}) as h3_cell FROM {table}
     WHERE latitud >= {lat_min} AND latitud <= {lat_max} AND longitud >= {lon_min} AND longitud <= {lon_max}
     ) as subq1
    GROUP BY h3_cell
    ORDER BY count DESC
    """

    # Ejecutamos la consulta y retornamos el dataframe
    df = databaseService.runQuery(query, True)
    return df


def getFeatureCollection(df, fields):
    features = []
    for index, row in df.iterrows():
        geom = wkt.loads(row['geom'])  # Convierte WKT a un objeto de geometría usando wkt.loads
        # Do it for each aggregated field feature = Feature(geometry=geom, properties={"aggField": row['aggField'], "h3_cell": row['h3_cell']})
        properties = {"h3_cell": row['h3_cell']}
        for field in fields:
            properties[field] = row[f'avg_{field}']
        feature = Feature(geometry=geom, properties=properties)
        features.append(feature)
    return FeatureCollection(features)

@router.get("/csv", response_class=HTMLResponse)
async def create_map_csv(table: str, fields: list, level: int = 5):
    df = getData(table, fields, level)
   # Return the dataframe as a CSV file
    return df.to_csv()

@router.get("/geojson")
async def create_map_geojson(table: str, fields: str, bbox: str, level: int = 5):
    # Convert bbox bbox=-5.734656374770793,38.91107573878938,-0.9550204057964322,41.34695562076499 to lat_min: float = 26.5, lat_max: float = 44.5,
    #             lon_min: float = -19.3, lon_max: float = 7.8
    bbox = bbox.split(',')
    lat_min = float(bbox[1])
    lat_max = float(bbox[3])
    lon_min = float(bbox[0])
    lon_max = float(bbox[2])
    fields = fields.split(',')
    starttime = time.time()
    df = getData(table, fields, level, lat_min, lat_max, lon_min, lon_max)
    geojson_obj = getFeatureCollection(df, fields)
    log.info(f"Size {len(df)} records - {df.memory_usage(deep=True).sum() / 1024 ** 2} Mb - {time.time() - starttime} seconds")
    responseObject = {
        "metadata":{
            "records": len(df),
            "dfsize": round(df.memory_usage(deep=True).sum() / 1024 ** 2, 2),
            "objectSize": 0,
            "time": round(time.time() - starttime, 2)
        },
        "geojson": geojson_obj
    }
    responseObject["metadata"]["objectSize"] = round(len(str(responseObject)) / 1024 ** 2, 2)
    return JSONResponse(content=responseObject)

@router.get("/html", response_class=HTMLResponse)
async def create_map(table: str, level: int = 5):
    try:
        df = getData(table, level)
        geojson_obj = getFeatureCollection(df)

        fig = px.choropleth_mapbox(
            df,
            geojson=geojson_obj,
            locations='h3_cell',
            featureidkey="properties.h3_cell",  # Especificar la clave para el GeoJSON
            color='aggField',
            color_continuous_scale="Viridis",
            range_color=(df['aggField'].min(), df['aggField'].max()),
            mapbox_style='carto-positron',
            zoom=5,
            center={"lat": 40.624032273164794, "lon": -3.993888283105448},
            opacity=0.7,
            labels={'count': '# cantidad de registros'}
        )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

        # Generar el HTML y agregar el JavaScript necesario
        plot_html = fig.to_html(full_html=False)
        html_content = f"""
        <html>
        <head>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body>
            {plot_html}
            <script>
                var plotElement = document.getElementsByClassName('plotly-graph-div')[0];
                plotElement.on('plotly_relayout', function(eventdata) {{
                    console.log('Zoom or pan detected!', eventdata);
                    // Aquí puedes enviar los datos al servidor para recalcular
                    // Por ejemplo, usando fetch para hacer una llamada a la API
                    fetch('/maps/update', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify(eventdata)
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        // Aquí puedes actualizar el gráfico con los nuevos datos
                        Plotly.react(plotElement, data);
                    }});
                }});
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    except Exception as e:
        print("Error: " + str(e))
        return "Error creating map"


@router.get("/mapbox_token")
def getMapboxToken():
    log.info("Getting Mapbox token")
    token = mapsService.mapbox_access_token
    return {"token": token}

''' EXPERIMENTAL 
@router.get("/tiles/{table}/{z}/{x}/{y}.pbf")
async def get_tile(table: str, z: int, x: int, y: int):
    level = 5
    print(f"####### Getting tile {z}/{x}/{y}")

    df = getData(table, level)
    # Print the number of rows
    print("Number of rows: ", len(df))

    #vmin = df['aggField'].min()
    #vmax = df['aggField'].max()

    feature_collection = getFeatureCollection(df)
    #print("Geojson: ", feature_collection)
    tile_index = geojson2vt(feature_collection,{
        'maxZoom': 24,  # max zoom to preserve detail on; can't be higher than 24
        'tolerance': 5, # simplification tolerance (higher means simpler)
        'extent': 4096, # tile extent (both width and height)
        'buffer': 64,   # tile buffer on each side
        'lineMetrics': False, # whether to enable line metrics tracking for LineString/MultiLineString features
        'promoteId': 'h3_cell',    # name of a feature property to promote to feature.id. Cannot be used with `generateId`
        'generateId': False,  # whether to generate feature ids. Cannot be used with `promoteId`
        'indexMaxZoom': 14,       # max zoom in the initial tile index
        'indexMaxPoints': 100000 # max number of points per tile in the index
    })
    # Print index size
    print("Index size: ", len(tile_index.tiles))
    vector_tile = tile_index.get_tile(z, x, y)
    if not vector_tile:
        # Return 204
        return Response(status_code=204)

    pbf = vt2pbf(vector_tile)
    # Print pbf bytes
    print("PBF bytes: ", len(pbf))
    return Response(content=pbf, media_type="application/x-protobuf")

def tile_to_bbox(z, x, y):
    n = 2.0 ** z
    lon_min = x / n * 360.0 - 180.0
    lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    lon_max = (x + 1) / n * 360.0 - 180.0
    lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    print(f"Tile {z}/{x}/{y} is in bbox ({lat_min}, {lon_min}, {lat_max}, {lon_max})")
    return lon_min, lat_min, lon_max, lat_max

def agg_field_to_color(value, vmin, vmax):
    norm_value = (value - vmin) / (vmax - vmin)
    colorscale = [
        "#440154", "#482878", "#3e4989", "#31688e", "#26828e",
        "#1f9e89", "#35b779", "#6ece58", "#b5de2b", "#fde725"
    ]
    #print("Norm value: ", norm_value)
    # if norm_value is Nan, return the first color
    if math.isnan(norm_value):
        return colorscale[0]
    color_idx = int(norm_value * (len(colorscale) - 1))
    return colorscale[color_idx]

'''