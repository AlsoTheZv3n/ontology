from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class OntologyObject(BaseModel):
    type: str
    key: str
    properties: dict[str, Any] = Field(default_factory=dict)
    sources: dict[str, Any] = Field(default_factory=dict)


class CompanyObject(OntologyObject):
    type: str = "company"


class PersonObject(OntologyObject):
    type: str = "person"


class ArticleObject(OntologyObject):
    type: str = "article"


class RepositoryObject(OntologyObject):
    type: str = "repository"


class EventObject(OntologyObject):
    type: str = "event"


# --- API Response Schemas ---


class ObjectResponse(BaseModel):
    id: UUID
    type: str
    key: str
    properties: dict[str, Any]
    sources: dict[str, Any]
    created_at: str
    updated_at: str


class ObjectListResponse(BaseModel):
    items: list[ObjectResponse]
    total: int


class LinkResponse(BaseModel):
    id: UUID
    type: str
    from_id: UUID
    to_id: UUID
    weight: float
    properties: dict[str, Any]
    created_at: str


class GraphNode(BaseModel):
    id: str
    type: str
    data: dict[str, Any]


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class InsightAnomaly(BaseModel):
    key: str
    name: str | None
    missing_sources: list[str]
    source_coverage: float


class TopCompany(BaseModel):
    key: str
    name: str | None
    value: float


class SyncResponse(BaseModel):
    status: str
    source: str
