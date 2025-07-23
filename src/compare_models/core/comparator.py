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
            
            for prop_match in rel_match.property_matches:
                _categorize_field_recommendations(
                    prop_match, 'relationship_property', recommendations_by_category
                )
    
    # Add categorized recommendations to results
    enhanced['categorized_recommendations'] = recommendations_by_category
    
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
