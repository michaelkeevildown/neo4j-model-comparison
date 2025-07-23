from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class PropertyDefinition(BaseModel):
    property: str
    type: List[str]
    mandatory: bool


class Constraint(BaseModel):
    type: str  # "NODE_KEY", "UNIQUE", "EXISTS", etc.
    properties: List[str]  # Properties involved in the constraint
    name: Optional[str] = None  # Constraint name if available


class Index(BaseModel):
    type: str  # "PROPERTY", "FULLTEXT", "VECTOR"
    properties: List[str]  # Properties indexed
    name: Optional[str] = None  # Index name if available
    config: Optional[Dict[str, Any]] = None  # Additional configuration (dimensions, similarity, etc.)


class Node(BaseModel):
    cypher_representation: str
    label: str
    additional_labels: List[str] = []  # Additional labels that can be applied to this node
    indexes: List[Index]
    constraints: List[Constraint]
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
