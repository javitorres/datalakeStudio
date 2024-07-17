from fastapi import FastAPI
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import geopandas as gpd
import h3
from shapely.geometry import Polygon
from geojson import Feature, FeatureCollection
import plotly.express as px

router = APIRouter(prefix="/maps")

############################################################################################################

def add_geometry(row):
    points = h3.h3_to_geo_boundary(row['h3_cell'], True)
    return Polygon(points)

def geo_to_h3(row, H3_res):
    return h3.geo_to_h3(lat=row.LATDD83, lng=row.LONGDD83, resolution=H3_res)

@router.get("/", response_class=HTMLResponse)
async def create_map():
    fire_ignitions = gpd.read_file("SCFireOccurrence.gdb.zip")
    H3_res = 5
    fire_ignitions['h3_cell'] = fire_ignitions.apply(lambda row: geo_to_h3(row, H3_res), axis=1)
    fire_ignitions_g = (fire_ignitions
                        .groupby('h3_cell')
                        .apply(lambda x: list(x.index))
                        .reset_index(name='ids'))
    fire_ignitions_g['count'] = fire_ignitions_g['ids'].apply(len)
    fire_ignitions_g['geometry'] = fire_ignitions_g.apply(add_geometry, axis=1)

    features = [Feature(geometry=row['geometry'], properties={"count": row['count']})
                for index, row in fire_ignitions_g.iterrows()]
    geojson_obj = FeatureCollection(features)

    fig = px.choropleth_mapbox(
        fire_ignitions_g,
        geojson=geojson_obj,
        locations='h3_cell',
        color='count',
        color_continuous_scale="Viridis",
        range_color=(0, fire_ignitions_g['count'].max()),
        mapbox_style='carto-positron',
        zoom=7,
        center={"lat": 65.469211, "lon": -136.713865},
        opacity=0.7,
        labels={'count': '# of fire ignitions'}
    )
    fig.update_layout(margin={"r":0, "t":0, "l":0, "b":0})
    return fig.to_html()