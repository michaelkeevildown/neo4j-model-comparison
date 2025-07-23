from neo4j import GraphDatabase
from ..common.config import settings
from ..common.models import GraphSchema, Node, Relationship, PropertyDefinition, Path


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

    # First, collect all label combinations from nodeTypeProperties
    label_combinations = {}
    node_properties: dict[str, list[PropertyDefinition]] = {}
    
    for prop in node_properties_result:
        if prop["propertyName"] is None:
            continue
        
        node_labels = prop["nodeLabels"]
        # Create a key from sorted labels for consistent lookup
        label_key = ":".join(sorted(node_labels))
        
        # Track which individual labels are part of multi-label combinations
        if len(node_labels) > 1:
            if label_key not in label_combinations:
                label_combinations[label_key] = node_labels
        
        if label_key not in node_properties:
            node_properties[label_key] = []
        node_properties[label_key].append(
            PropertyDefinition(
                property=prop["propertyName"],
                type=prop["propertyTypes"],
                mandatory=prop["mandatory"],
            )
        )

    # Identify which labels should be grouped together based on multi-label combinations
    labels_in_combinations = set()
    for combo in label_combinations.values():
        labels_in_combinations.update(combo)
    
    # Group nodes - handling both single and multi-label nodes
    node_groups = {}
    processed_single_labels = set()
    
    for node_data in nodes_data:
        label = node_data["name"]
        
        # Check if this label is part of a multi-label combination
        if label in labels_in_combinations:
            # Find which combination(s) this label belongs to
            for combo_key, combo_labels in label_combinations.items():
                if label in combo_labels:
                    # Use the first label in the sorted combination as primary
                    primary_label = sorted(combo_labels)[0]
                    
                    if primary_label not in node_groups:
                        node_groups[primary_label] = {
                            "primary_label": primary_label,
                            "all_labels": set(combo_labels),
                            "additional_labels": [l for l in sorted(combo_labels) if l != primary_label],
                            "indexes": [],
                            "constraints": [],
                            "properties": node_properties.get(combo_key, []),
                            "cypher_representation": f"(:{primary_label})"
                        }
                    
                    # Add indexes and constraints from this specific label
                    node_groups[primary_label]["indexes"].extend(node_data.get("indexes", []))
                    node_groups[primary_label]["constraints"].extend(node_data.get("constraints", []))
                    processed_single_labels.add(label)
        
        # If not part of a combination, treat as single-label node
        elif label not in processed_single_labels:
            node_groups[label] = {
                "primary_label": label,
                "all_labels": {label},
                "additional_labels": [],
                "indexes": node_data.get("indexes", []),
                "constraints": node_data.get("constraints", []),
                "properties": node_properties.get(label, []),
                "cypher_representation": f"(:{label})"
            }
            processed_single_labels.add(label)
    
    # Create nodes from the grouped data
    nodes = []
    for primary_label, group_data in node_groups.items():
        # Remove duplicates from indexes and constraints
        unique_indexes = list(dict.fromkeys(group_data["indexes"]))
        unique_constraints = list(dict.fromkeys(group_data["constraints"]))
        
        nodes.append(
            Node(
                cypher_representation=group_data["cypher_representation"],
                label=group_data["primary_label"],
                additional_labels=group_data["additional_labels"],
                indexes=unique_indexes,
                constraints=unique_constraints,
                properties=group_data["properties"],
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

        relationships_dict[rel_type]["paths"].append(Path(path=path))

    relationships = [Relationship(**data) for data in relationships_dict.values()]

    return GraphSchema(nodes=nodes, relationships=relationships)
