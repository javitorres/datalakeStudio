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
from fastapi.responses import Response
import pandas as pd

router = APIRouter(prefix="/maps")


def getGeom(table: str, geomField: str, lat_min: float = 26.5, lat_max: float = 44.5, lon_min: float = -19.3, lon_max: float = 7.8):
    # La consulta completa
    query = f"""
    SELECT * , geom_4326 as geom FROM (
    SELECT * EXCLUDE GEOM, ST_AsText(ST_Transform(ST_GeomFromText({geomField}), 'EPSG:32630', 'EPSG:4326')) as geom_4326
    FROM {table}
    WHERE  {geomField} IS NOT NULL
    AND ST_Within(
        ST_MakeEnvelope({lon_min}::DOUBLE, {lat_min}::DOUBLE, {lon_max}::DOUBLE, {lat_max}::DOUBLE), 
        ST_Transform(ST_GeomFromText({geomField}), 'EPSG:32630', 'EPSG:4326'))
        ) as subq1
    LIMIT 1000
    """

    # Ejecutamos la consulta y retornamos el dataframe
    df = databaseService.runQuery(query, True)
    return df

def getH3Data(table: str, latitudeField: str, longitudeField: str, aggFields: list, level: int = 5, lat_min: float = 26.5, lat_max: float = 44.5,
            lon_min: float = -19.3, lon_max: float = 7.8):
    # Si no se proporcionan campos de agregación, usamos un campo predeterminado
    if aggFields is None:
        aggFields = ['anyoConst']

    # Aplicamos la función de agregación 'avg' a cada campo de aggFields
    aggFields_sql = ', '.join([f'avg({field}) as avg_{field}' for field in aggFields])

    # La consulta completa
    query = f"""
    SELECT h3_cell, h3_cell_to_boundary_wkt(h3_cell) geom, count(*) as count, {aggFields_sql} FROM
    (SELECT *, h3_latlng_to_cell({latitudeField}, {longitudeField}, {level}) as h3_cell FROM {table}
     WHERE {latitudeField} >= {lat_min} AND {latitudeField} <= {lat_max} AND {longitudeField} >= {lon_min} AND {longitudeField} <= {lon_max}
     ) as subq1
    GROUP BY h3_cell
    ORDER BY count DESC
    """

    # Ejecutamos la consulta y retornamos el dataframe
    df = databaseService.runQuery(query, True)
    return df

def getRecords(table: str, latitudeField: str, longitudeField: str,  fields: str, lat_min: float = 26.5, lat_max: float = 44.5,
            lon_min: float = -19.3, lon_max: float = 7.8):

    # Aplicamos la función de agregación 'avg' a cada campo de aggFields
    if (fields is None or fields == ""):
        fields = f"""* EXCLUDE ({latitudeField}, {longitudeField})"""
        #fields_sql = ', '.join([{field} for field in fields])
    else:
        # Remove latitude and longitude fields
        fields = fields.replace(f"{latitudeField}", "")
        fields = fields.replace(f"{longitudeField}", "")
        fields = fields.replace(",,", ",")
        fields = fields.replace(",,", ",")
        # REmove fisrt or last comma
        if fields[0] == ",": fields = fields[1:]
        if fields[-1] == ",": fields = fields[:-1]

    # La consulta completa
    query = f"""
    SELECT round({latitudeField}, 5) as latitude, round({longitudeField}, 5) as longitude, {fields}
        FROM {table}
    WHERE {latitudeField} >= {lat_min} 
      AND {latitudeField} <= {lat_max} 
      AND {longitudeField} >= {lon_min} 
      AND {longitudeField} <= {lon_max}
      LIMIT 100000
    """

    # Ejecutamos la consulta y retornamos el dataframe
    df = databaseService.runQuery(query, True)
    # Show firt 5 records
    print(df.head())
    return df


def getFeatureCollection(df, fields, addProperties: bool = True):
    features = []
    for index, row in df.iterrows():
        geom = wkt.loads(row['geom'])  # Convierte WKT a un objeto de geometría usando wkt.loads
        # Do it for each aggregated field feature = Feature(geometry=geom, properties={"aggField": row['aggField'], "h3_cell": row['h3_cell']})
        if addProperties:
            properties = {}
            if 'h3_cell' in row:
                properties = {"h3_cell": row['h3_cell']}

            if 'count' in row:
                properties['count'] = row['count']

            if fields is not None and len(fields) > 0:
                for field in fields:
                    if f'avg_{field}' in row:
                        properties[field] = row[f'avg_{field}']

                    else:
                        properties[field] = row[field]
            feature = Feature(geometry=geom, properties=properties)
        else:
            feature = Feature(geometry=geom, properties={})
        features.append(feature)
    return FeatureCollection(features)

@router.get("/csv", response_class=HTMLResponse)
async def csv(table: str, latitudeField: str,  longitudeField: str, fields: str, bbox: str):
    bbox = bbox.split(',')
    lat_min = float(bbox[1])
    lat_max = float(bbox[3])
    lon_min = float(bbox[0])
    lon_max = float(bbox[2])
    starttime = time.time()
    df = getRecords(table, latitudeField, longitudeField, fields, lat_min, lat_max, lon_min, lon_max)
    log.info(f"Size {len(df)} records - {df.memory_usage(deep=True).sum() / 1024 ** 2} Mb - {time.time() - starttime} seconds")
    return JSONResponse(content=df.to_csv(index=False), media_type="text/csv")

@router.get("/geojson")
async def create_map_geojson(table: str, latitudeField: str,  longitudeField: str, geomField: str, bbox: str, level: int = 5, fields: str = ""):
    # Convert bbox bbox=-5.734656374770793,38.91107573878938,-0.9550204057964322,41.34695562076499 to lat_min: float = 26.5, lat_max: float = 44.5,
    #             lon_min: float = -19.3, lon_max: float = 7.8
    bbox = bbox.split(',')
    lat_min = float(bbox[1])
    lat_max = float(bbox[3])
    lon_min = float(bbox[0])
    lon_max = float(bbox[2])
    fields = fields.split(',')
    if fields[0] == "":
        fields = []
    starttime = time.time()
    df = None
    geojson_obj = None
    if ((latitudeField == "" or longitudeField == "") and geomField != ""):
        df = getGeom(table, geomField, lat_min, lat_max, lon_min, lon_max)
    elif (latitudeField != "" and longitudeField != ""):
        df = getH3Data(table, latitudeField, longitudeField, fields, level, lat_min, lat_max, lon_min, lon_max)
    else:
        log.error("No latitude-longitude or geom fields provided")
        return Response(status_code=400)

    with pd.option_context('display.max_columns', None, 'display.width', 1000):
        log.info("df head:\n" + str(df.head()))

    # Reflace Nans in df with -1
    df = df.fillna(-1)
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
    #log.info("Geojson: " + str(geojson_obj))
    responseObject["metadata"]["objectSize"] = round(len(str(responseObject)) / 1024 ** 2, 2)
    return JSONResponse(content=responseObject)

@router.get("/html", response_class=HTMLResponse)
async def create_map(table: str, level: int = 5):
    try:
        df = getH3Data(table, level)
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
