"""
Similarity engine for comparing Neo4j schema elements.

This module provides various similarity calculation techniques for matching
customer database schemas against standard Neo4j data models.
"""

from .base import SimilarityCalculator, SimilarityResult
from .string_similarity import LevenshteinSimilarity, JaroWinklerSimilarity, FuzzySimilarity, AbbreviationSimilarity
from .semantic_similarity import SemanticSimilarity, ContextualSimilarity
from .composite_similarity import CompositeSimilarity, AdaptiveSimilarity
from .field_matcher import FieldMatcher, FieldMatch, NodeMatch, RelationshipMatch, MatchType

__all__ = [
    'SimilarityCalculator',
    'SimilarityResult', 
    'LevenshteinSimilarity',
    'JaroWinklerSimilarity',
    'FuzzySimilarity',
    'AbbreviationSimilarity',
    'SemanticSimilarity',
    'ContextualSimilarity',
    'CompositeSimilarity',
    'AdaptiveSimilarity',
    'FieldMatcher',
    'FieldMatch',
    'NodeMatch', 
    'RelationshipMatch',
    'MatchType'
]