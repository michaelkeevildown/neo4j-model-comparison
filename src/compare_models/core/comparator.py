from typing import Dict, Any, Optional
from ..common.models import GraphSchema
from .similarity import FieldMatcher, MatchType


def compare_schemas(existing_schema: GraphSchema, standard_schema: GraphSchema, 
                   similarity_threshold: float = 0.7, use_adaptive: bool = True) -> Dict[str, Any]:
    """
    Compares the existing schema against the standard schema and returns a comprehensive analysis.
    
    Args:
        existing_schema: The customer's current database schema
        standard_schema: The standard Neo4j schema to compare against
        similarity_threshold: Minimum similarity score to consider a match (0.0 to 1.0)
        use_adaptive: Whether to use adaptive similarity weighting
        
    Returns:
        Comprehensive comparison results with matches, gaps, and recommendations
    """
    # Initialize the field matcher with specified configuration
    matcher = FieldMatcher(
        use_adaptive=use_adaptive, 
        similarity_threshold=similarity_threshold
    )
    
    # Perform the comprehensive schema comparison
    comparison_results = matcher.match_schemas(existing_schema, standard_schema)
    
    # Enhance the results with additional analysis
    enhanced_results = _enhance_comparison_results(comparison_results)
    
    return enhanced_results


def _enhance_comparison_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance the comparison results with additional insights and categorized recommendations.
    """
    enhanced = results.copy()
    
    # Categorize recommendations by type
    recommendations_by_category = {
        'critical': [],      # Issues that prevent compliance
        'important': [],     # Issues that impact functionality
        'style': [],         # Naming and formatting issues
        'optimization': []   # Performance and best practice improvements
    }
    
    # New categorization by issue type
    recommendations_by_type = {
        'node_renames': [],           # Node label changes
        'relationship_renames': [],   # Relationship type changes  
        'property_renames': [],       # Property name changes
        'missing_indexes': [],        # Missing indexes
        'data_type_mismatches': []    # Wrong property data types
    }
    
    # Analyze node matches for categorized recommendations
    for node_match in results.get('node_matches', []):
        if node_match.target_node is None:
            # Unmatched node - critical issue
            recommendations_by_category['critical'].append({
                'type': 'unmatched_node',
                'message': f"Node '{node_match.source_node.label}' does not match any standard node",
                'suggestion': "Consider removing or mapping to a standard node type"
            })
        else:
            # Analyze label match
            if node_match.label_match:
                _categorize_field_recommendations(
                    node_match.label_match, 'node_label', recommendations_by_category
                )
                
                # Add to type-based categorization
                if node_match.label_match.match_type != MatchType.EXACT:
                    recommendations_by_type['node_renames'].append({
                        'current_label': node_match.source_node.label,
                        'standard_label': node_match.target_node.label,
                        'match_type': node_match.label_match.match_type,
                        'similarity_score': node_match.label_match.similarity_result.score,
                        'priority': _get_priority_from_match_type(node_match.label_match.match_type),
                        'cypher_command': f"MATCH (n:{node_match.source_node.label}) SET n:{node_match.target_node.label} REMOVE n:{node_match.source_node.label}"
                    })
            
            # Analyze missing properties
            for missing_prop in node_match.missing_properties:
                if missing_prop.mandatory:
                    recommendations_by_category['critical'].append({
                        'type': 'missing_mandatory_property',
                        'message': f"Node '{node_match.source_node.label}' missing mandatory property '{missing_prop.property}'",
                        'suggestion': f"Add property '{missing_prop.property}' of type {missing_prop.type}"
                    })
                else:
                    recommendations_by_category['important'].append({
                        'type': 'missing_optional_property',
                        'message': f"Node '{node_match.source_node.label}' missing optional property '{missing_prop.property}'",
                        'suggestion': f"Consider adding property '{missing_prop.property}' for completeness"
                    })
            
            # Analyze property matches
            for prop_match in node_match.property_matches:
                _categorize_field_recommendations(
                    prop_match, 'node_property', recommendations_by_category
                )
                
                # Check for property renames
                if prop_match.match_type != MatchType.EXACT and 'rename' in ' '.join(prop_match.recommendations).lower():
                    recommendations_by_type['property_renames'].append({
                        'element_type': 'Node',
                        'element_name': node_match.source_node.label,
                        'current_property': prop_match.source_field,
                        'standard_property': prop_match.target_field,
                        'similarity_score': prop_match.similarity_result.score,
                        'priority': _get_priority_from_match_type(prop_match.match_type)
                    })
                
                # Check for data type mismatches
                if 'type mismatch' in ' '.join(prop_match.recommendations).lower():
                    # Find the property definitions to get type info
                    source_prop = next((p for p in node_match.source_node.properties if p.property == prop_match.source_field), None)
                    target_prop = next((p for p in node_match.target_node.properties if p.property == prop_match.target_field), None)
                    
                    recommendations_by_type['data_type_mismatches'].append({
                        'element_type': 'Node',
                        'element_property': f"{node_match.source_node.label}.{prop_match.source_field}",
                        'current_types': source_prop.type if source_prop else ['unknown'],
                        'expected_types': target_prop.type if target_prop else ['unknown'],
                        'priority': 'HIGH'
                    })
            
            # Check for missing indexes
            if node_match.target_node.indexes:
                source_index_keys = {f"{idx.type}:{':'.join(sorted(idx.properties))}" for idx in node_match.source_node.indexes}
                for target_index in node_match.target_node.indexes:
                    target_key = f"{target_index.type}:{':'.join(sorted(target_index.properties))}"
                    if target_key not in source_index_keys:
                        cypher_cmd = _generate_index_cypher(node_match.target_node.label, target_index)
                        recommendations_by_type['missing_indexes'].append({
                            'element_label': node_match.source_node.label,
                            'index_type': target_index.type,
                            'properties': target_index.properties,
                            'priority': 'MEDIUM',
                            'cypher_command': cypher_cmd
                        })
    
    # Analyze relationship matches
    for rel_match in results.get('relationship_matches', []):
        if rel_match.target_relationship is None:
            recommendations_by_category['critical'].append({
                'type': 'unmatched_relationship',
                'message': f"Relationship '{rel_match.source_relationship.type}' does not match any standard relationship",
                'suggestion': "Consider removing or mapping to a standard relationship type"
            })
        else:
            if rel_match.type_match:
                _categorize_field_recommendations(
                    rel_match.type_match, 'relationship_type', recommendations_by_category
                )
                
                # Add to type-based categorization
                if rel_match.type_match.match_type != MatchType.EXACT:
                    recommendations_by_type['relationship_renames'].append({
                        'current_type': rel_match.source_relationship.type,
                        'standard_type': rel_match.target_relationship.type,
                        'match_type': rel_match.type_match.match_type,
                        'similarity_score': rel_match.type_match.similarity_result.score,
                        'priority': _get_priority_from_match_type(rel_match.type_match.match_type),
                        'cypher_command': _generate_relationship_rename_cypher(
                            rel_match.source_relationship.type,
                            rel_match.target_relationship.type
                        )
                    })
            
            for prop_match in rel_match.property_matches:
                _categorize_field_recommendations(
                    prop_match, 'relationship_property', recommendations_by_category
                )
                
                # Check for property renames
                if prop_match.match_type != MatchType.EXACT and 'rename' in ' '.join(prop_match.recommendations).lower():
                    recommendations_by_type['property_renames'].append({
                        'element_type': 'Relationship',
                        'element_name': rel_match.source_relationship.type,
                        'current_property': prop_match.source_field,
                        'standard_property': prop_match.target_field,
                        'similarity_score': prop_match.similarity_result.score,
                        'priority': _get_priority_from_match_type(prop_match.match_type)
                    })
                
                # Check for data type mismatches
                if 'type mismatch' in ' '.join(prop_match.recommendations).lower():
                    # Find the property definitions to get type info
                    source_prop = next((p for p in rel_match.source_relationship.properties if p.property == prop_match.source_field), None)
                    target_prop = next((p for p in rel_match.target_relationship.properties if p.property == prop_match.target_field), None)
                    
                    recommendations_by_type['data_type_mismatches'].append({
                        'element_type': 'Relationship',
                        'element_property': f"{rel_match.source_relationship.type}.{prop_match.source_field}",
                        'current_types': source_prop.type if source_prop else ['unknown'],
                        'expected_types': target_prop.type if target_prop else ['unknown'],
                        'priority': 'HIGH'
                    })
    
    # Add categorized recommendations to results
    enhanced['categorized_recommendations'] = recommendations_by_category
    enhanced['recommendations_by_type'] = recommendations_by_type
    
    # Add priority scores
    enhanced['priority_scores'] = {
        'critical_issues': len(recommendations_by_category['critical']),
        'important_issues': len(recommendations_by_category['important']),
        'style_issues': len(recommendations_by_category['style']),
        'optimization_opportunities': len(recommendations_by_category['optimization'])
    }
    
    # Calculate compliance level
    compliance_level = _calculate_compliance_level(
        enhanced['summary']['overall_compliance_score'],
        recommendations_by_category
    )
    enhanced['compliance_level'] = compliance_level
    
    return enhanced


def _categorize_field_recommendations(field_match, field_type: str, 
                                    categories: Dict[str, list]) -> None:
    """Categorize field match recommendations by severity."""
    if field_match.match_type == MatchType.EXACT:
        return  # No recommendations needed for exact matches
    
    for recommendation in field_match.recommendations:
        if 'case sensitivity' in recommendation.lower():
            categories['style'].append({
                'type': f'{field_type}_case_sensitivity',
                'message': recommendation,
                'suggestion': 'Update naming to match standard case conventions'
            })
        elif 'type mismatch' in recommendation.lower():
            categories['critical'].append({
                'type': f'{field_type}_type_mismatch',
                'message': recommendation,
                'suggestion': 'Update property type to match standard'
            })
        elif 'mandatory' in recommendation.lower():
            categories['critical'].append({
                'type': f'{field_type}_mandatory_mismatch',
                'message': recommendation,
                'suggestion': 'Make property mandatory as per standard'
            })
        else:
            # General naming recommendations
            if field_match.similarity_result.score >= 0.8:
                categories['style'].append({
                    'type': f'{field_type}_naming',
                    'message': recommendation,
                    'suggestion': 'Consider renaming for better clarity'
                })
            else:
                categories['important'].append({
                    'type': f'{field_type}_naming',
                    'message': recommendation,
                    'suggestion': 'Rename to match standard for compliance'
                })


def _calculate_compliance_level(compliance_score: float, 
                              recommendations: Dict[str, list]) -> str:
    """Calculate overall compliance level based on score and recommendation severity."""
    critical_count = len(recommendations['critical'])
    important_count = len(recommendations['important'])
    
    if critical_count == 0 and compliance_score >= 0.95:
        return 'excellent'
    elif critical_count == 0 and compliance_score >= 0.85:
        return 'good'
    elif critical_count <= 2 and compliance_score >= 0.70:
        return 'fair'
    elif critical_count <= 5 and compliance_score >= 0.50:
        return 'poor'
    else:
        return 'critical'


def _get_priority_from_match_type(match_type: MatchType) -> str:
    """Convert MatchType to priority string."""
    if match_type == MatchType.EXACT:
        return 'LOW'
    elif match_type == MatchType.STRONG:
        return 'MEDIUM'
    elif match_type == MatchType.MODERATE:
        return 'HIGH'
    else:
        return 'CRITICAL'


def _generate_index_cypher(label: str, index_info) -> str:
    """Generate Cypher command for creating an index."""
    if index_info.type == 'BTREE':
        props = ', '.join(f'n.{prop}' for prop in index_info.properties)
        return f"CREATE INDEX FOR (n:{label}) ON ({props})"
    elif index_info.type == 'FULLTEXT':
        props = ', '.join(f'n.{prop}' for prop in index_info.properties)
        return f"CREATE FULLTEXT INDEX FOR (n:{label}) ON EACH [{props}]"
    else:
        return f"// Create {index_info.type} index for {label}({', '.join(index_info.properties)})"


def _generate_relationship_rename_cypher(old_type: str, new_type: str) -> str:
    """Generate Cypher command for renaming a relationship type."""
    return f"""// Rename relationship type from {old_type} to {new_type}
