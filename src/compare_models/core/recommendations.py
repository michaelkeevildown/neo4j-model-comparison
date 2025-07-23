"""
Recommendation generator for Neo4j schema compliance improvements.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..common.models import GraphSchema, Node, Relationship, PropertyDefinition
from .similarity import NodeMatch, RelationshipMatch, FieldMatch, MatchType


class RecommendationType(Enum):
    """Types of recommendations that can be generated."""
    SCHEMA_MIGRATION = "schema_migration"
    PROPERTY_CHANGE = "property_change"
    CONSTRAINT_ADDITION = "constraint_addition"
    INDEX_ADDITION = "index_addition"
    DATA_TYPE_CHANGE = "data_type_change"
    NAMING_CONVENTION = "naming_convention"
    STRUCTURAL_CHANGE = "structural_change"


class Priority(Enum):
    """Priority levels for recommendations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Recommendation:
    """Represents a specific recommendation for schema improvement."""
    id: str
    type: RecommendationType
    priority: Priority
    title: str
    description: str
    cypher_commands: List[str]
    impact_assessment: str
    estimated_effort: str
    prerequisites: List[str]
    rollback_strategy: str
    affected_elements: List[str]


class RecommendationGenerator:
    """
    Generates specific, actionable recommendations for Neo4j schema compliance.
    
    Provides detailed Cypher commands, impact assessments, and implementation guidance
    for bringing customer schemas into compliance with standards.
    """
    
    def __init__(self):
        self.recommendation_id_counter = 1
    
    def generate_recommendations(self, comparison_results: Dict[str, Any]) -> List[Recommendation]:
        """
        Generate comprehensive recommendations based on schema comparison results.
        
        Args:
            comparison_results: Results from schema comparison including matches and gaps
            
        Returns:
            List of prioritized recommendations with implementation details
        """
        recommendations = []
        
        # Generate node-related recommendations
        node_recommendations = self._generate_node_recommendations(
            comparison_results.get('node_matches', [])
        )
        recommendations.extend(node_recommendations)
        
        # Generate relationship-related recommendations
        rel_recommendations = self._generate_relationship_recommendations(
            comparison_results.get('relationship_matches', [])
        )
        recommendations.extend(rel_recommendations)
        
        # Generate structural recommendations
        structural_recommendations = self._generate_structural_recommendations(
            comparison_results
        )
        recommendations.extend(structural_recommendations)
        
        # Sort by priority and return
        priority_order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
        recommendations.sort(key=lambda r: priority_order[r.priority])
        
        return recommendations
    
    def _generate_node_recommendations(self, node_matches: List[NodeMatch]) -> List[Recommendation]:
        """Generate recommendations for node-related improvements."""
        recommendations = []
        
        for node_match in node_matches:
            if node_match.target_node is None:
                # Unmatched node - suggest removal or mapping
                recommendations.append(self._create_unmatched_node_recommendation(node_match))
            else:
                # Matched node - check for specific improvements
                if node_match.label_match and node_match.label_match.match_type != MatchType.EXACT:
                    recommendations.append(self._create_label_rename_recommendation(node_match))
                
                # Missing properties
                for missing_prop in node_match.missing_properties:
                    recommendations.append(self._create_missing_property_recommendation(
                        node_match, missing_prop
                    ))
                
                # Property type mismatches
                for prop_match in node_match.property_matches:
                    if 'type mismatch' in ' '.join(prop_match.recommendations).lower():
                        recommendations.append(self._create_property_type_recommendation(
                            node_match, prop_match
                        ))
                
                # Missing constraints and indexes
                if node_match.target_node.constraints:
                    missing_constraints = self._find_missing_constraints(
                        node_match.source_node, node_match.target_node
                    )
                    for constraint_info in missing_constraints:
                        recommendations.append(self._create_constraint_recommendation(
                            node_match, constraint_info
                        ))
                
                if node_match.target_node.indexes:
                    missing_indexes = self._find_missing_indexes(
                        node_match.source_node, node_match.target_node
                    )
                    for index_info in missing_indexes:
                        recommendations.append(self._create_index_recommendation(
                            node_match, index_info
                        ))
        
        return recommendations
    
    def _generate_relationship_recommendations(self, rel_matches: List[RelationshipMatch]) -> List[Recommendation]:
        """Generate recommendations for relationship-related improvements."""
        recommendations = []
        
        for rel_match in rel_matches:
            if rel_match.target_relationship is None:
                recommendations.append(self._create_unmatched_relationship_recommendation(rel_match))
            else:
                if rel_match.type_match and rel_match.type_match.match_type != MatchType.EXACT:
                    recommendations.append(self._create_relationship_rename_recommendation(rel_match))
                
                # Missing properties
                for missing_prop in rel_match.missing_properties:
                    recommendations.append(self._create_missing_rel_property_recommendation(
                        rel_match, missing_prop
                    ))
        
        return recommendations
    
    def _generate_structural_recommendations(self, comparison_results: Dict[str, Any]) -> List[Recommendation]:
        """Generate high-level structural recommendations."""
        recommendations = []
        
        summary = comparison_results.get('summary', {})
        compliance_score = summary.get('overall_compliance_score', 0.0)
        
        if compliance_score < 0.5:
            recommendations.append(self._create_comprehensive_migration_recommendation(
                comparison_results
            ))
        
        return recommendations
    
    def _create_unmatched_node_recommendation(self, node_match: NodeMatch) -> Recommendation:
        """Create recommendation for unmatched nodes."""
        node_label = node_match.source_node.label
        
        return Recommendation(
            id=self._get_next_id(),
            type=RecommendationType.STRUCTURAL_CHANGE,
            priority=Priority.HIGH,
            title=f"Review unmatched node: {node_label}",
            description=f"The node '{node_label}' in your schema doesn't correspond to any standard node type. Consider if this node is necessary or if it should be mapped to a standard type.",
            cypher_commands=[
                f"// Review all {node_label} nodes and their usage",
                f"MATCH (n:{node_label}) RETURN n LIMIT 10",
                f"// Count relationships involving {node_label}",
                f"MATCH (n:{node_label})-[r]-() RETURN type(r), count(*) ORDER BY count(*) DESC"
            ],
            impact_assessment="Medium - Affects data model consistency but may not impact functionality",
            estimated_effort="2-4 hours for analysis and decision",
            prerequisites=["Business stakeholder consultation", "Data usage analysis"],
            rollback_strategy="No changes made until decision is final",
            affected_elements=[node_label]
        )
    
    def _create_label_rename_recommendation(self, node_match: NodeMatch) -> Recommendation:
        """Create recommendation for node label renaming."""
        source_label = node_match.source_node.label
        target_label = node_match.target_node.label
        
        # Check if it's just a case change
        is_case_change = source_label.lower() == target_label.lower()
        priority = Priority.MEDIUM if is_case_change else Priority.HIGH
        
        cypher_commands = [
            f"// Rename node label from {source_label} to {target_label}",
            f"MATCH (n:{source_label}) SET n:{target_label}",
            f"MATCH (n:{target_label}) REMOVE n:{source_label}"
        ]
        
        return Recommendation(
            id=self._get_next_id(),
            type=RecommendationType.NAMING_CONVENTION,
            priority=priority,
            title=f"Rename node label: {source_label} → {target_label}",
            description=f"Update node label '{source_label}' to '{target_label}' to match the standard naming convention.",
            cypher_commands=cypher_commands,
            impact_assessment="Low - Naming change only, no data loss" if is_case_change else "Medium - Schema change affects queries",
            estimated_effort="30 minutes - 1 hour",
            prerequisites=["Backup database", "Update application queries"],
            rollback_strategy=f"Rename back from {target_label} to {source_label}",
            affected_elements=[source_label, target_label]
        )
    
    def _create_missing_property_recommendation(self, node_match: NodeMatch, 
                                              missing_prop: PropertyDefinition) -> Recommendation:
        """Create recommendation for missing properties."""
        node_label = node_match.source_node.label
        prop_name = missing_prop.property
        prop_types = ', '.join(missing_prop.type)
        
        priority = Priority.CRITICAL if missing_prop.mandatory else Priority.MEDIUM
        
        cypher_commands = [
            f"// Add missing property {prop_name} to {node_label} nodes"
        ]
        
        if missing_prop.mandatory:
            cypher_commands.extend([
                f"// First, add the property with a default value",
                f"MATCH (n:{node_label}) WHERE n.{prop_name} IS NULL",
                f"SET n.{prop_name} = '' // Replace with appropriate default",
                f"// Consider adding a constraint to enforce the property",
                f"CREATE CONSTRAINT FOR (n:{node_label}) REQUIRE n.{prop_name} IS NOT NULL"
            ])
        else:
            cypher_commands.extend([
                f"// Add optional property as needed",
                f"MATCH (n:{node_label}) WHERE <condition>",
                f"SET n.{prop_name} = <value>"
            ])
        
        return Recommendation(
            id=self._get_next_id(),
            type=RecommendationType.PROPERTY_CHANGE,
            priority=priority,
            title=f"Add missing property: {node_label}.{prop_name}",
            description=f"Add the {'mandatory' if missing_prop.mandatory else 'optional'} property '{prop_name}' (type: {prop_types}) to {node_label} nodes as required by the standard.",
            cypher_commands=cypher_commands,
            impact_assessment="High - Data model change affects compliance" if missing_prop.mandatory else "Medium - Optional property for completeness",
            estimated_effort="1-3 hours depending on data migration needs",
            prerequisites=["Determine appropriate default values", "Plan data migration strategy"],
            rollback_strategy=f"Remove property: MATCH (n:{node_label}) REMOVE n.{prop_name}",
            affected_elements=[f"{node_label}.{prop_name}"]
        )
    
    def _create_property_type_recommendation(self, node_match: NodeMatch, 
                                           prop_match: FieldMatch) -> Recommendation:
        """Create recommendation for property type changes."""
        node_label = node_match.source_node.label
        prop_name = prop_match.source_field
        
        return Recommendation(
            id=self._get_next_id(),
            type=RecommendationType.DATA_TYPE_CHANGE,
            priority=Priority.HIGH,
            title=f"Fix property type: {node_label}.{prop_name}",
            description=f"Property '{prop_name}' has incorrect data type. Update to match standard specification.",
            cypher_commands=[
                f"// Check current property types",
                f"MATCH (n:{node_label}) RETURN DISTINCT type(n.{prop_name}) LIMIT 10",
                f"// Convert property type (example - adjust based on actual types)",
                f"MATCH (n:{node_label}) WHERE n.{prop_name} IS NOT NULL",
                f"SET n.{prop_name} = toString(n.{prop_name}) // Example conversion"
            ],
            impact_assessment="High - Data type changes can affect application compatibility",
            estimated_effort="2-6 hours including testing",
            prerequisites=["Backup database", "Test type conversion logic", "Update application code"],
            rollback_strategy="Restore from backup if conversion fails",
            affected_elements=[f"{node_label}.{prop_name}"]
        )
    
    def _create_constraint_recommendation(self, node_match: NodeMatch, 
                                        constraint_info: Dict[str, Any]) -> Recommendation:
        """Create recommendation for missing constraints."""
        node_label = node_match.source_node.label
        constraint_type = constraint_info['type']
        properties = constraint_info['properties']
        
        prop_list = ', '.join(properties)
        
        if constraint_type == 'UNIQUE':
            cypher_cmd = f"CREATE CONSTRAINT FOR (n:{node_label}) REQUIRE n.{properties[0]} IS UNIQUE"
        elif constraint_type == 'NODE_KEY':
            prop_spec = ', '.join(f'n.{prop}' for prop in properties)
            cypher_cmd = f"CREATE CONSTRAINT FOR (n:{node_label}) REQUIRE ({prop_spec}) IS NODE KEY"
        else:
            cypher_cmd = f"// Create {constraint_type} constraint for {node_label}({prop_list})"
        
        return Recommendation(
            id=self._get_next_id(),
            type=RecommendationType.CONSTRAINT_ADDITION,
            priority=Priority.HIGH,
            title=f"Add {constraint_type} constraint: {node_label}({prop_list})",
            description=f"Add {constraint_type} constraint on {node_label} properties ({prop_list}) as required by the standard.",
            cypher_commands=[
                "// Check for existing data that might violate the constraint",
                f"MATCH (n:{node_label}) WITH n.{properties[0]} as prop, count(*) as cnt WHERE cnt > 1 RETURN prop, cnt",
                cypher_cmd
            ],
            impact_assessment="High - Constraint addition may fail if data violates uniqueness",
            estimated_effort="1-2 hours including data validation",
            prerequisites=["Clean duplicate data if necessary", "Validate constraint compatibility"],
            rollback_strategy=f"DROP CONSTRAINT {constraint_info.get('name', 'constraint_name')}",
            affected_elements=[f"{node_label}.{prop}" for prop in properties]
        )
    
    def _create_index_recommendation(self, node_match: NodeMatch, 
                                   index_info: Dict[str, Any]) -> Recommendation:
        """Create recommendation for missing indexes."""
        node_label = node_match.source_node.label
        index_type = index_info['type']
        properties = index_info['properties']
        
        prop_list = ', '.join(properties)
        
        if index_type == 'PROPERTY':
            cypher_cmd = f"CREATE INDEX FOR (n:{node_label}) ON (n.{properties[0]})"
        elif index_type == 'FULLTEXT':
            prop_spec = ', '.join(f'n.{prop}' for prop in properties)
            cypher_cmd = f"CREATE FULLTEXT INDEX FOR (n:{node_label}) ON EACH [{prop_spec}]"
        else:
            cypher_cmd = f"// Create {index_type} index for {node_label}({prop_list})"
        
        return Recommendation(
            id=self._get_next_id(),
            type=RecommendationType.INDEX_ADDITION,
            priority=Priority.MEDIUM,
            title=f"Add {index_type} index: {node_label}({prop_list})",
            description=f"Add {index_type} index on {node_label} properties ({prop_list}) to improve query performance.",
            cypher_commands=[cypher_cmd],
            impact_assessment="Low - Performance improvement, no data changes",
            estimated_effort="15-30 minutes",
            prerequisites=["Monitor query performance before/after"],
            rollback_strategy=f"DROP INDEX {index_info.get('name', 'index_name')}",
            affected_elements=[f"{node_label}.{prop}" for prop in properties]
        )
    
    def _create_unmatched_relationship_recommendation(self, rel_match: RelationshipMatch) -> Recommendation:
        """Create recommendation for unmatched relationships."""
        rel_type = rel_match.source_relationship.type
        
        return Recommendation(
            id=self._get_next_id(),
            type=RecommendationType.STRUCTURAL_CHANGE,
            priority=Priority.MEDIUM,
            title=f"Review unmatched relationship: {rel_type}",
            description=f"The relationship type '{rel_type}' doesn't correspond to any standard relationship. Consider if this relationship is necessary.",
            cypher_commands=[
                f"// Review {rel_type} relationship usage",
                f"MATCH ()-[r:{rel_type}]-() RETURN count(r) as relationship_count",
                f"MATCH (a)-[r:{rel_type}]->(b) RETURN labels(a), labels(b), count(*) LIMIT 10"
            ],
            impact_assessment="Medium - May affect data model semantics",
            estimated_effort="1-2 hours for analysis",
            prerequisites=["Business stakeholder consultation"],
            rollback_strategy="No changes until decision is made",
            affected_elements=[rel_type]
        )
    
    def _create_relationship_rename_recommendation(self, rel_match: RelationshipMatch) -> Recommendation:
        """Create recommendation for relationship renaming."""
        source_type = rel_match.source_relationship.type
        target_type = rel_match.target_relationship.type
        
        return Recommendation(
            id=self._get_next_id(),
            type=RecommendationType.NAMING_CONVENTION,
            priority=Priority.MEDIUM,
            title=f"Rename relationship: {source_type} → {target_type}",
            description=f"Update relationship type '{source_type}' to '{target_type}' to match standard naming.",
            cypher_commands=[
                f"// Rename relationship type from {source_type} to {target_type}",
                f"MATCH ()-[r:{source_type}]-() CREATE (startNode(r))-[r2:{target_type}]->(endNode(r))",
                f"SET r2 = properties(r)",
                f"DELETE r"
            ],
            impact_assessment="Medium - Relationship type change affects queries",
            estimated_effort="1-2 hours",
            prerequisites=["Update application queries", "Test relationship functionality"],
            rollback_strategy=f"Rename back from {target_type} to {source_type}",
            affected_elements=[source_type, target_type]
        )
    
    def _create_missing_rel_property_recommendation(self, rel_match: RelationshipMatch, 
                                                  missing_prop: PropertyDefinition) -> Recommendation:
        """Create recommendation for missing relationship properties."""
        rel_type = rel_match.source_relationship.type
        prop_name = missing_prop.property
        
        return Recommendation(
            id=self._get_next_id(),
            type=RecommendationType.PROPERTY_CHANGE,
            priority=Priority.MEDIUM,
            title=f"Add missing relationship property: {rel_type}.{prop_name}",
            description=f"Add property '{prop_name}' to {rel_type} relationships as required by the standard.",
            cypher_commands=[
                f"// Add property {prop_name} to {rel_type} relationships",
                f"MATCH ()-[r:{rel_type}]-() WHERE r.{prop_name} IS NULL",
                f"SET r.{prop_name} = '' // Set appropriate default value"
            ],
            impact_assessment="Medium - Relationship property change",
            estimated_effort="1-2 hours",
            prerequisites=["Determine appropriate default values"],
            rollback_strategy=f"MATCH ()-[r:{rel_type}]-() REMOVE r.{prop_name}",
            affected_elements=[f"{rel_type}.{prop_name}"]
        )
    
    def _create_comprehensive_migration_recommendation(self, comparison_results: Dict[str, Any]) -> Recommendation:
        """Create recommendation for comprehensive schema migration."""
        compliance_score = comparison_results.get('summary', {}).get('overall_compliance_score', 0.0)
        
        return Recommendation(
            id=self._get_next_id(),
            type=RecommendationType.SCHEMA_MIGRATION,
            priority=Priority.CRITICAL,
            title="Comprehensive Schema Migration Required",
            description=f"Your schema has a low compliance score ({compliance_score:.1%}). Consider a comprehensive migration to align with the standard.",
            cypher_commands=[
                "// This requires a comprehensive migration strategy",
                "// 1. Create migration plan",
                "// 2. Implement changes incrementally", 
                "// 3. Validate at each step",
                "// Contact Neo4j professional services for assistance"
            ],
            impact_assessment="Critical - Major schema restructuring required",
            estimated_effort="2-4 weeks depending on complexity",
            prerequisites=["Complete data backup", "Professional consultation", "Staging environment"],
            rollback_strategy="Restore from backup - full migration rollback",
            affected_elements=["entire_schema"]
        )
    
    def _find_missing_constraints(self, source_node: Node, target_node: Node) -> List[Dict[str, Any]]:
        """Find constraints that exist in target but not in source."""
        source_constraints = {self._constraint_key(c): c for c in source_node.constraints}
        missing = []
        
        for target_constraint in target_node.constraints:
            key = self._constraint_key(target_constraint)
            if key not in source_constraints:
                missing.append({
                    'type': target_constraint.type,
                    'properties': target_constraint.properties,
                    'name': target_constraint.name
                })
        
        return missing
    
    def _find_missing_indexes(self, source_node: Node, target_node: Node) -> List[Dict[str, Any]]:
        """Find indexes that exist in target but not in source."""
        source_indexes = {self._index_key(i): i for i in source_node.indexes}
        missing = []
        
        for target_index in target_node.indexes:
            key = self._index_key(target_index)
            if key not in source_indexes:
                missing.append({
                    'type': target_index.type,
                    'properties': target_index.properties,
                    'name': target_index.name
                })
        
        return missing
    
    def _constraint_key(self, constraint) -> str:
        """Generate unique key for constraint comparison."""
        return f"{constraint.type}:{':'.join(sorted(constraint.properties))}"
    
    def _index_key(self, index) -> str:
        """Generate unique key for index comparison."""
        return f"{index.type}:{':'.join(sorted(index.properties))}"
    
    def _get_next_id(self) -> str:
        """Get next recommendation ID."""
        rec_id = f"REC-{self.recommendation_id_counter:04d}"
        self.recommendation_id_counter += 1
        return rec_id