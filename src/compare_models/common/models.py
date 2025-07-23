from typing import List, Optional
from pydantic import BaseModel


class PropertyDefinition(BaseModel):
    property: str
    type: List[str]
    mandatory: bool


class Node(BaseModel):
    cypher_representation: str
    label: str
    indexes: List[str]
    constraints: List[str]
    properties: List[PropertyDefinition]
    detail: Optional[str] = None


class Path(BaseModel):
    path: str


class Relationship(BaseModel):
    cypher_representation: str
    type: str
    paths: List[Path]
    properties: List[PropertyDefinition]


class GraphSchema(BaseModel):
    nodes: List[Node]
    relationships: List[Relationship]