MATCH (a)-[r:{old_type}]->(b)
CREATE (a)-[r2:{new_type}]->(b)
SET r2 = properties(r)
DELETE r"""


def get_similarity_engine_info() -> Dict[str, Any]:
    """
    Get information about the available similarity techniques and their capabilities.
    
    Returns:
        Dictionary with details about similarity engine capabilities
    """
    return {
        'techniques': {
            'levenshtein': {
                'description': 'Edit distance similarity, good for typos and minor variations',
                'best_for': ['exact matches', 'typo detection', 'short strings']
            },
            'jaro_winkler': {
                'description': 'String similarity with prefix bias, excellent for abbreviations',
                'best_for': ['abbreviations', 'common prefixes', 'partial matches']
            },
            'fuzzy': {
                'description': 'Multiple fuzzy matching algorithms including token-based',
                'best_for': ['general purpose', 'word reordering', 'partial matches']
            },
            'abbreviation': {
                'description': 'Specialized abbreviation expansion and matching',
                'best_for': ['CUSTNUM -> customer_number', 'database abbreviations']
            },
            'semantic': {
                'description': 'Meaning-based similarity using embeddings',
                'best_for': ['conceptually similar terms', 'synonyms', 'context understanding']
            },
            'contextual': {
                'description': 'Domain-specific similarity using financial/database knowledge',
                'best_for': ['banking terms', 'database patterns', 'field types']
            }
        },
        'composition': {
            'adaptive': 'Automatically adjusts technique weights based on string characteristics',
            'composite': 'Combines all techniques with configurable weights',
            'default_threshold': 0.7
        }
    }
