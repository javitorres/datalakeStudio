from pydantic import BaseModel
from typing import List
import pandas as pd
import json
from typing import Optional

class Parameter(BaseModel):
    name: str
    exampleValue: str

    def to_dict(self):
        return {
            "name": self.name,
            "exampleValue": self.exampleValue
        }

class PublishEndpointRequestDTO(BaseModel):
    id_query: int
    id_endpoint: int
    endpoint: str
    parameters: Optional[List[Parameter]]
    description: Optional[str]
    query: str
    queryStringTest: Optional[str]
    status: str

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame):
        if df is None or df.empty:
            return None
        id_query = df['id_query'].iloc[0]
        id_endpoint = df['id_endpoint'].iloc[0]
        endpoint = df['endpoint'].iloc[0]
        parameters = df.get('parameters', [None]).iloc[0]
        description = df.get('description', [None]).iloc[0]
        query = df['query'].iloc[0]
        queryStringTest = df.get('queryStringTest', [None]).iloc[0]
        status = df['status'].iloc[0]

        # parameters  are stored as a json string: ["marca", "marca_id"] convert to list
        # Asumiendo que 'parameters' es una cadena JSON de una lista de diccionarios
        parameters_json = df.get('parameters', [None]).iloc[0]
        if parameters_json is not None:
            # Convertir la cadena JSON a una lista de diccionarios
            parameters = json.loads(parameters_json)
        else:
            parameters = None

        return cls(id_query=id_query, id_endpoint=id_endpoint, endpoint=endpoint, parameters=parameters, description=description, query=query, queryStringTest=queryStringTest, status=status)
    