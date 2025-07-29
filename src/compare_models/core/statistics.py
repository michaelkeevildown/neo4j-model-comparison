"""
Statistics collector for schema comparison.

This module tracks and analyzes matching statistics to provide insights
into the effectiveness of different similarity techniques and identify
patterns in schema mismatches.
"""

from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field
from .similarity import MatchType


@dataclass
class MatchingStatistics:
    """Container for comprehensive matching statistics."""
    # Overall counts
    total_nodes_analyzed: int = 0
    total_relationships_analyzed: int = 0
    total_properties_analyzed: int = 0
    
    # Match counts by type
    node_matches_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    relationship_matches_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    property_matches_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Technique usage and effectiveness
    technique_usage: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    technique_success_rate: Dict[str, float] = field(default_factory=dict)
    technique_avg_score: Dict[str, float] = field(default_factory=dict)
    
    # Unmatched entities
    unmatched_nodes: List[Dict[str, Any]] = field(default_factory=list)
    unmatched_relationships: List[Dict[str, Any]] = field(default_factory=list)
    unmatched_properties: List[Dict[str, Any]] = field(default_factory=list)
    
    # Common patterns
    abbreviation_patterns: Dict[str, str] = field(default_factory=dict)
    case_mismatches: List[Tuple[str, str]] = field(default_factory=list)
    naming_convention_issues: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))


