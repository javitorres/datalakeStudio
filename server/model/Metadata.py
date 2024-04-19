# models.py
from pydantic import BaseModel
from typing import List, Dict
from typing import Optional

class Metadata(BaseModel):
    description: str
    owner: str
    schema: Optional[str] = None
    bucket: str
    path: str


    

    
