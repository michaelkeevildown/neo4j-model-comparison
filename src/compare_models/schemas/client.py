from neo4j import GraphDatabase, NotificationMinimumSeverity
from ..common.config import settings
from ..common.models import GraphSchema, Node, Relationship, PropertyDefinition, Path, Constraint, Index


def get_graph_schema() -> GraphSchema:
    # Suppress Neo4j warnings about propertyTypes field format changes in future versions
    # The warnings are about db.schema.nodeTypeProperties() and db.schema.relTypeProperties()
    # procedures changing their propertyTypes field output format in the next major version
    with GraphDatabase.driver(
        settings.uri, 
        auth=(settings.username, settings.password),
        notifications_min_severity=NotificationMinimumSeverity.OFF
    ) as driver:
        with driver.session(database=settings.database) as session:
            schema_result = session.run("call db.schema.visualization()").data()
            node_properties_result = session.run(
                "CALL db.schema.nodeTypeProperties()"
            ).data()
            rel_properties_result = session.run(
                "CALL db.schema.relTypeProperties()"
            ).data()
            constraints_result = session.run("SHOW CONSTRAINTS").data()
            indexes_result = session.run("SHOW INDEXES").data()

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
    
    # Process constraints from SHOW CONSTRAINTS
    constraints_by_label = {}
    for constraint in constraints_result:
        # Extract labels from constraint definition
        labels = constraint.get("labelsOrTypes", []) or []
        constraint_type = constraint.get("type", "")
        constraint_name = constraint.get("name", "")
        properties = constraint.get("properties", []) or []
        
        # Handle different constraint types
        if constraint_type == "NODE_KEY":
            constraint_obj = Constraint(
                type="NODE_KEY",
                properties=properties,
                name=constraint_name
            )
        elif constraint_type == "UNIQUENESS":
            constraint_obj = Constraint(
                type="UNIQUE",
                properties=properties,
                name=constraint_name
            )
        else:
            # Handle other constraint types
            constraint_obj = Constraint(
                type=constraint_type,
                properties=properties,
                name=constraint_name
            )
        
        # Map to all labels involved
        for label in labels:
            if label not in constraints_by_label:
                constraints_by_label[label] = []
            constraints_by_label[label].append(constraint_obj)
    
    # Process indexes from SHOW INDEXES
    indexes_by_label = {}
    for index in indexes_result:
        # Skip system indexes
        if index.get("name", "").startswith("system."):
            continue
            
        labels = index.get("labelsOrTypes", []) or []
        index_type = index.get("type", "")
        index_name = index.get("name", "")
        properties = index.get("properties", []) or []
        
        # Map Neo4j index types to our types
        if index_type == "FULLTEXT":
            mapped_type = "FULLTEXT"
        elif index_type == "VECTOR":
            mapped_type = "VECTOR"
        elif index_type in ["BTREE", "RANGE"]:
            mapped_type = "PROPERTY"
        else:
            mapped_type = index_type
        
        # Extract configuration if available
        config = {}
        if index_type == "FULLTEXT":
            # Fulltext indexes might have analyzer configuration
            if "analyzer" in index:
                config["analyzer"] = index["analyzer"]
        elif index_type == "VECTOR":
            # Vector indexes have dimensions and similarity
            if "dimensions" in index:
                config["dimensions"] = index["dimensions"]
            if "similarity" in index:
                config["similarity"] = index["similarity"]
        
        index_obj = Index(
            type=mapped_type,
            properties=properties,           
            name=index_name,
            config=config if config else None
        )
        
        # Map to all labels involved
        for label in labels:
            if label not in indexes_by_label:
                indexes_by_label[label] = []
            indexes_by_label[label].append(index_obj)
    
    # Create nodes from the grouped data
    nodes = []
    for primary_label, group_data in node_groups.items():
        # Get constraints and indexes for this node label
        node_constraints = constraints_by_label.get(primary_label, [])
        node_indexes = indexes_by_label.get(primary_label, [])
        
        # Also check additional labels for multi-label nodes
        for additional_label in group_data["additional_labels"]:
            node_constraints.extend(constraints_by_label.get(additional_label, []))
            node_indexes.extend(indexes_by_label.get(additional_label, []))
        
        # Remove duplicates while preserving order
        unique_constraints = []
        unique_indexes = []
        
        for constraint in node_constraints:
            if constraint not in unique_constraints:
                unique_constraints.append(constraint)
                
        for index in node_indexes:
            if index not in unique_indexes:
                unique_indexes.append(index)
        
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
