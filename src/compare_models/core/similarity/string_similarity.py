"""
String-based similarity calculators.

This module provides similarity calculation techniques that rely on direct
string comparison, such as Levenshtein distance, Jaro-Winkler, and fuzzy matching.
"""

import Levenshtein
from fuzzywuzzy import fuzz
from typing import List, Tuple

from .base import SimilarityCalculator, SimilarityResult, AbbreviationExpander


class LevenshteinSimilarity(SimilarityCalculator):
    """
    Calculates similarity based on Levenshtein distance.
    
    This is good for catching simple misspellings and small differences.
    """
    
    def __init__(self):
        super().__init__("levenshtein")
    
    def calculate(self, text1: str, text2: str) -> SimilarityResult:
        """Calculate similarity using Levenshtein distance ratio."""
        if not text1 or not text2:
            return SimilarityResult(
                score=0.0,
                confidence=1.0,
                technique=self.name,
                metadata={"reason": "empty_string"}
            )
        
        score = Levenshtein.ratio(text1.lower(), text2.lower())
        confidence = 0.9 if score > 0.8 else 0.8
        
        return SimilarityResult(
            score=score,
            confidence=confidence,
            technique=self.name
        )


class JaroWinklerSimilarity(SimilarityCalculator):
    """
    Calculates similarity using the Jaro-Winkler algorithm.
    
    This technique is particularly effective for short strings like person names
    and field names, and it gives more weight to prefixes.
    """
    
    def __init__(self):
        super().__init__("jaro_winkler")
        
    def calculate(self, text1: str, text2: str) -> SimilarityResult:
        """Calculate similarity using Jaro-Winkler."""
        if not text1 or not text2:
            return SimilarityResult(
                score=0.0,
                confidence=1.0,
                technique=self.name,
                metadata={"reason": "empty_string"}
            )
            
        score = Levenshtein.jaro_winkler(text1.lower(), text2.lower())
        confidence = 0.9 if score > 0.9 else 0.8
        
        return SimilarityResult(
            score=score,
            confidence=confidence,
            technique=self.name
        )


class FuzzySimilarity(SimilarityCalculator):
    """
    Calculates similarity using fuzzy string matching from fuzzywuzzy.
    
    This class uses token-based matching which can be very effective for
    matching reordered words or partial matches in longer field names.
    """
    
    def __init__(self):
        super().__init__("fuzzy")
    
    def calculate(self, text1: str, text2: str) -> SimilarityResult:
        """Calculate similarity using fuzzywuzzy's token set ratio."""
        if not text1 or not text2:
            return SimilarityResult(
                score=0.0,
                confidence=1.0,
                technique=self.name,
                metadata={"reason": "empty_string"}
            )
            
        score = fuzz.token_set_ratio(text1.lower(), text2.lower()) / 100.0
        confidence = 0.9 if score > 0.9 else 0.8
        
        return SimilarityResult(
            score=score,
            confidence=confidence,
            technique=self.name
        )


class AbbreviationSimilarity(SimilarityCalculator):
    """
    Specialized similarity calculator that focuses on abbreviation matching.
    
    Specifically designed to handle cases like "CUSTNUM" -> "customer_number".
    """
    
    def __init__(self):
        super().__init__("abbreviation") 
        self.expander = AbbreviationExpander()
    
    def calculate(self, text1: str, text2: str) -> SimilarityResult:
        """Calculate similarity with emphasis on abbreviation expansion."""
        if not text1 or not text2:
            return SimilarityResult(
                score=0.0,
                confidence=1.0,
                technique=self.name,
                metadata={"reason": "empty_string"}
            )
        
        # Get all variations of both texts
        variations1 = self.expander.get_variations(text1)
        variations2 = self.expander.get_variations(text2)
        
        best_score = 0.0
        best_match = None
        
        # Compare all variations against each other
        for var1 in variations1:
            for var2 in variations2:
                # Use Jaro-Winkler for the actual comparison
                score = Levenshtein.jaro_winkler(var1.lower(), var2.lower())
                if score > best_score:
                    best_score = score
                    best_match = (var1, var2)
        
        # High confidence if we found a good match through expansion
        if best_match and best_match != (text1, text2):
            confidence = 0.95 if best_score >= 0.8 else 0.85
        else:
            confidence = 0.7 if best_score >= 0.8 else 0.6
        
        return SimilarityResult(
            score=best_score,
            confidence=confidence,
            technique=self.name,
            metadata={
                "variations1": variations1,
                "variations2": variations2,
                "best_match": best_match,
                "used_expansion": best_match != (text1, text2) if best_match else False
            }
        )
