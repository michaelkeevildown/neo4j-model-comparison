from neo4j import GraphDatabase
from ..common.config import settings
from ..common.models import GraphSchema, Node, Relationship, PropertyDefinition


def get_graph_schema() -> GraphSchema:
    with GraphDatabase.driver(
        settings.uri, auth=(settings.username, settings.password)
    ) as driver:
        with driver.session(database=settings.database) as session:
            schema_result = session.run("call db.schema.visualization()").data()
            node_properties_result = session.run(
                "CALL db.schema.nodeTypeProperties()"
            ).data()
            rel_properties_result = session.run(
                "CALL db.schema.relTypeProperties()"
            ).data()

    payload = schema_result[0]
    nodes_data = payload.get("nodes", [])
    relationships_data = payload.get("relationships", [])

    node_properties: dict[str, list[PropertyDefinition]] = {}
    for prop in node_properties_result:
        if prop["propertyName"] is None:
            continue
        label = prop["nodeLabels"][0]
        if label not in node_properties:
            node_properties[label] = []
        node_properties[label].append(
            PropertyDefinition(
                property=prop["propertyName"],
                type=prop["propertyTypes"],
                mandatory=prop["mandatory"],
            )
        )

    nodes = []
    for node_data in nodes_data:
        label = node_data["name"]
        nodes.append(
            Node(
                cypher_representation=f"(:{label})",
                label=label,
                indexes=node_data.get("indexes", []),
                constraints=node_data.get("constraints", []),
                properties=node_properties.get(label, []),
            )
        )

    rel_properties: dict[str, list[PropertyDefinition]] = {}
    for prop in rel_properties_result:
        if prop["propertyName"] is None:
            continue
        rel_type = prop["relType"].replace("`", "")
        if rel_type not in rel_properties:
            rel_properties[rel_type] = []
        rel_properties[rel_type].append(
            PropertyDefinition(
                property=prop["propertyName"],
                type=prop["propertyTypes"],
                mandatory=prop["mandatory"],
            )
        )

    relationships_dict = {}
    for rel_data in relationships_data:
        start_node = rel_data[0]["name"]
        rel_type = rel_data[1]
        end_node = rel_data[2]["name"]
        path = f"(:{start_node})-[:{rel_type}]->(:{end_node})"

        if rel_type not in relationships_dict:
            relationships_dict[rel_type] = {
                "cypher_representation": f"[:{rel_type}]",
                "type": rel_type,
                "paths": [],
                "properties": rel_properties.get(rel_type, []),
            }

        relationships_dict[rel_type]["paths"].append({"path": path})

    relationships = [Relationship(**data) for data in relationships_dict.values()]

    return GraphSchema(nodes=nodes, relationships=relationships)
