from ...common.models import GraphSchema
from .parser import fetch_markdown_content, parse_standard_schema

# URL to the standard Transactions and Accounts model documentation
STANDARD_MODEL_URL = "https://neo4j.com/developer/industry-use-cases/_attachments/transactions-base-model.txt"

# Cache for the parsed schema to avoid repeated HTTP requests
_cached_schema = None

def get_standard_schema() -> GraphSchema:
    """
    Returns the standard Transactions and Accounts data model by parsing the official documentation.
    The result is cached to avoid repeated HTTP requests.
    """
    global _cached_schema
    
    if _cached_schema is None:
        try:
            # Fetch and parse the markdown content
            markdown_content = fetch_markdown_content(STANDARD_MODEL_URL)
            _cached_schema = parse_standard_schema(markdown_content)
        except Exception as e:
            # If parsing fails, fall back to a minimal hardcoded schema
            print(f"Warning: Failed to fetch/parse standard schema: {e}")
            print("Falling back to minimal hardcoded schema")
            
            from ...common.models import Node, Relationship, PropertyDefinition, Path
            
            # Minimal fallback schema
            nodes = [
                Node(
                    cypher_representation="(:Customer)",
                    label="Customer",
                    indexes=[],
                    constraints=[],
                    properties=[
                        PropertyDefinition(property="customerId", type=["String"], mandatory=True),
                    ],
                ),
                Node(
                    cypher_representation="(:Account)",
                    label="Account",
                    indexes=[],
                    constraints=[],
                    properties=[
                        PropertyDefinition(property="accountNumber", type=["String"], mandatory=True),
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
            ]
            
            _cached_schema = GraphSchema(nodes=nodes, relationships=relationships)
    
    return _cached_schema
