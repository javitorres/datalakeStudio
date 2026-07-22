import logging as log
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from shapely import wkt
from geojson import Feature, FeatureCollection
from services import databaseService
from services import mapsService
import time
import math
from fastapi.responses import Response
import pandas as pd

router = APIRouter(prefix="/maps")


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _filter_clause(filter_expr: str) -> str:
    # Optional cross-filter predicate appended to the map queries' WHERE clause.
    filter_expr = (filter_expr or "").strip()
    return f"\n          AND ({filter_expr})" if filter_expr else ""


def _parse_bbox(bbox: str):
    try:
        values = [float(value) for value in bbox.split(',')]
    except (AttributeError, TypeError, ValueError):
        raise HTTPException(status_code=400, detail="bbox must contain four numbers")

    if len(values) != 4 or not all(math.isfinite(value) for value in values):
        raise HTTPException(status_code=400, detail="bbox must contain four finite numbers")

    lon_min, lat_min, lon_max, lat_max = values
    if not (-180 <= lon_min < lon_max <= 180 and -90 <= lat_min < lat_max <= 90):
        raise HTTPException(status_code=400, detail="bbox is outside valid longitude/latitude bounds")
    return lat_min, lat_max, lon_min, lon_max


def _validated_map_fields(table: str, latitude_field: str = None, longitude_field: str = None,
                          geom_field: str = None, fields=None):
    schema = databaseService.getDatabaseSchema()
    if table not in schema:
        raise HTTPException(status_code=404, detail=f"Unknown table: {table}")

    requested = [field for field in [latitude_field, longitude_field, geom_field] if field]
    requested.extend(fields or [])
    missing = [field for field in requested if field not in schema[table]]
    if missing:
        raise HTTPException(status_code=400, detail=f"Unknown columns: {', '.join(missing)}")

    numeric_markers = ('INT', 'DECIMAL', 'NUMERIC', 'REAL', 'FLOAT', 'DOUBLE')
    non_numeric = [field for field in (fields or [])
                   if not any(marker in schema[table][field].upper() for marker in numeric_markers)]
    if non_numeric:
        raise HTTPException(status_code=400, detail=f"Aggregation columns must be numeric: {', '.join(non_numeric)}")
    return schema[table]


def getGeom(table: str, geomField: str, lat_min: float = 26.5, lat_max: float = 44.5,
            lon_min: float = -19.3, lon_max: float = 7.8, map_filter: str = ""):
    table_sql = _quote_identifier(table)
    geom_sql = _quote_identifier(geomField)
    query = f"""
    SELECT *, geom_4326 AS geom FROM (
        SELECT * EXCLUDE ({geom_sql}),
               ST_AsText(ST_Transform(ST_GeomFromText({geom_sql}), 'EPSG:32630', 'EPSG:4326')) AS geom_4326
        FROM {table_sql}
        WHERE {geom_sql} IS NOT NULL
          AND ST_Within(
              ST_MakeEnvelope({lon_min}::DOUBLE, {lat_min}::DOUBLE, {lon_max}::DOUBLE, {lat_max}::DOUBLE),
              ST_Transform(ST_GeomFromText({geom_sql}), 'EPSG:32630', 'EPSG:4326')){_filter_clause(map_filter)}
    ) AS source_rows
    LIMIT 1000
    """
    return databaseService.runQuery(query, True)


def getH3Data(table: str, latitudeField: str, longitudeField: str, aggFields: list, level: int = 5,
              lat_min: float = 26.5, lat_max: float = 44.5, lon_min: float = -19.3, lon_max: float = 7.8,
              map_filter: str = ""):
    table_sql = _quote_identifier(table)
    latitude_sql = _quote_identifier(latitudeField)
    longitude_sql = _quote_identifier(longitudeField)
    aggregate_sql = [
        f"avg({_quote_identifier(field)}) AS {_quote_identifier(field)}"
        for field in (aggFields or [])
    ]
    select_sql = ", ".join([
        "h3_cell",
        "h3_cell_to_boundary_wkt(h3_cell) AS geom",
        "count(*) AS count",
        *aggregate_sql
    ])

    query = f"""
    SELECT {select_sql}
    FROM (
        SELECT *, h3_latlng_to_cell(
            TRY_CAST({latitude_sql} AS DOUBLE),
            TRY_CAST({longitude_sql} AS DOUBLE),
            {level}
        ) AS h3_cell
        FROM {table_sql}
        WHERE TRY_CAST({latitude_sql} AS DOUBLE) BETWEEN {lat_min} AND {lat_max}
          AND TRY_CAST({longitude_sql} AS DOUBLE) BETWEEN {lon_min} AND {lon_max}{_filter_clause(map_filter)}
    ) AS source_rows
    GROUP BY h3_cell
    ORDER BY count DESC
    """
    return databaseService.runQuery(query, True)


