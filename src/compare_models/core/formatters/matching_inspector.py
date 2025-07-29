"""
Matching inspector for detailed analysis of the matching process.

This module provides transparency into how matches are made, showing
the step-by-step process and which similarity techniques contributed
to each match decision.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from ...common.models import Node, Relationship, PropertyDefinition
from ..similarity import SimilarityResult, MatchType


@dataclass
class MatchingStep:
    """Represents a single step in the matching process."""
    step_number: int
    description: str
    technique: str
    score: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchCandidate:
    """Represents a candidate match with detailed scoring information."""
    target_name: str
    final_score: float
    technique_scores: Dict[str, float]
    match_type: MatchType
    validation_result: Dict[str, Any]
    recommendation: str


@dataclass
class MatchingTrace:
    """Complete trace of a matching decision."""
    source_name: str
    source_type: str  # 'node' or 'relationship'
    candidates: List[MatchCandidate]
    selected_match: Optional[str]
    steps: List[MatchingStep]
    decision_rationale: str


class MatchingInspector:
    """
    Provides detailed inspection of the matching process.
    
    This class tracks and explains how matching decisions are made,
    providing transparency into the similarity calculations and
    selection process.
    """
    
    def __init__(self):
        """Initialize the matching inspector."""
        self.traces: List[MatchingTrace] = []
        self.current_trace: Optional[MatchingTrace] = None
    
    def start_trace(self, source_name: str, source_type: str):
        """Start tracing a new matching process."""
        self.current_trace = MatchingTrace(
            source_name=source_name,
            source_type=source_type,
            candidates=[],
            selected_match=None,
            steps=[],
            decision_rationale=""
        )
    
    def add_step(self, description: str, technique: str, score: float, details: Dict[str, Any] = None):
        """Add a step to the current trace."""
        if self.current_trace:
            step = MatchingStep(
                step_number=len(self.current_trace.steps) + 1,
                description=description,
                technique=technique,
                score=score,
                details=details or {}
            )
            self.current_trace.steps.append(step)
    
    def add_candidate(self, candidate: MatchCandidate):
        """Add a candidate to the current trace."""
        if self.current_trace:
            self.current_trace.candidates.append(candidate)
    
    def complete_trace(self, selected_match: Optional[str], rationale: str):
        """Complete the current trace and add it to the collection."""
        if self.current_trace:
            self.current_trace.selected_match = selected_match
            self.current_trace.decision_rationale = rationale
            self.traces.append(self.current_trace)
            self.current_trace = None
    
    def analyze_similarity_result(self, source: str, target: str, 
                                result: SimilarityResult) -> Dict[str, Any]:
        """
        Analyze a similarity result to extract technique contributions.
        
        Args:
            source: Source field name
            target: Target field name
            result: The similarity result to analyze
            
        Returns:
            Detailed analysis of the similarity calculation
        """
        analysis = {
            'source': source,
            'target': target,
            'final_score': result.score,
            'primary_technique': result.technique,
            'confidence': result.confidence,
            'technique_breakdown': {}
        }
        
        # Extract technique contributions from metadata
        metadata = result.metadata or {}
        
        # Check for technique scores in metadata
        if 'technique_scores' in metadata:
            analysis['technique_breakdown'] = metadata['technique_scores']
        elif 'composite_scores' in metadata:
            # Handle composite similarity metadata format
            for technique, score in metadata['composite_scores'].items():
                analysis['technique_breakdown'][technique] = score
        else:
            # Single technique result
            analysis['technique_breakdown'][result.technique] = result.score
        
        # Add expansion information if available
        if 'expanded_text1' in metadata or 'expanded_text2' in metadata:
            analysis['expansions'] = {
                'source_original': source,
                'source_expanded': metadata.get('expanded_text1', source),
                'target_original': target,
                'target_expanded': metadata.get('expanded_text2', target),
                'expansion_helped': metadata.get('used_expansion', False)
            }
        
        # Add any warnings or special notes
        analysis['notes'] = []
        
        if result.technique == 'semantic' and result.score > 0.7:
            analysis['notes'].append(
                "High semantic similarity - verify this match makes sense in context"
            )
        
        if 'abbreviation' in result.technique and result.score > 0.8:
            analysis['notes'].append(
                f"Strong abbreviation match: '{source}' → '{target}'"
            )
        
        return analysis
    
    def generate_match_explanation(self, source_name: str, target_name: Optional[str],
                                 score: float, match_type: MatchType,
                                 technique_scores: Dict[str, float]) -> str:
        """
        Generate a human-readable explanation of why a match was made.
        
        Args:
            source_name: Name of the source field
            target_name: Name of the target field (None if no match)
            score: Final similarity score
            match_type: Type of match (exact, strong, moderate, etc.)
            technique_scores: Scores from different similarity techniques
            
        Returns:
            Human-readable explanation
        """
        if not target_name:
            return f"No suitable match found for '{source_name}' in the standard schema."
        
        explanation_parts = [
            f"'{source_name}' matched to '{target_name}' with {score:.1%} confidence."
        ]
        
        # Identify the primary contributor
        if technique_scores:
            sorted_techniques = sorted(technique_scores.items(), key=lambda x: x[1], reverse=True)
            primary_technique, primary_score = sorted_techniques[0]
            
            technique_explanations = {
                'abbreviation': f"abbreviation expansion ({source_name} → {target_name})",
                'semantic': "semantic/meaning similarity",
                'fuzzy': "fuzzy string matching",
                'levenshtein': "character-level similarity",
                'jaro_winkler': "string similarity with prefix matching",
                'contextual': "domain-specific knowledge"
            }
            
            explanation = technique_explanations.get(primary_technique, primary_technique)
            explanation_parts.append(f"Primary match reason: {explanation} ({primary_score:.1%})")
            
            # Add secondary contributors if significant
            if len(sorted_techniques) > 1:
                secondary_contributors = [
                    f"{tech} ({score:.1%})" 
                    for tech, score in sorted_techniques[1:3]
                    if score > 0.5
                ]
                if secondary_contributors:
                    explanation_parts.append(
                        f"Also supported by: {', '.join(secondary_contributors)}"
                    )
        
        # Add match type interpretation
        match_interpretations = {
            MatchType.EXACT: "This is an exact match.",
            MatchType.STRONG: "This is a strong match with high confidence.",
            MatchType.MODERATE: "This is a moderate match - manual verification recommended.",
            MatchType.WEAK: "This is a weak match - careful review needed.",
            MatchType.NO_MATCH: "No acceptable match found."
        }
        
        if match_type in match_interpretations:
            explanation_parts.append(match_interpretations[match_type])
        
        return " ".join(explanation_parts)
    
    def validate_match(self, source_entity: Any, target_entity: Any, 
                      entity_type: str) -> Dict[str, Any]:
        """
        Validate a match by checking property compatibility and other factors.
        
        Args:
            source_entity: Source node or relationship
            target_entity: Target node or relationship
            entity_type: 'node' or 'relationship'
            
        Returns:
            Validation results with issues and warnings
        """
        validation = {
            'valid': True,
            'confidence_adjustment': 0.0,
            'issues': [],
            'warnings': [],
            'property_analysis': {}
        }
        
        if entity_type == 'node':
            validation.update(self._validate_node_match(source_entity, target_entity))
        else:
            validation.update(self._validate_relationship_match(source_entity, target_entity))
        
        # Calculate overall validity
        validation['valid'] = len(validation['issues']) == 0
        
        return validation
    
    def _validate_node_match(self, source_node: Node, target_node: Node) -> Dict[str, Any]:
        """Validate a node match."""
        result = {
            'property_analysis': {
                'compatibility_score': 0.0,
                'common_properties': [],
                'type_mismatches': []
            }
        }
        
        # Analyze property compatibility
        source_props = {p.property.lower(): p for p in source_node.properties}
        target_props = {p.property.lower(): p for p in target_node.properties}
        
        # Find common properties
        common_keys = set(source_props.keys()) & set(target_props.keys())
        all_keys = set(source_props.keys()) | set(target_props.keys())
        
        if all_keys:
            result['property_analysis']['compatibility_score'] = len(common_keys) / len(all_keys)
            
            # Check for type compatibility in common properties
            for key in common_keys:
                source_prop = source_props[key]
                target_prop = target_props[key]
                
                result['property_analysis']['common_properties'].append(key)
                
                # Simple type compatibility check
                if source_prop.type != target_prop.type:
                    result['property_analysis']['type_mismatches'].append({
                        'property': key,
                        'source_type': source_prop.type,
                        'target_type': target_prop.type
                    })
        
        # Generate warnings based on analysis
        if result['property_analysis']['compatibility_score'] < 0.2:
            result['warnings'] = result.get('warnings', [])
            result['warnings'].append(
                f"Low property compatibility ({result['property_analysis']['compatibility_score']:.1%}) "
                f"between {source_node.label} and {target_node.label}"
            )
            result['confidence_adjustment'] = -0.2
        
        if result['property_analysis']['type_mismatches']:
            result['issues'] = result.get('issues', [])
            result['issues'].append(
                f"{len(result['property_analysis']['type_mismatches'])} property type mismatches found"
            )
        
        return result
    
    def _validate_relationship_match(self, source_rel: Relationship, 
                                   target_rel: Relationship) -> Dict[str, Any]:
        """Validate a relationship match."""
        result = {
            'path_analysis': {
                'compatible': False,
                'source_paths': [],
                'target_paths': []
            }
        }
        
        # Extract and compare paths
        source_paths = [p.path for p in source_rel.paths]
        target_paths = [p.path for p in target_rel.paths]
        
        result['path_analysis']['source_paths'] = source_paths
        result['path_analysis']['target_paths'] = target_paths
        
        # Simple compatibility check - could be enhanced
        import re
        source_nodes = set()
        target_nodes = set()
        
        for path in source_paths:
            nodes = re.findall(r':(\w+)', path)
            source_nodes.update(nodes)
        
        for path in target_paths:
            nodes = re.findall(r':(\w+)', path)
            target_nodes.update(nodes)
        
        # Check if there's any overlap in node types
        if source_nodes & target_nodes:
            result['path_analysis']['compatible'] = True
        else:
            result['warnings'] = result.get('warnings', [])
            result['warnings'].append(
                f"Relationship {source_rel.type} connects different node types than {target_rel.type}"
            )
        
        return result
    
    def get_trace_summary(self) -> Dict[str, Any]:
        """Get a summary of all matching traces."""
        summary = {
            'total_traces': len(self.traces),
            'successful_matches': 0,
            'failed_matches': 0,
            'technique_usage': {},
            'common_issues': {}
        }
        
        for trace in self.traces:
            if trace.selected_match:
                summary['successful_matches'] += 1
            else:
                summary['failed_matches'] += 1
            
            # Count technique usage
            for step in trace.steps:
                technique = step.technique
                summary['technique_usage'][technique] = summary['technique_usage'].get(technique, 0) + 1
        
        return summary
    
    def export_traces(self, detailed: bool = False) -> List[Dict[str, Any]]:
        """
        Export all traces for analysis or display.
        
        Args:
            detailed: Whether to include all step details
            
        Returns:
            List of trace dictionaries
        """
        exported = []
        
        for trace in self.traces:
            trace_data = {
                'source': trace.source_name,
                'type': trace.source_type,
                'selected_match': trace.selected_match,
                'decision': trace.decision_rationale,
                'candidates': [
                    {
                        'target': c.target_name,
                        'score': c.final_score,
                        'match_type': c.match_type.value,
                        'primary_technique': max(c.technique_scores.items(), 
                                               key=lambda x: x[1])[0] if c.technique_scores else 'unknown'
                    }
                    for c in trace.candidates
                ]
            }
            
            if detailed:
                trace_data['steps'] = [
                    {
                        'step': step.step_number,
                        'description': step.description,
                        'technique': step.technique,
                        'score': step.score,
                        'details': step.details
                    }
                    for step in trace.steps
                ]
            
            exported.append(trace_data)
        
        return exported