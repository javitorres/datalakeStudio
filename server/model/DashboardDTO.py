from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DashboardDTO(BaseModel):
    title: str = Field(max_length=200)
    spec: Dict[str, Any]
    # The instructions given to the assistant and its answers: [{role, text}]
    history: List[Dict[str, Any]] = Field(default_factory=list, max_length=200)
    database: Optional[str] = None


class PublishDashboardDTO(BaseModel):
    path: str = Field(min_length=1, max_length=260)
    # The SQL of each widget and filter, by its id, with {name} placeholders for the filter values
    queries: Dict[str, str] = Field(max_length=80)


class PublishedQueryDTO(BaseModel):
    query: str = Field(min_length=1, max_length=40)
    filters: Dict[str, Any] = Field(default_factory=dict, max_length=40)
