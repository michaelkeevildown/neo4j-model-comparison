"""
High-level field matcher that uses the similarity engine for schema comparison.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ...common.models import Node, Relationship, PropertyDefinition, GraphSchema
from .composite_similarity import CompositeSimilarity, AdaptiveSimilarity
from .base import SimilarityResult


class MatchType(Enum):
    """Types of matches that can be found."""
    EXACT = "exact"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NO_MATCH = "no_match"


@dataclass
class FieldMatch:
    """Represents a match between two schema elements."""
    source_field: str
    target_field: str
    match_type: MatchType
    similarity_result: SimilarityResult
    confidence: float
    recommendations: List[str]
    
    def is_acceptable_match(self, min_threshold: float = 0.7) -> bool:
        """Check if this match meets the minimum threshold."""
        return self.similarity_result.score >= min_threshold


@dataclass
class NodeMatch:
    """Represents a match between two nodes."""
    source_node: Node
    target_node: Optional[Node]
    label_match: Optional[FieldMatch]
    property_matches: List[FieldMatch]
    missing_properties: List[PropertyDefinition]
    extra_properties: List[PropertyDefinition]
    overall_confidence: float


@dataclass
class RelationshipMatch:
    """Represents a match between two relationships."""
    source_relationship: Relationship
    target_relationship: Optional[Relationship]
    type_match: Optional[FieldMatch]
    property_matches: List[FieldMatch]
    missing_properties: List[PropertyDefinition]
    extra_properties: List[PropertyDefinition]
    overall_confidence: float


class FieldMatcher:
    """
    High-level field matcher that uses similarity engines to compare schema elements.
    
    This class provides the main interface for comparing customer schemas against
    standard schemas, handling nodes, relationships, and properties.
    """
    
    def __init__(self, use_adaptive: bool = True, similarity_threshold: float = 0.7):
        """
        Initialize the field matcher.
        
        Args:
            use_adaptive: Whether to use adaptive similarity weighting
            similarity_threshold: Minimum similarity score to consider a match
        """
        self.similarity_threshold = similarity_threshold
        
        if use_adaptive:
            self.similarity_engine = AdaptiveSimilarity()
        else:
            self.similarity_engine = CompositeSimilarity()
    
    def match_schemas(self, customer_schema: GraphSchema, 
                     standard_schema: GraphSchema) -> Dict[str, Any]:
        """
        Compare a customer schema against the standard schema.
        
        Args:
            customer_schema: The customer's existing database schema
            standard_schema: The standard Neo4j schema to compare against
            
        Returns:
            Comprehensive comparison results with matches and recommendations
        """
        results = {
            "node_matches": [],
            "relationship_matches": [],
            "summary": {
                "total_customer_nodes": len(customer_schema.nodes),
                "total_standard_nodes": len(standard_schema.nodes),
                "matched_nodes": 0,
                "total_customer_relationships": len(customer_schema.relationships),
                "total_standard_relationships": len(standard_schema.relationships),
                "matched_relationships": 0,
                "overall_compliance_score": 0.0
            },
            "recommendations": []
        }
        
        # Match nodes
        node_matches = self._match_nodes(customer_schema.nodes, standard_schema.nodes)
        results["node_matches"] = node_matches
        results["summary"]["matched_nodes"] = sum(1 for match in node_matches if match.target_node is not None)
        
        # Match relationships
        relationship_matches = self._match_relationships(
            customer_schema.relationships, 
            standard_schema.relationships
        )
        results["relationship_matches"] = relationship_matches
        results["summary"]["matched_relationships"] = sum(
            1 for match in relationship_matches if match.target_relationship is not None
        )
        
        # Calculate overall compliance score
        results["summary"]["overall_compliance_score"] = self._calculate_compliance_score(
            node_matches, relationship_matches
        )
        
        # Generate high-level recommendations
        results["recommendations"] = self._generate_schema_recommendations(
            node_matches, relationship_matches
        )
        
        return results
    
    def _match_nodes(self, customer_nodes: List[Node], 
                    standard_nodes: List[Node]) -> List[NodeMatch]:
        """Match customer nodes against standard nodes."""
        matches = []
        used_standard_nodes = set()
        
        for customer_node in customer_nodes:
            best_match = None
            best_score = 0.0
            
            # Find the best matching standard node
            for standard_node in standard_nodes:
                if standard_node.label in used_standard_nodes:
                    continue
                
                similarity = self.similarity_engine.calculate(
                    customer_node.label, 
                    standard_node.label
                )
                
                if similarity.score > best_score and similarity.score >= self.similarity_threshold:
                    best_score = similarity.score
                    best_match = standard_node
            
            if best_match:
                used_standard_nodes.add(best_match.label)
                
                # Create detailed node match
                node_match = self._create_node_match(customer_node, best_match)
                matches.append(node_match)
            else:
                # No match found
                matches.append(NodeMatch(
                    source_node=customer_node,
                    target_node=None,
                    label_match=None,
                    property_matches=[],
                    missing_properties=[],
                    extra_properties=customer_node.properties,
                    overall_confidence=0.0
                ))
        
        return matches
    
    def _create_node_match(self, customer_node: Node, standard_node: Node) -> NodeMatch:
        """Create a detailed node match with property comparisons."""
        # Match the labels
        label_similarity = self.similarity_engine.calculate(
            customer_node.label, 
            standard_node.label
        )
        
        # Check if it's only a case difference
        is_case_only_diff = customer_node.label.lower() == standard_node.label.lower() and customer_node.label != standard_node.label
        
        # Adjust match type for case-only differences
        match_type = self._classify_match_type(label_similarity.score)
        if is_case_only_diff and match_type == MatchType.EXACT:
            match_type = MatchType.STRONG  # Downgrade to STRONG so it appears in recommendations
        
        label_match = FieldMatch(
            source_field=customer_node.label,
            target_field=standard_node.label,
            match_type=match_type,
            similarity_result=label_similarity,
            confidence=label_similarity.confidence,
            recommendations=self._generate_label_recommendations(
                customer_node.label, standard_node.label, label_similarity
            )
        )
        
        # Match properties
        property_matches, missing_props, extra_props = self._match_properties(
            customer_node.properties, 
            standard_node.properties
        )
        
        # Calculate overall confidence
        overall_confidence = self._calculate_node_confidence(
            label_match, property_matches, missing_props, extra_props
        )
        
        return NodeMatch(
            source_node=customer_node,
            target_node=standard_node,
            label_match=label_match,
            property_matches=property_matches,
            missing_properties=missing_props,
            extra_properties=extra_props,
            overall_confidence=overall_confidence
        )
    
    def _match_relationships(self, customer_rels: List[Relationship], 
                           standard_rels: List[Relationship]) -> List[RelationshipMatch]:
        """Match customer relationships against standard relationships."""
        matches = []
        used_standard_rels = set()
        
        for customer_rel in customer_rels:
            best_match = None
            best_score = 0.0
            
            # Find the best matching standard relationship
            for standard_rel in standard_rels:
                if standard_rel.type in used_standard_rels:
                    continue
                
                similarity = self.similarity_engine.calculate(
                    customer_rel.type, 
                    standard_rel.type
                )
                
                if similarity.score > best_score and similarity.score >= self.similarity_threshold:
                    best_score = similarity.score
                    best_match = standard_rel
            
            if best_match:
                used_standard_rels.add(best_match.type)
                
                # Create detailed relationship match
                rel_match = self._create_relationship_match(customer_rel, best_match)
                matches.append(rel_match)
            else:
                # No match found
                matches.append(RelationshipMatch(
                    source_relationship=customer_rel,
                    target_relationship=None,
                    type_match=None,
                    property_matches=[],
                    missing_properties=[],
                    extra_properties=customer_rel.properties,
                    overall_confidence=0.0
                ))
        
        return matches
    
    def _create_relationship_match(self, customer_rel: Relationship, 
                                 standard_rel: Relationship) -> RelationshipMatch:
        """Create a detailed relationship match with property comparisons."""
        # Match the relationship types
        type_similarity = self.similarity_engine.calculate(
            customer_rel.type, 
            standard_rel.type
        )
        
        # Check if it's only a case difference
        is_case_only_diff = customer_rel.type.lower() == standard_rel.type.lower() and customer_rel.type != standard_rel.type
        
        # Adjust match type for case-only differences
        match_type = self._classify_match_type(type_similarity.score)
        if is_case_only_diff and match_type == MatchType.EXACT:
            match_type = MatchType.STRONG  # Downgrade to STRONG so it appears in recommendations
        
        type_match = FieldMatch(
            source_field=customer_rel.type,
            target_field=standard_rel.type,
            match_type=match_type,
            similarity_result=type_similarity,
            confidence=type_similarity.confidence,
            recommendations=self._generate_relationship_recommendations(
                customer_rel.type, standard_rel.type, type_similarity
            )
        )
        
        # Match properties
        property_matches, missing_props, extra_props = self._match_properties(
            customer_rel.properties, 
            standard_rel.properties
        )
        
        # Calculate overall confidence
        overall_confidence = self._calculate_relationship_confidence(
            type_match, property_matches, missing_props, extra_props
        )
        
        return RelationshipMatch(
            source_relationship=customer_rel,
            target_relationship=standard_rel,
            type_match=type_match,
            property_matches=property_matches,
            missing_properties=missing_props,
            extra_properties=extra_props,
            overall_confidence=overall_confidence
        )
    
    def _match_properties(self, customer_props: List[PropertyDefinition], 
                         standard_props: List[PropertyDefinition]) -> Tuple[List[FieldMatch], List[PropertyDefinition], List[PropertyDefinition]]:
        """Match properties between customer and standard schemas."""
        matches = []
        used_standard_props = set()
        
        # Find matches for customer properties
        for customer_prop in customer_props:
            best_match = None
            best_score = 0.0
            
            for standard_prop in standard_props:
                if standard_prop.property in used_standard_props:
                    continue
                
                similarity = self.similarity_engine.calculate(
                    customer_prop.property, 
                    standard_prop.property
                )
                
                if similarity.score > best_score and similarity.score >= self.similarity_threshold:
                    best_score = similarity.score
                    best_match = standard_prop
            
            if best_match:
                used_standard_props.add(best_match.property)
                
                # Check if it's underscore vs camelCase or case-only difference
                is_underscore_to_camel = self._is_underscore_to_camelcase(customer_prop.property, best_match.property)
                is_case_only_diff = customer_prop.property.lower() == best_match.property.lower() and customer_prop.property != best_match.property
                
                # Adjust match type for formatting differences
                match_type = self._classify_match_type(best_score)
                if (is_underscore_to_camel or is_case_only_diff) and match_type == MatchType.EXACT:
                    match_type = MatchType.STRONG  # Downgrade to STRONG so it appears in recommendations
                
                # Create property match
                prop_match = FieldMatch(
                    source_field=customer_prop.property,
                    target_field=best_match.property,
                    match_type=match_type,
                    similarity_result=self.similarity_engine.calculate(
                        customer_prop.property, best_match.property
                    ),
                    confidence=similarity.confidence,
                    recommendations=self._generate_property_recommendations(
                        customer_prop, best_match, similarity
                    )
                )
                matches.append(prop_match)
        
        # Find missing properties (in standard but not in customer)
        missing_props = [
            prop for prop in standard_props 
            if prop.property not in used_standard_props
        ]
        
        # Find extra properties (in customer but not matched to standard)
        matched_customer_props = {match.source_field for match in matches}
        extra_props = [
            prop for prop in customer_props 
            if prop.property not in matched_customer_props
        ]
        
        return matches, missing_props, extra_props
    
    def _classify_match_type(self, score: float) -> MatchType:
        """Classify the type of match based on similarity score."""
        if score >= 0.95:
            return MatchType.EXACT
        elif score >= 0.85:
            return MatchType.STRONG
        elif score >= 0.70:
            return MatchType.MODERATE
        elif score >= 0.50:
            return MatchType.WEAK
        else:
            return MatchType.NO_MATCH
    
    def _generate_label_recommendations(self, customer_label: str, 
                                      standard_label: str, 
                                      similarity: SimilarityResult) -> List[str]:
        """Generate recommendations for node label improvements."""
        recommendations = []
        
        if similarity.score < 1.0:
            if customer_label.lower() == standard_label.lower():
                recommendations.append(
                    f"Change node label '{customer_label}' to '{standard_label}' (case sensitivity)"
                )
            else:
                recommendations.append(
                    f"Consider renaming node label '{customer_label}' to '{standard_label}' for compliance"
                )
        
        return recommendations
    
    def _generate_relationship_recommendations(self, customer_type: str, 
                                             standard_type: str, 
                                             similarity: SimilarityResult) -> List[str]:
        """Generate recommendations for relationship type improvements."""
        recommendations = []
        
        if similarity.score < 1.0:
            if customer_type.lower() == standard_type.lower():
                recommendations.append(
                    f"Change relationship type '{customer_type}' to '{standard_type}' (case sensitivity)"
                )
            else:
                recommendations.append(
                    f"Consider renaming relationship type '{customer_type}' to '{standard_type}' for compliance"
                )
        
        return recommendations
    
    def _is_underscore_to_camelcase(self, underscore_str: str, camel_str: str) -> bool:
        """Check if two strings represent underscore vs camelCase versions of the same name."""
        # Convert underscore to camelCase
        parts = underscore_str.split('_')
        if len(parts) > 1:
            expected_camel = parts[0] + ''.join(word.capitalize() for word in parts[1:])
            return expected_camel == camel_str
        
        # Also check the reverse (camelCase to underscore)
        import re
        camel_to_underscore = re.sub(r'(?<!^)(?=[A-Z])', '_', camel_str).lower()
        return camel_to_underscore == underscore_str
    
    def _generate_property_recommendations(self, customer_prop: PropertyDefinition, 
                                         standard_prop: PropertyDefinition, 
                                         similarity: SimilarityResult) -> List[str]:
        """Generate recommendations for property improvements."""
        recommendations = []
        
        # Name recommendations
        if similarity.score < 1.0:
            if customer_prop.property.lower() == standard_prop.property.lower():
                recommendations.append(
                    f"Change property name '{customer_prop.property}' to '{standard_prop.property}' (case sensitivity)"
                )
            else:
                recommendations.append(
                    f"Rename property '{customer_prop.property}' to '{standard_prop.property}' to match standard"
                )
        
        # Type recommendations
        if customer_prop.type != standard_prop.type:
            recommendations.append(
                f"Property type mismatch: '{customer_prop.property}' is {customer_prop.type} but should be {standard_prop.type}"
            )
        
        # Mandatory field recommendations
        if not customer_prop.mandatory and standard_prop.mandatory:
            recommendations.append(
                f"Property '{customer_prop.property}' should be mandatory according to the standard"
            )
        
        return recommendations
    
    def _calculate_node_confidence(self, label_match: FieldMatch, 
                                 property_matches: List[FieldMatch],
                                 missing_props: List[PropertyDefinition],
                                 extra_props: List[PropertyDefinition]) -> float:
        """Calculate overall confidence for a node match."""
        if not label_match:
            return 0.0
        
        # Start with label match confidence
        confidence = label_match.confidence * 0.4
        
        # Add property match confidence
        if property_matches:
            avg_prop_confidence = sum(match.confidence for match in property_matches) / len(property_matches)
            confidence += avg_prop_confidence * 0.4
        
        # Penalize for missing required properties
        mandatory_missing = sum(1 for prop in missing_props if prop.mandatory)
        confidence -= mandatory_missing * 0.1
        
        # Small penalty for extra properties (might indicate schema drift)
        confidence -= len(extra_props) * 0.02
        
        return max(0.0, min(1.0, confidence))
    
    def _calculate_relationship_confidence(self, type_match: FieldMatch, 
                                         property_matches: List[FieldMatch],
                                         missing_props: List[PropertyDefinition],
                                         extra_props: List[PropertyDefinition]) -> float:
        """Calculate overall confidence for a relationship match."""
        if not type_match:
            return 0.0
        
        # Similar to node confidence but with different weights
        confidence = type_match.confidence * 0.5
        
        if property_matches:
            avg_prop_confidence = sum(match.confidence for match in property_matches) / len(property_matches)
            confidence += avg_prop_confidence * 0.3
        
        # Relationships tend to have fewer required properties
        mandatory_missing = sum(1 for prop in missing_props if prop.mandatory)
        confidence -= mandatory_missing * 0.05
        
        return max(0.0, min(1.0, confidence))
    
    def _calculate_compliance_score(self, node_matches: List[NodeMatch], 
                                  relationship_matches: List[RelationshipMatch]) -> float:
        """Calculate overall compliance score for the schema."""
        total_elements = len(node_matches) + len(relationship_matches)
        if total_elements == 0:
            return 0.0
        
        total_confidence = 0.0
        
        # Sum node confidences
        for match in node_matches:
            total_confidence += match.overall_confidence
        
        # Sum relationship confidences
        for match in relationship_matches:
            total_confidence += match.overall_confidence
        
        return total_confidence / total_elements
    
    def _generate_schema_recommendations(self, node_matches: List[NodeMatch], 
                                       relationship_matches: List[RelationshipMatch]) -> List[str]:
        """Generate high-level schema recommendations."""
        recommendations = []
        
        # Count unmatched elements
        unmatched_nodes = sum(1 for match in node_matches if match.target_node is None)
        unmatched_rels = sum(1 for match in relationship_matches if match.target_relationship is None)
        
        if unmatched_nodes > 0:
            recommendations.append(
                f"{unmatched_nodes} node(s) in your schema don't match the standard model"
            )
        
        if unmatched_rels > 0:
            recommendations.append(
                f"{unmatched_rels} relationship(s) in your schema don't match the standard model"
            )
        
        # Identify common issues
        case_issues = 0
        for match in node_matches:
            if match.label_match and match.label_match.match_type != MatchType.EXACT:
                if (match.source_node.label.lower() == match.target_node.label.lower() 
                    if match.target_node else False):
                    case_issues += 1
        
        if case_issues > 0:
            recommendations.append(
                f"{case_issues} node label(s) have case sensitivity issues"
            )
        
        return recommendations