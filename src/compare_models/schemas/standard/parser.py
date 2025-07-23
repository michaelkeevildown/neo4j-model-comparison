import re
from typing import List, Dict, Optional, Tuple
import requests
from ...common.models import GraphSchema, Node, Relationship, PropertyDefinition, Path


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
    
    nodes = []
    relationships = []
    
    if node_section_match:
        nodes = parse_node_section(node_section_match.group(1))
    
    if rel_section_match:
        relationships = parse_relationship_section(rel_section_match.group(1))
    
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