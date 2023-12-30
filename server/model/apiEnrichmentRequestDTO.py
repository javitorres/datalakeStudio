# models.py
from pydantic import BaseModel
from typing import List, Dict

class Mapping(BaseModel):
    jsonField: str
    newFieldName: str

class Method(BaseModel):
    controller: str
    method: str
    path: str

class ApiEnrichmentRequestDTO(BaseModel):
    tableName: str
    parameters: Dict[str, str]
    mappings: List[Mapping]
    recordsToProcess: int
    service: str
    method: Method
    url: str
    newTableName: str
