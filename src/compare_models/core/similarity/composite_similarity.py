"""
Composite similarity calculator that combines multiple techniques.
"""

from typing import List, Dict, Any, Optional
from .base import SimilarityCalculator, SimilarityResult
from .string_similarity import (
    LevenshteinSimilarity, 
    JaroWinklerSimilarity, 
    FuzzySimilarity,
    AbbreviationSimilarity
)
from .semantic_similarity import SemanticSimilarity, ContextualSimilarity


class CompositeSimilarity(SimilarityCalculator):
    """
    Composite similarity calculator that combines multiple techniques with configurable weights.
    
    This is the main entry point for similarity calculations, intelligently combining
    string-based, semantic, and contextual similarity techniques to achieve high
    accuracy in matching field names.
    """
    
    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        super().__init__("composite")
        
        # Default weights - can be adjusted based on testing and domain requirements
        self.default_weights = {
            'levenshtein': 0.10,      # Good for exact matches and typos
            'jaro_winkler': 0.15,     # Great for abbreviations with common prefixes
            'fuzzy': 0.30,            # Strong general-purpose string matching
            'abbreviation': 0.35,     # Specialized for abbreviation expansion
            'semantic': 0.05,         # Semantic understanding via embeddings
            'contextual': 0.05        # Domain-specific knowledge
        }
        
        # Use custom weights if provided
        self.weights = custom_weights or self.default_weights
        
        # Initialize all similarity calculators
        self.calculators = {
            'levenshtein': LevenshteinSimilarity(),
            'jaro_winkler': JaroWinklerSimilarity(),
            'fuzzy': FuzzySimilarity(),
            'abbreviation': AbbreviationSimilarity(),
            'semantic': SemanticSimilarity(),
            'contextual': ContextualSimilarity()
        }
        
        # Ensure weights sum to 1.0
        weight_sum = sum(self.weights.values())
        if abs(weight_sum - 1.0) > 0.01:  # Allow small floating point errors
            # Normalize weights
            self.weights = {k: v / weight_sum for k, v in self.weights.items()}
    
    def calculate(self, text1: str, text2: str, weights: Optional[Dict[str, float]] = None) -> SimilarityResult:
        """
        Calculate composite similarity by combining results from all techniques.
        """
        calc_weights = self.weights if weights is None else weights

        if not text1 or not text2:
            return SimilarityResult(
                score=0.0,
                confidence=1.0,
                technique=self.name,
                metadata={"reason": "empty_string"}
            )
        
        # Collect results from all calculators
        results = {}
        total_weighted_score = 0.0
        total_weighted_confidence = 0.0
        
        for calc_name, calculator in self.calculators.items():
            try:
                result = calculator.calculate(text1, text2)
                results[calc_name] = result
                
                # Add to weighted totals
                weight = calc_weights.get(calc_name, 0.0)
                total_weighted_score += result.score * weight
                total_weighted_confidence += result.confidence * weight
                
            except Exception as e:
                # If a calculator fails, record the error but continue
                results[calc_name] = SimilarityResult(
                    score=0.0,
                    confidence=0.1,
                    technique=calc_name,
                    metadata={"error": str(e)}
                )
        
        # Apply boost for consistent high scores across multiple techniques
        high_score_count = sum(1 for r in results.values() if r.score >= 0.8)
        consistency_boost = min(0.15, high_score_count * 0.05)
        
        final_score = min(1.0, total_weighted_score + consistency_boost)
        final_confidence = min(1.0, total_weighted_confidence)
        
        # Determine the most influential technique
        best_individual_result = max(results.values(), key=lambda r: r.score)
        
        return SimilarityResult(
            score=final_score,
            confidence=final_confidence,
            technique=self.name,
            metadata={
                "individual_results": {name: {
                    "score": result.score,
                    "confidence": result.confidence,
                    "metadata": result.metadata
                } for name, result in results.items()},
                "weights_used": calc_weights,
                "consistency_boost": consistency_boost,
                "high_score_count": high_score_count,
                "best_individual_technique": best_individual_result.technique,
                "best_individual_score": best_individual_result.score
            }
        )
    
    def calculate_with_explanation(self, text1: str, text2: str) -> tuple[SimilarityResult, str]:
        """
        Calculate similarity and provide a human-readable explanation of the result.
        
        Returns:
            Tuple of (SimilarityResult, explanation_string)
        """
        result = self.calculate(text1, text2)
        
        if result.score == 0.0:
            return result, f"No similarity detected between '{text1}' and '{text2}'"
        
        explanation_parts = []
        individual_results = result.metadata.get("individual_results", {})
        
        # Sort by score to highlight the most influential techniques
        sorted_results = sorted(
            individual_results.items(), 
            key=lambda x: x[1]["score"], 
            reverse=True
        )
        
        explanation_parts.append(f"Overall similarity: {result.score:.3f} (confidence: {result.confidence:.3f})")
        explanation_parts.append("\nBreakdown:")
        
        for technique, data in sorted_results:
            score = data["score"]
            weight = self.weights.get(technique, 0.0)
            contribution = score * weight
            
            if score > 0.0:
                explanation_parts.append(
                    f"  • {technique.replace('_', ' ').title()}: {score:.3f} "
                    f"(weight: {weight:.2f}, contribution: {contribution:.3f})"
                )
        
        best_technique = result.metadata.get("best_individual_technique", "")
        if best_technique:
            explanation_parts.append(f"\nBest individual match: {best_technique}")
        
        consistency_boost = result.metadata.get("consistency_boost", 0.0)
        if consistency_boost > 0:
            explanation_parts.append(f"Consistency boost applied: +{consistency_boost:.3f}")
        
        return result, "\n".join(explanation_parts)
    
    def batch_calculate_with_ranking(self, text: str, candidates: List[str], 
                                   threshold: float = 0.5) -> List[tuple[str, SimilarityResult]]:
        """
        Calculate similarity against multiple candidates and return ranked results.
        
        Args:
            text: The text to compare against all candidates
            candidates: List of candidate strings
            threshold: Minimum score to include in results
            
        Returns:
            List of (candidate, SimilarityResult) tuples, sorted by score descending
        """
        results = []
        
        for candidate in candidates:
            result = self.calculate(text, candidate)
            if result.score >= threshold:
                results.append((candidate, result))
        
        # Sort by score descending, then by confidence descending
        results.sort(key=lambda x: (x[1].score, x[1].confidence), reverse=True)
        
        return results
    
    def update_weights(self, new_weights: Dict[str, float]):
        """
        Update the weights used for combining similarity techniques.
        
        Args:
            new_weights: Dictionary mapping technique names to new weights
        """
        # Validate that all technique names are valid
        valid_techniques = set(self.calculators.keys())
        invalid_techniques = set(new_weights.keys()) - valid_techniques
        
        if invalid_techniques:
            raise ValueError(f"Invalid technique names: {invalid_techniques}")
        
        # Update weights and normalize
        self.weights.update(new_weights)
        weight_sum = sum(self.weights.values())
        
        if weight_sum > 0:
            self.weights = {k: v / weight_sum for k, v in self.weights.items()}
        else:
            # Reset to default if all weights are zero
            self.weights = self.default_weights.copy()


