# models.py
from pydantic import BaseModel
from typing import List, Dict

class SaveQueryRequestDTO(BaseModel):
    query: str
    sqlQueryName: str
    description: str
    