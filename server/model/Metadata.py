# models.py
from pydantic import BaseModel
from typing import List, Dict

class Metadata(BaseModel):
    description: str
    bucket: str
    path: str
    

    
