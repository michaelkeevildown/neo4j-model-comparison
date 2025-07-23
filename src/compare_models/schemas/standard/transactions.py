from ...common.models import GraphSchema, Node, Relationship, PropertyDefinition, Path

def get_standard_schema() -> GraphSchema:
    """
    Returns a hardcoded representation of the standard Transactions and Accounts data model.
    """
    nodes = [
        Node(
            cypher_representation="(:Customer)",
            label="Customer",
            indexes=[],
            constraints=[],
            properties=[
                PropertyDefinition(property="id", type=["String"], mandatory=True),
                PropertyDefinition(property="name", type=["String"], mandatory=False),
            ],
        ),
        Node(
            cypher_representation="(:Account)",
            label="Account",
            indexes=[],
            constraints=[],
            properties=[
                PropertyDefinition(property="id", type=["String"], mandatory=True),
                PropertyDefinition(property="type", type=["String"], mandatory=False),
            ],
        ),
        Node(
            cypher_representation="(:Transaction)",
            label="Transaction",
            indexes=[],
            constraints=[],
            properties=[
                PropertyDefinition(property="id", type=["String"], mandatory=True),
                PropertyDefinition(property="amount", type=["Float"], mandatory=True),
            ],
        ),
    ]

    relationships = [
        Relationship(
            cypher_representation="[:HAS_ACCOUNT]",
            type="HAS_ACCOUNT",
            paths=[
                Path(path="(:Customer)-[:HAS_ACCOUNT]->(:Account)")
            ],
            properties=[],
        ),
        Relationship(
            cypher_representation="[:PERFORMED_TRANSACTION]",
            type="PERFORMED_TRANSACTION",
            paths=[
                Path(path="(:Account)-[:PERFORMED_TRANSACTION]->(:Transaction)")
            ],
            properties=[],
        ),
    ]

    return GraphSchema(nodes=nodes, relationships=relationships)