class AdaptiveSimilarity(SimilarityCalculator):
    """
    Adaptive similarity calculator that adjusts technique weights based on string characteristics.
    
    Automatically optimizes which techniques to emphasize based on the input strings,
    for example using more string-based techniques for short abbreviations and more
    semantic techniques for longer descriptive field names.
    """
    
    def __init__(self):
        super().__init__("adaptive")
        self.composite = CompositeSimilarity()
    
    def _analyze_string_characteristics(self, text: str) -> Dict[str, Any]:
        """Analyze characteristics of a string to determine optimal technique weights."""
        characteristics = {
            'length': len(text),
            'has_uppercase': any(c.isupper() for c in text),
            'has_lowercase': any(c.islower() for c in text),
            'has_numbers': any(c.isdigit() for c in text),
            'has_underscores': '_' in text,
            'has_camelcase': any(i > 0 and text[i-1].islower() and text[i].isupper() for i in range(1, len(text))),
            'is_abbreviation_like': len(text) <= 8 and text.isupper(),
            'word_count': len(text.replace('_', ' ').split())
        }
        return characteristics
    
    def _compute_adaptive_weights(self, text1: str, text2: str) -> Dict[str, float]:
        """Compute optimal weights based on string characteristics."""
        char1 = self._analyze_string_characteristics(text1)
        char2 = self._analyze_string_characteristics(text2)
        
        # Start with default weights
        weights = self.composite.default_weights.copy()
        
        # Adjust based on characteristics
        avg_length = (char1['length'] + char2['length']) / 2
        
        # For short strings or abbreviations, favor string-based techniques
        if avg_length <= 8 or char1['is_abbreviation_like'] or char2['is_abbreviation_like']:
            weights['abbreviation'] += 0.1
            weights['jaro_winkler'] += 0.05
            weights['semantic'] -= 0.1
            weights['contextual'] -= 0.05
        
        # For longer strings, favor semantic techniques
        elif avg_length > 15:
            weights['semantic'] += 0.1
            weights['contextual'] += 0.05
            weights['levenshtein'] -= 0.1
            weights['abbreviation'] -= 0.05
        
        # If both strings have similar casing patterns, boost fuzzy matching
        if char1['has_camelcase'] and char2['has_camelcase']:
            weights['fuzzy'] += 0.05
            weights['levenshtein'] -= 0.05
        
        # Normalize weights
        weight_sum = sum(weights.values())
        if weight_sum > 0:
            weights = {k: v / weight_sum for k, v in weights.items()}
        
        return weights
    
    def calculate(self, text1: str, text2: str) -> SimilarityResult:
        """Calculate similarity using adaptively weighted techniques."""
        if not text1 or not text2:
            return SimilarityResult(
                score=0.0,
                confidence=1.0,
                technique=self.name,
                metadata={"reason": "empty_string"}
            )
        
        # Compute adaptive weights
        adaptive_weights = self._compute_adaptive_weights(text1, text2)
        
        # Calculate result using the composite engine with temporary weights
        result = self.composite.calculate(text1, text2, weights=adaptive_weights)
        
        # Update metadata to indicate adaptive weighting was used
        result.technique = self.name
        result.metadata["adaptive_weights"] = adaptive_weights
        
        return result