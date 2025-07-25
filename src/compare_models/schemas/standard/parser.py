import re
from typing import List, Dict, Optional, Tuple
import requests
from ...common.models import GraphSchema, Node, Relationship, PropertyDefinition, Path, Constraint, Index


def fetch_markdown_content(url: str) -> str:
    """Fetch the markdown content from the given URL."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch markdown content: {e}")


def parse_property_line(line: str) -> Optional[Tuple[str, List[str], bool]]:
    """
    Parse a property line from the markdown.
    Returns: (property_name, types, is_mandatory) or None if not a property line.
    """
    # Pattern: `propertyName` (Type): Description
    match = re.match(r'^\s*-\s*`([^`]+)`\s*\(([^)]+)\):\s*(.*)$', line)
    if not match:
        return None
    
    property_name = match.group(1)
    type_str = match.group(2)
    description = match.group(3)
    
    # Parse types (could be "String" or "List of Float")
    types = []
    if "List of" in type_str:
        inner_type = type_str.replace("List of", "").strip()
        types = [f"List[{inner_type}]"]
    else:
        types = [type_str]
    
    # Check if optional
    is_mandatory = not description.startswith("Optional:")
    
    return property_name, types, is_mandatory


def parse_node_section(content: str) -> List[Node]:
    """Parse the node labels and properties section."""
    nodes = []
    lines = content.split('\n')
    
    current_node = None
    current_labels = []
    current_properties = []
    in_properties = False
    in_labels = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for node header (e.g., ### Account)
        if line.startswith('### '):
            # Save previous node if exists
            if current_node:
                primary_label = current_node
                # For nodes with multiple labels, extract the base label and additional labels
                if len(current_labels) > 1:
                    # Filter out non-label entries and the primary label
                    additional = [l for l in current_labels[1:] if l not in ['Labels:', primary_label]]
                    nodes.append(Node(
                        cypher_representation=f"(:{primary_label})",
                        label=primary_label,
                        additional_labels=additional,
                        indexes=[],
                        constraints=[],
                        properties=current_properties
                    ))
                else:
                    nodes.append(Node(
                        cypher_representation=f"(:{primary_label})",
                        label=primary_label,
                        additional_labels=[],
                        indexes=[],
                        constraints=[],
                        properties=current_properties
                    ))
            
            # Start new node
            current_node = line[4:].strip()
            current_labels = [current_node]
            current_properties = []
            in_properties = False
            in_labels = False
            
        # Check for Labels section
        elif line.strip() == '- Labels:':
            in_labels = True
            in_properties = False
            
        # Check for Properties section
        elif line.strip() == '- Properties:':
            in_properties = True
            in_labels = False
            
        # Parse labels
        elif in_labels and line.strip().startswith('- `') and '`:' in line:
            # Extract label name from pattern like: - `Internal`: Label for accounts...
            label_match = re.match(r'^\s*-\s*`([^`]+)`:', line)
            if label_match:
                label = label_match.group(1)
                if label not in current_labels:
                    current_labels.append(label)
        
        # Parse properties
        elif in_properties:
            parsed_property = parse_property_line(line)
            if parsed_property:
                prop_name, prop_types, is_mandatory = parsed_property
                current_properties.append(PropertyDefinition(
                    property=prop_name,
                    type=prop_types,
                    mandatory=is_mandatory
                ))
        
        i += 1
    
    # Don't forget the last node
    if current_node:
        primary_label = current_node
        if len(current_labels) > 1:
            additional = [l for l in current_labels[1:] if l not in ['Labels:', primary_label]]
            nodes.append(Node(
                cypher_representation=f"(:{primary_label})",
                label=primary_label,
                additional_labels=additional,
                indexes=[],
                constraints=[],
                properties=current_properties
            ))
        else:
            nodes.append(Node(
                cypher_representation=f"(:{primary_label})",
                label=primary_label,
                additional_labels=[],
                indexes=[],
                constraints=[],
                properties=current_properties
            ))
    
    return nodes


def parse_relationship_section(content: str) -> List[Relationship]:
    """Parse the relationship types and properties section."""
    relationships = []
    lines = content.split('\n')
    
    current_rel = None
    current_direction = None
    current_properties = []
    in_properties = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for relationship header (e.g., ### :HAS_ACCOUNT)
        if line.startswith('### :'):
            # Save previous relationship if exists
            if current_rel and current_direction:
                # Parse direction (e.g., Customer->Account)
                parts = current_direction.split('->')
                if len(parts) == 2:
                    source = parts[0].strip()
                    target = parts[1].strip()
                    path_str = f"(:{source})-[:{current_rel}]->(:{target})"
                    
                    relationships.append(Relationship(
                        cypher_representation=f"[:{current_rel}]",
                        type=current_rel,
                        paths=[Path(path=path_str)],
                        properties=current_properties
                    ))
            
            # Start new relationship
            current_rel = line[5:].strip()  # Remove "### :"
            current_direction = None
            current_properties = []
            in_properties = False
            
        # Check for Direction
        elif line.startswith('- Direction:'):
            current_direction = line.replace('- Direction:', '').strip()
            
        # Check for Properties
        elif line.startswith('- Properties:'):
            in_properties = True
            # Check if next line says "None"
            if i + 1 < len(lines) and lines[i + 1].strip() == 'None':
                current_properties = []
                in_properties = False
                i += 1  # Skip the "None" line
        
        # Parse properties
        elif in_properties:
            parsed_property = parse_property_line(line)
            if parsed_property:
                prop_name, prop_types, is_mandatory = parsed_property
                current_properties.append(PropertyDefinition(
                    property=prop_name,
                    type=prop_types,
                    mandatory=is_mandatory
                ))
        
        i += 1
    
    # Don't forget the last relationship
    if current_rel and current_direction:
        parts = current_direction.split('->')
        if len(parts) == 2:
            source = parts[0].strip()
            target = parts[1].strip()
            path_str = f"(:{source})-[:{current_rel}]->(:{target})"
            
            relationships.append(Relationship(
                cypher_representation=f"[:{current_rel}]",
                type=current_rel,
                paths=[Path(path=path_str)],
                properties=current_properties
            ))
    
    return relationships


def parse_constraints_section(content: str) -> Dict[str, List[Constraint]]:
    """Parse the constraints section and return a dict mapping labels to constraints."""
    constraints_by_label = {}
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines, comments, and code block markers
        if not line or line.startswith('//') or line == '```cypher' or line == '```':
            i += 1
            continue
        
        # Check if this line starts a CREATE CONSTRAINT statement
        if line.startswith('CREATE CONSTRAINT'):
            # Constraints can span multiple lines, so collect the full statement
            full_statement = line
            
            # Look ahead to get the complete statement
            j = i + 1
            while j < len(lines) and not lines[j].strip().endswith(';'):
                full_statement += ' ' + lines[j].strip()
                j += 1
            
            # Add the final line with semicolon
            if j < len(lines):
                full_statement += ' ' + lines[j].strip()
            
            # Now parse the complete statement
            # Extract constraint name
            name_match = re.search(r'CREATE CONSTRAINT\s+(\w+)', full_statement)
            constraint_name = name_match.group(1) if name_match else None
            
            # Extract label from FOR (x:Label) pattern
            label_match = re.search(r'FOR\s*\([^:]+:([^)]+)\)', full_statement)
            if label_match:
                label = label_match.group(1).strip()
                
                # Initialize list for this label if needed
                if label not in constraints_by_label:
                    constraints_by_label[label] = []
                
                # Extract constraint details
                if 'IS NODE KEY' in full_statement:
                    # Extract properties from REQUIRE clause
                    require_match = re.search(r'REQUIRE\s+(.+?)\s+IS NODE KEY', full_statement)
                    if require_match:
                        props_str = require_match.group(1)
                        # Remove parentheses and node alias
                        props_str = re.sub(r'^\(', '', props_str)
                        props_str = re.sub(r'\)$', '', props_str)
                        props_str = re.sub(r'[a-z]+\.', '', props_str)  # Remove alias like 'c.'
                        
                        # Parse properties
                        if ',' in props_str:
                            properties = [p.strip() for p in props_str.split(',')]
                        else:
                            properties = [props_str.strip()]
                        
                        constraint = Constraint(
                            type="NODE_KEY",
                            properties=properties,
                            name=constraint_name
                        )
                        
                        constraints_by_label[label].append(constraint)
            
            # Skip to the next statement
            i = j + 1
        else:
            i += 1
    
    return constraints_by_label


def parse_indexes_section(content: str) -> Dict[str, List[Index]]:
    """Parse the indexes section and return a dict mapping labels to indexes."""
    indexes_by_label = {}
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines and pure comments
        if not line or line == '//':
            i += 1
            continue
            
        # Skip code block markers
        if line == '```cypher' or line == '```':
            i += 1
            continue
            
        # Parse CREATE INDEX statements
        if 'CREATE INDEX' in line and 'FOR' in line:
            # Extract index name
            name_match = re.search(r'CREATE INDEX\s+(\w+)', line)
            index_name = name_match.group(1) if name_match else None
            
            # Extract label from FOR (x:Label) pattern
            label_match = re.search(r'FOR\s*\([^:]+:([^)]+)\)', line)
            if label_match:
                label = label_match.group(1).strip()
                
                # Initialize list for this label if needed
                if label not in indexes_by_label:
                    indexes_by_label[label] = []
                
                # Check for regular property index
                on_match = re.search(r'ON\s*\(([^)]+)\)', line)
                if on_match:
                    prop = on_match.group(1).strip()
                    # Remove alias prefix (e.g., 't.date' -> 'date')
                    prop = re.sub(r'^[a-z]+\.', '', prop)
                    
                    index = Index(
                        type="PROPERTY",
                        properties=[prop],
                        name=index_name
                    )
                    indexes_by_label[label].append(index)
        
        # Parse FULLTEXT INDEX statements
        elif 'CREATE FULLTEXT INDEX' in line and 'FOR' in line:
            # Extract index name
            name_match = re.search(r'CREATE FULLTEXT INDEX\s+(\w+)', line)
            index_name = name_match.group(1) if name_match else None
            
            label_match = re.search(r'FOR\s*\([^:]+:([^)]+)\)', line)
            if label_match:
                label = label_match.group(1).strip()
                
                if label not in indexes_by_label:
                    indexes_by_label[label] = []
                
                # Extract properties from ON EACH clause
                on_each_match = re.search(r'ON EACH\s*\[([^\]]+)\]', line)
                if on_each_match:
                    props_str = on_each_match.group(1)
                    # Remove alias prefixes and clean property names
                    props = [re.sub(r'^[a-z]+\.', '', p.strip().strip("'\"")) for p in props_str.split(',')]
                    
                    index = Index(
                        type="FULLTEXT",
                        properties=props,
                        name=index_name
                    )
                    indexes_by_label[label].append(index)
        
        # Parse vector index (multi-line CALL statement)
        elif line.startswith('CALL db.index.vector.createNodeIndex'):
            # Look ahead to find all parameters
            if i + 5 < len(lines):
                # Extract index name (first parameter)
                name_line = lines[i + 1].strip().strip(',').strip("'\"")
                # Extract label (second parameter)
                label_line = lines[i + 2].strip().strip(',').strip("'\"")
                # Extract property (third parameter) 
                prop_line = lines[i + 3].strip().strip(',').strip("'\"")
                # Extract dimensions (fourth parameter)
                dim_line = lines[i + 4].strip().strip(',')
                # Extract similarity metric (fifth parameter)
                similarity_line = lines[i + 5].strip().strip(',').strip("'\"").rstrip(')').split('//')[0].strip().strip("'\")")
                
                if label_line not in indexes_by_label:
                    indexes_by_label[label_line] = []
                
                # Parse dimensions as integer
                try:
                    dimensions = int(dim_line)
                except ValueError:
                    dimensions = None
                
                config = {}
                if dimensions:
                    config["dimensions"] = dimensions
                if similarity_line:
                    config["similarity"] = similarity_line
                
                index = Index(
                    type="VECTOR",
                    properties=[prop_line],
                    name=name_line,
                    config=config if config else None
                )
                indexes_by_label[label_line].append(index)
                i += 6  # Skip the entire CALL block
                continue
        
        i += 1
    
    return indexes_by_label


def parse_standard_schema(markdown_content: str) -> GraphSchema:
    """Parse the standard schema from the markdown content."""
    # Extract section 1 (Node Labels and Properties)
    node_section_match = re.search(
        r'## 1\. Node Labels and Properties\n(.*?)(?=## 2\.|$)', 
        markdown_content, 
        re.DOTALL
    )
    
    # Extract section 2 (Relationship Types and Properties)
    rel_section_match = re.search(
        r'## 2\. Relationship Types and Properties\n(.*?)(?=## 3\.|$)', 
        markdown_content, 
        re.DOTALL
    )
    
    # Extract section 3 (Constraints and Indexes)
    constraints_section_match = re.search(
        r'## 3\. Constraints and Indexes\n(.*?)(?=## 4\.|## Demo|$)', 
        markdown_content, 
        re.DOTALL
    )
    
    nodes = []
    relationships = []
    constraints_by_label = {}
    indexes_by_label = {}
    
    if node_section_match:
        nodes = parse_node_section(node_section_match.group(1))
    
    if rel_section_match:
        relationships = parse_relationship_section(rel_section_match.group(1))
    
    if constraints_section_match:
        # Parse constraints and indexes from section 3
        section_content = constraints_section_match.group(1)
        constraints_by_label = parse_constraints_section(section_content)
        indexes_by_label = parse_indexes_section(section_content)
    
    # Map constraints and indexes to nodes
    for node in nodes:
        # Add constraints for this node's label
        if node.label in constraints_by_label:
            node.constraints = constraints_by_label[node.label]
        
        # Add indexes for this node's label
        if node.label in indexes_by_label:
            node.indexes = indexes_by_label[node.label]
    
    # Merge duplicate relationships with same type but different paths
    merged_relationships = {}
    for rel in relationships:
        if rel.type in merged_relationships:
            # Add the path to existing relationship
            merged_relationships[rel.type].paths.extend(rel.paths)
        else:
            merged_relationships[rel.type] = rel
    
    return GraphSchema(
        nodes=nodes,
        relationships=list(merged_relationships.values())
    )