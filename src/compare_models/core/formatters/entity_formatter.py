"""
Entity-centric formatter for schema comparison results.

This formatter reorganizes the comparison output to group all information
about each entity (node or relationship) together, making it easier to
understand the complete context of each match.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from ...common.models import Node, Relationship, PropertyDefinition
from ..similarity import FieldMatch, NodeMatch, RelationshipMatch, MatchType


@dataclass
class EntityReport:
    """Represents a complete report for a single entity (node or relationship)."""
    entity_type: str  # 'node' or 'relationship'
    source_name: str
    target_name: Optional[str]
    match_score: float
    match_type: MatchType
    similarity_details: Dict[str, float]
    property_matches: List[Dict[str, Any]]
    missing_properties: List[PropertyDefinition]
    extra_properties: List[PropertyDefinition]
    validation_issues: List[str]
    confidence: float
    recommendations: List[str]


class EntityCentricFormatter:
    """
    Formats schema comparison results in an entity-centric way.
    
    Instead of separating nodes, relationships, and properties into different
    sections, this formatter groups all information about each entity together.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the formatter.
        
        Args:
            verbose: Whether to include detailed matching information
        """
        self.verbose = verbose
    
    def format_comparison_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform comparison results into entity-centric format.
        
        Args:
            results: Raw comparison results from the comparator
            
        Returns:
            Reformatted results organized by entity
        """
        formatted = {
            'entities': {
                'nodes': [],
                'relationships': []
            },
            'summary': results.get('summary', {}),
            'statistics': self._generate_statistics(results),
            'unmatched_summary': self._generate_unmatched_summary(results)
        }
        
        # Process node matches
        for node_match in results.get('node_matches', []):
            entity_report = self._process_node_match(node_match)
            formatted['entities']['nodes'].append(entity_report)
        
        # Process relationship matches
        for rel_match in results.get('relationship_matches', []):
            entity_report = self._process_relationship_match(rel_match)
            formatted['entities']['relationships'].append(entity_report)
        
        return formatted
    
    def _process_node_match(self, node_match: NodeMatch) -> Dict[str, Any]:
        """Process a single node match into an entity report."""
        source_node = node_match.source_node
        target_node = node_match.target_node
        
        report = {
            'entity_type': 'node',
            'source': {
                'label': source_node.label,
                'property_count': len(source_node.properties),
                'properties': [p.property for p in source_node.properties]
            }
        }
        
        if target_node:
            # We have a match
            report['match'] = {
                'label': target_node.label,
                'score': node_match.label_match.similarity_result.score if node_match.label_match else 0.0,
                'type': node_match.label_match.match_type.value if node_match.label_match else 'no_match',
                'confidence': node_match.overall_confidence
            }
            
            # Add similarity details if verbose
            if self.verbose and node_match.label_match:
                report['match']['similarity_breakdown'] = self._extract_similarity_breakdown(
                    node_match.label_match
                )
            
            # Process property matches
            report['properties'] = {
                'matches': [],
                'missing': [],
                'extra': []
            }
            
            for prop_match in node_match.property_matches:
                prop_info = {
                    'source': prop_match.source_field,
                    'target': prop_match.target_field,
                    'score': prop_match.similarity_result.score,
                    'type': prop_match.match_type.value,
                    'recommendations': prop_match.recommendations
                }
                
                if self.verbose:
                    prop_info['techniques'] = self._extract_similarity_breakdown(prop_match)
                
                report['properties']['matches'].append(prop_info)
            
            # Missing properties (in standard but not in source)
            for missing_prop in node_match.missing_properties:
                report['properties']['missing'].append({
                    'name': missing_prop.property,
                    'type': missing_prop.type,
                    'mandatory': missing_prop.mandatory
                })
            
            # Extra properties (in source but not in standard)
            for extra_prop in node_match.extra_properties:
                report['properties']['extra'].append({
                    'name': extra_prop.property,
                    'type': extra_prop.type
                })
            
            # Validation checks
            report['validation'] = self._validate_node_match(node_match)
            
        else:
            # No match found
            report['match'] = None
            report['recommendations'] = [
                f"Node '{source_node.label}' has no match in the standard schema",
                "Consider reviewing if this node is necessary or should be mapped to a standard node"
            ]
        
        return report
    
    def _process_relationship_match(self, rel_match: RelationshipMatch) -> Dict[str, Any]:
        """Process a single relationship match into an entity report."""
        source_rel = rel_match.source_relationship
        target_rel = rel_match.target_relationship
        
        report = {
            'entity_type': 'relationship',
            'source': {
                'type': source_rel.type,
                'property_count': len(source_rel.properties),
                'properties': [p.property for p in source_rel.properties],
                'paths': [p.path for p in source_rel.paths]
            }
        }
        
        if target_rel:
            # We have a match
            report['match'] = {
                'type': target_rel.type,
                'score': rel_match.type_match.similarity_result.score if rel_match.type_match else 0.0,
                'match_type': rel_match.type_match.match_type.value if rel_match.type_match else 'no_match',
                'confidence': rel_match.overall_confidence
            }
            
            # Add similarity details if verbose
            if self.verbose and rel_match.type_match:
                report['match']['similarity_breakdown'] = self._extract_similarity_breakdown(
                    rel_match.type_match
                )
            
            # Process property matches
            report['properties'] = {
                'matches': [],
                'missing': [],
                'extra': []
            }
            
            for prop_match in rel_match.property_matches:
                prop_info = {
                    'source': prop_match.source_field,
                    'target': prop_match.target_field,
                    'score': prop_match.similarity_result.score,
                    'type': prop_match.match_type.value,
                    'recommendations': prop_match.recommendations
                }
                
                if self.verbose:
                    prop_info['techniques'] = self._extract_similarity_breakdown(prop_match)
                
                report['properties']['matches'].append(prop_info)
            
            # Missing and extra properties
            for missing_prop in rel_match.missing_properties:
                report['properties']['missing'].append({
                    'name': missing_prop.property,
                    'type': missing_prop.type,
                    'mandatory': missing_prop.mandatory
                })
            
            for extra_prop in rel_match.extra_properties:
                report['properties']['extra'].append({
                    'name': extra_prop.property,
                    'type': extra_prop.type
                })
            
            # Validation checks
            report['validation'] = self._validate_relationship_match(rel_match)
            
        else:
            # No match found
            report['match'] = None
            report['recommendations'] = [
                f"Relationship '{source_rel.type}' has no match in the standard schema",
                "Consider reviewing if this relationship is necessary or should be mapped to a standard type"
            ]
        
        return report
    
    def _extract_similarity_breakdown(self, field_match: FieldMatch) -> Dict[str, Any]:
        """Extract detailed similarity information from a field match."""
        breakdown = {}
        
        # Get metadata from similarity result
        metadata = field_match.similarity_result.metadata or {}
        
        # Extract technique contributions
        if 'technique_scores' in metadata:
            breakdown['techniques'] = metadata['technique_scores']
        else:
            # Fallback to basic info
            breakdown['primary_technique'] = field_match.similarity_result.technique
            breakdown['score'] = field_match.similarity_result.score
        
        # Add any expansion information
        if 'expanded_text1' in metadata:
            breakdown['expansions'] = {
                'source': metadata.get('expanded_text1'),
                'target': metadata.get('expanded_text2')
            }
        
        return breakdown
    
    def _validate_node_match(self, node_match: NodeMatch) -> Dict[str, Any]:
        """Validate a node match for potential issues."""
        validation = {
            'issues': [],
            'warnings': [],
            'property_compatibility': 0.0
        }
        
        if not node_match.target_node:
            return validation
        
        # Check property compatibility
        source_props = {p.property.lower() for p in node_match.source_node.properties}
        target_props = {p.property.lower() for p in node_match.target_node.properties}
        
        if source_props and target_props:
            # Calculate Jaccard similarity of property sets
            intersection = len(source_props & target_props)
            union = len(source_props | target_props)
            validation['property_compatibility'] = intersection / union if union > 0 else 0.0
            
            # Flag if property compatibility is very low
            if validation['property_compatibility'] < 0.2 and node_match.label_match:
                if node_match.label_match.similarity_result.score > 0.7:
                    validation['warnings'].append(
                        f"High label similarity ({node_match.label_match.similarity_result.score:.2f}) "
                        f"but low property compatibility ({validation['property_compatibility']:.2f})"
                    )
        
        # Check for semantic mismatches
        if node_match.label_match and node_match.label_match.similarity_result.technique == 'semantic':
            if node_match.label_match.similarity_result.score < 0.8:
                validation['warnings'].append(
                    "Match based primarily on semantic similarity - verify this is correct"
                )
        
        # Check for missing mandatory properties
        mandatory_missing = [p for p in node_match.missing_properties if p.mandatory]
        if mandatory_missing:
            validation['issues'].append(
                f"Missing {len(mandatory_missing)} mandatory properties: "
                f"{', '.join(p.property for p in mandatory_missing[:3])}"
                f"{'...' if len(mandatory_missing) > 3 else ''}"
            )
        
        return validation
    
    def _validate_relationship_match(self, rel_match: RelationshipMatch) -> Dict[str, Any]:
        """Validate a relationship match for potential issues."""
        validation = {
            'issues': [],
            'warnings': [],
            'path_compatibility': False
        }
        
        if not rel_match.target_relationship:
            return validation
        
        # Check if relationship paths are compatible
        # This is a simplified check - could be enhanced
        source_paths = set(p.path for p in rel_match.source_relationship.paths)
        target_paths = set(p.path for p in rel_match.target_relationship.paths)
        
        # Extract node types from paths (simplified)
        source_nodes = self._extract_nodes_from_paths(source_paths)
        target_nodes = self._extract_nodes_from_paths(target_paths)
        
        if source_nodes and target_nodes:
            # Check if node types are similar
            validation['path_compatibility'] = bool(source_nodes & target_nodes)
            
            if not validation['path_compatibility']:
                validation['warnings'].append(
                    "Relationship connects different node types in source vs standard"
                )
        
        return validation
    
    def _extract_nodes_from_paths(self, paths: set) -> set:
        """Extract node labels from relationship paths."""
        import re
        nodes = set()
        for path in paths:
            # Simple regex to extract node labels from paths like (:Customer)-[:HAS]->(:Account)
            matches = re.findall(r':(\w+)', path)
            nodes.update(matches)
        return nodes
    
    def _generate_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate matching statistics from results."""
        stats = {
            'node_matches': {
                'exact': 0,
                'strong': 0,
                'moderate': 0,
                'weak': 0,
                'no_match': 0
            },
            'relationship_matches': {
                'exact': 0,
                'strong': 0,
                'moderate': 0,
                'weak': 0,
                'no_match': 0
            },
            'technique_usage': {},
            'property_match_rate': 0.0
        }
        
        # Count node matches by type
        for node_match in results.get('node_matches', []):
            if node_match.target_node and node_match.label_match:
                match_type = node_match.label_match.match_type.value
                stats['node_matches'][match_type] = stats['node_matches'].get(match_type, 0) + 1
                
                # Track technique usage
                technique = node_match.label_match.similarity_result.technique
                stats['technique_usage'][technique] = stats['technique_usage'].get(technique, 0) + 1
            else:
                stats['node_matches']['no_match'] += 1
        
        # Count relationship matches by type
        for rel_match in results.get('relationship_matches', []):
            if rel_match.target_relationship and rel_match.type_match:
                match_type = rel_match.type_match.match_type.value
                stats['relationship_matches'][match_type] = stats['relationship_matches'].get(match_type, 0) + 1
                
                # Track technique usage
                technique = rel_match.type_match.similarity_result.technique
                stats['technique_usage'][technique] = stats['technique_usage'].get(technique, 0) + 1
            else:
                stats['relationship_matches']['no_match'] += 1
        
        # Calculate property match rate
        total_properties = 0
        matched_properties = 0
        
        for node_match in results.get('node_matches', []):
            if node_match.source_node:
                total_properties += len(node_match.source_node.properties)
                matched_properties += len(node_match.property_matches)
        
        if total_properties > 0:
            stats['property_match_rate'] = matched_properties / total_properties
        
        return stats
    
    def _generate_unmatched_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of why entities didn't match."""
        unmatched = {
            'nodes': [],
            'relationships': []
        }
        
        # Find unmatched nodes
        for node_match in results.get('node_matches', []):
            if not node_match.target_node:
                unmatched['nodes'].append({
                    'label': node_match.source_node.label,
                    'reason': 'No suitable match found in standard schema',
                    'best_candidate': self._find_best_candidate_info(node_match)
                })
        
        # Find unmatched relationships
        for rel_match in results.get('relationship_matches', []):
            if not rel_match.target_relationship:
                unmatched['relationships'].append({
                    'type': rel_match.source_relationship.type,
                    'reason': 'No suitable match found in standard schema',
                    'best_candidate': self._find_best_candidate_info(rel_match)
                })
        
        return unmatched
    
    def _find_best_candidate_info(self, match) -> Optional[Dict[str, Any]]:
        """Find information about the best candidate that didn't meet the threshold."""
        # This would need access to all candidates, not just the selected match
        # For now, return None - this could be enhanced when we track all candidates
        return None