def getRecords(table: str, latitudeField: str, longitudeField: str, fields: list,
               lat_min: float = 26.5, lat_max: float = 44.5, lon_min: float = -19.3, lon_max: float = 7.8,
               map_filter: str = ""):
    table_sql = _quote_identifier(table)
    latitude_sql = _quote_identifier(latitudeField)
    longitude_sql = _quote_identifier(longitudeField)
    selected_fields = [field for field in (fields or []) if field not in (latitudeField, longitudeField)]
    extra_sql = [f"{_quote_identifier(field)} AS {_quote_identifier(field)}" for field in selected_fields]
    select_sql = ", ".join([
        f"round(TRY_CAST({latitude_sql} AS DOUBLE), 5) AS latitude",
        f"round(TRY_CAST({longitude_sql} AS DOUBLE), 5) AS longitude",
        *extra_sql
    ])

    query = f"""
    SELECT {select_sql}
    FROM {table_sql}
    WHERE TRY_CAST({latitude_sql} AS DOUBLE) BETWEEN {lat_min} AND {lat_max}
      AND TRY_CAST({longitude_sql} AS DOUBLE) BETWEEN {lon_min} AND {lon_max}{_filter_clause(map_filter)}
    LIMIT 100000
    """
    return databaseService.runQuery(query, True)


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

@router.get("/csv", response_class=Response)
async def csv(table: str, latitudeField: str, longitudeField: str, bbox: str, fields: str = "", filter: str = ""):
    lat_min, lat_max, lon_min, lon_max = _parse_bbox(bbox)
    field_list = [field for field in fields.split(",") if field]
    if not latitudeField or not longitudeField:
        raise HTTPException(status_code=400, detail="Latitude and longitude columns are required")
    _validated_map_fields(table, latitudeField, longitudeField, fields=field_list)

    starttime = time.time()
    df = getRecords(table, latitudeField, longitudeField, field_list, lat_min, lat_max, lon_min, lon_max, filter)
    log.info(f"Size {len(df)} records - {df.memory_usage(deep=True).sum() / 1024 ** 2} Mb - {time.time() - starttime} seconds")
    return Response(content=df.to_csv(index=False), media_type="text/csv")


@router.get("/geojson")
async def create_map_geojson(table: str, latitudeField: str = "", longitudeField: str = "",
                             geomField: str = "", bbox: str = "-19.3,26.5,7.8,44.5",
                             level: int = 5, fields: str = "", filter: str = ""):
    if not 0 <= level <= 15:
        raise HTTPException(status_code=400, detail="H3 level must be between 0 and 15")

    lat_min, lat_max, lon_min, lon_max = _parse_bbox(bbox)
    field_list = [field for field in fields.split(",") if field]
    _validated_map_fields(
        table, latitudeField or None, longitudeField or None, geomField or None, field_list
    )

    starttime = time.time()
    if latitudeField and longitudeField:
        df = getH3Data(table, latitudeField, longitudeField, field_list, level,
                       lat_min, lat_max, lon_min, lon_max, filter)
    elif geomField:
        df = getGeom(table, geomField, lat_min, lat_max, lon_min, lon_max, filter)
    else:
        raise HTTPException(
            status_code=400, detail="Select latitude and longitude columns or a geometry column"
        )

    df = df.fillna(-1)
    geojson_obj = getFeatureCollection(df, field_list)
    elapsed = time.time() - starttime
    response_object = {
        "metadata": {
            "records": len(df),
            "dfsize": round(df.memory_usage(deep=True).sum() / 1024 ** 2, 2),
            "objectSize": 0,
            "time": round(elapsed, 2)
        },
        "geojson": geojson_obj
    }
    response_object["metadata"]["objectSize"] = round(len(str(response_object)) / 1024 ** 2, 2)
    log.info(f"Map query returned {len(df)} records in {elapsed:.2f} seconds")
    return JSONResponse(content=response_object)


@router.get("/html")
async def create_map(table: str, level: int = 5):
    raise HTTPException(
        status_code=410,
        detail="The legacy HTML map endpoint was retired; use /maps/geojson instead"
    )


@router.get("/mapbox_token")
def getMapboxToken():
    log.info("Getting Mapbox token")
    token = mapsService.mapbox_access_token
    if not token:
        raise HTTPException(status_code=503, detail="Mapbox is not configured")
    return {"token": token}