class StatisticsCollector:
    """
    Collects and analyzes statistics from schema comparison operations.
    
    This class tracks various metrics to help understand matching patterns,
    identify common issues, and optimize the matching process.
    """
    
    def __init__(self):
        """Initialize the statistics collector."""
        self.stats = MatchingStatistics()
        self._technique_scores: Dict[str, List[float]] = defaultdict(list)
        self._technique_matches: Dict[str, int] = defaultdict(int)
    
    def record_node_match(self, source_label: str, target_label: Optional[str],
                         match_type: MatchType, similarity_score: float,
                         technique: str, metadata: Dict[str, Any] = None):
        """Record statistics for a node match attempt."""
        self.stats.total_nodes_analyzed += 1
        self.stats.node_matches_by_type[match_type.value] += 1
        
        # Track technique usage
        self.stats.technique_usage[technique] += 1
        self._technique_scores[technique].append(similarity_score)
        
        if target_label:
            self._technique_matches[technique] += 1
            
            # Check for common patterns
            self._analyze_naming_pattern(source_label, target_label, 'node')
        else:
            # Record unmatched node
            self.stats.unmatched_nodes.append({
                'label': source_label,
                'best_score': similarity_score,
                'technique': technique,
                'metadata': metadata or {}
            })
    
    def record_relationship_match(self, source_type: str, target_type: Optional[str],
                                match_type: MatchType, similarity_score: float,
                                technique: str, metadata: Dict[str, Any] = None):
        """Record statistics for a relationship match attempt."""
        self.stats.total_relationships_analyzed += 1
        self.stats.relationship_matches_by_type[match_type.value] += 1
        
        # Track technique usage
        self.stats.technique_usage[technique] += 1
        self._technique_scores[technique].append(similarity_score)
        
        if target_type:
            self._technique_matches[technique] += 1
            
            # Check for common patterns
            self._analyze_naming_pattern(source_type, target_type, 'relationship')
        else:
            # Record unmatched relationship
            self.stats.unmatched_relationships.append({
                'type': source_type,
                'best_score': similarity_score,
                'technique': technique,
                'metadata': metadata or {}
            })
    
    def record_property_match(self, source_prop: str, target_prop: Optional[str],
                            match_type: MatchType, similarity_score: float,
                            technique: str, parent_type: str, parent_name: str,
                            metadata: Dict[str, Any] = None):
        """Record statistics for a property match attempt."""
        self.stats.total_properties_analyzed += 1
        self.stats.property_matches_by_type[match_type.value] += 1
        
        # Track technique usage
        self.stats.technique_usage[technique] += 1
        self._technique_scores[technique].append(similarity_score)
        
        if target_prop:
            self._technique_matches[technique] += 1
            
            # Check for common patterns
            self._analyze_naming_pattern(source_prop, target_prop, 'property')
        else:
            # Record unmatched property
            self.stats.unmatched_properties.append({
                'property': source_prop,
                'parent_type': parent_type,
                'parent_name': parent_name,
                'best_score': similarity_score,
                'technique': technique,
                'metadata': metadata or {}
            })
    
    def _analyze_naming_pattern(self, source: str, target: str, element_type: str):
        """Analyze naming patterns to identify common issues."""
        # Check for case-only differences
        if source.lower() == target.lower() and source != target:
            self.stats.case_mismatches.append((source, target))
            
            # Categorize the type of case mismatch
            if element_type == 'node':
                # Nodes should be PascalCase in Neo4j
                if not self._is_pascal_case(target):
                    self.stats.naming_convention_issues['node_not_pascal'].append(source)
            elif element_type == 'relationship':
                # Relationships should be UPPER_CASE in Neo4j
                if not self._is_upper_snake_case(target):
                    self.stats.naming_convention_issues['rel_not_upper'].append(source)
            elif element_type == 'property':
                # Properties should be camelCase in Neo4j
                if not self._is_camel_case(target):
                    self.stats.naming_convention_issues['prop_not_camel'].append(source)
        
        # Detect abbreviation patterns
        if len(source) < len(target) * 0.7:  # Source is significantly shorter
            # Likely an abbreviation
            self.stats.abbreviation_patterns[source] = target
        
        # Check for underscore vs camelCase
        if '_' in source and '_' not in target:
            self.stats.naming_convention_issues['underscore_to_camel'].append(f"{source} → {target}")
        
        # Check for hyphen vs camelCase
        if '-' in source and '-' not in target:
            self.stats.naming_convention_issues['hyphen_to_camel'].append(f"{source} → {target}")
    
    def _is_pascal_case(self, text: str) -> bool:
        """Check if text follows PascalCase convention."""
        return text and text[0].isupper() and not '_' in text and not '-' in text
    
    def _is_camel_case(self, text: str) -> bool:
        """Check if text follows camelCase convention."""
        return text and text[0].islower() and not '_' in text and not '-' in text
    
    def _is_upper_snake_case(self, text: str) -> bool:
        """Check if text follows UPPER_SNAKE_CASE convention."""
        return text.isupper() or (text.replace('_', '').isupper() and '_' in text)
    
    def calculate_technique_effectiveness(self):
        """Calculate effectiveness metrics for each similarity technique."""
        for technique in self.stats.technique_usage:
            # Calculate average score
            if technique in self._technique_scores and self._technique_scores[technique]:
                scores = self._technique_scores[technique]
                self.stats.technique_avg_score[technique] = sum(scores) / len(scores)
            
            # Calculate success rate (matches found / total attempts)
            total_attempts = self.stats.technique_usage[technique]
            successful_matches = self._technique_matches.get(technique, 0)
            
            if total_attempts > 0:
                self.stats.technique_success_rate[technique] = successful_matches / total_attempts
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of collected statistics."""
        # Calculate final metrics
        self.calculate_technique_effectiveness()
        
        # Calculate overall match rates
        total_nodes = self.stats.total_nodes_analyzed
        matched_nodes = total_nodes - len(self.stats.unmatched_nodes)
        node_match_rate = matched_nodes / total_nodes if total_nodes > 0 else 0
        
        total_rels = self.stats.total_relationships_analyzed
        matched_rels = total_rels - len(self.stats.unmatched_relationships)
        rel_match_rate = matched_rels / total_rels if total_rels > 0 else 0
        
        total_props = self.stats.total_properties_analyzed
        matched_props = total_props - len(self.stats.unmatched_properties)
        prop_match_rate = matched_props / total_props if total_props > 0 else 0
        
        return {
            'overview': {
                'total_nodes_analyzed': total_nodes,
                'total_relationships_analyzed': total_rels,
                'total_properties_analyzed': total_props,
                'node_match_rate': node_match_rate,
                'relationship_match_rate': rel_match_rate,
                'property_match_rate': prop_match_rate
            },
            'match_distribution': {
                'nodes': dict(self.stats.node_matches_by_type),
                'relationships': dict(self.stats.relationship_matches_by_type),
                'properties': dict(self.stats.property_matches_by_type)
            },
            'technique_effectiveness': {
                technique: {
                    'usage_count': self.stats.technique_usage[technique],
                    'success_rate': self.stats.technique_success_rate.get(technique, 0),
                    'average_score': self.stats.technique_avg_score.get(technique, 0)
                }
                for technique in self.stats.technique_usage
            },
            'common_issues': {
                'case_mismatches': len(self.stats.case_mismatches),
                'abbreviations_found': len(self.stats.abbreviation_patterns),
                'naming_convention_issues': {
                    k: len(v) for k, v in self.stats.naming_convention_issues.items()
                }
            },
            'unmatched_analysis': self._analyze_unmatched_patterns()
        }
    
    def _analyze_unmatched_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in unmatched entities."""
        analysis = {
            'nodes': {},
            'relationships': {},
            'properties': {}
        }
        
        # Analyze why nodes didn't match
        if self.stats.unmatched_nodes:
            avg_best_score = sum(n['best_score'] for n in self.stats.unmatched_nodes) / len(self.stats.unmatched_nodes)
            analysis['nodes'] = {
                'count': len(self.stats.unmatched_nodes),
                'average_best_score': avg_best_score,
                'common_prefixes': self._find_common_prefixes([n['label'] for n in self.stats.unmatched_nodes]),
                'likely_missing_from_standard': avg_best_score < 0.5
            }
        
        # Similar analysis for relationships and properties
        if self.stats.unmatched_relationships:
            avg_best_score = sum(r['best_score'] for r in self.stats.unmatched_relationships) / len(self.stats.unmatched_relationships)
            analysis['relationships'] = {
                'count': len(self.stats.unmatched_relationships),
                'average_best_score': avg_best_score,
                'types': [r['type'] for r in self.stats.unmatched_relationships]
            }
        
        return analysis
    
    def _find_common_prefixes(self, strings: List[str], min_length: int = 3) -> List[str]:
        """Find common prefixes in a list of strings."""
        if not strings:
            return []
        
        prefix_counts = defaultdict(int)
        
        for s in strings:
            # Check prefixes of different lengths
            for length in range(min_length, min(len(s), 10)):
                prefix = s[:length]
                prefix_counts[prefix] += 1
        
        # Return prefixes that appear in at least 2 strings
        common_prefixes = [
            prefix for prefix, count in prefix_counts.items()
            if count >= 2
        ]
        
        # Sort by frequency and length
        common_prefixes.sort(key=lambda p: (prefix_counts[p], len(p)), reverse=True)
        
        return common_prefixes[:5]  # Top 5 prefixes
    
    def get_recommendations(self) -> List[str]:
        """Generate recommendations based on collected statistics."""
        recommendations = []
        
        # Check technique effectiveness
        for technique, effectiveness in self.stats.technique_success_rate.items():
            if effectiveness < 0.3:
                recommendations.append(
                    f"Consider adjusting weights for '{technique}' technique "
                    f"(current success rate: {effectiveness:.1%})"
                )
        
        # Check for systematic naming issues
        if len(self.stats.case_mismatches) > 5:
            recommendations.append(
                f"Found {len(self.stats.case_mismatches)} case-only mismatches. "
                "Consider adding case-insensitive matching for initial comparison."
            )
        
        if len(self.stats.abbreviation_patterns) > 10:
            recommendations.append(
                f"Detected {len(self.stats.abbreviation_patterns)} abbreviations. "
                "Consider expanding the abbreviation dictionary."
            )
        
        # Check for missing standard elements
        if self.stats.unmatched_nodes:
            node_labels = [n['label'] for n in self.stats.unmatched_nodes[:5]]
            recommendations.append(
                f"Consider adding these nodes to the standard schema: {', '.join(node_labels)}"
            )
        
        return recommendations