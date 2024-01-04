from pydantic import BaseModel
from typing import List
import pandas as pd
import json

class PublishEndpointRequestDTO(BaseModel):
    id_query: int
    endpoint: str
    parameters: List[str]
    description: str

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame):
        print("DF:", df )
        id_query = df['id_query'].iloc[0]
        endpoint = df['endpoint'].iloc[0]
        parameters = df['parameters'].iloc[0]
        description = df['description'].iloc[0]

        # parameters  are stored as a json string: ["marca", "marca_id"] convert to list
        parameters = json.loads(parameters)

        return cls(id_query=id_query, endpoint=endpoint, parameters=parameters, description=description)
    