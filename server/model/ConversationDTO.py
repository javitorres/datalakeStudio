from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConversationDTO(BaseModel):
    title: str = Field(max_length=200)
    messages: List[Dict[str, Any]] = Field(max_length=500)
    database: Optional[str] = None


class ConversationTitleDTO(BaseModel):
    title: str = Field(min_length=1, max_length=200)
