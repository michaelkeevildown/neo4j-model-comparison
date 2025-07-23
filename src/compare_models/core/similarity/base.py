"""
Base classes and interfaces for similarity calculations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
from .abbreviations import NEO4J_ABBREVIATIONS


class SimilarityResult(BaseModel):
    """
    Result of a similarity calculation between two strings.
    """
    score: float  # Similarity score between 0.0 and 1.0
    confidence: float  # Confidence in the match (0.0 to 1.0)
    technique: str  # Name of the technique used
    metadata: Dict[str, Any] = {}  # Additional information about the match
    
    def is_match(self, threshold: float = 0.7) -> bool:
        """Check if this result represents a good match based on the threshold."""
        return self.score >= threshold


class SimilarityCalculator(ABC):
    """
    Abstract base class for all similarity calculation techniques.
    """
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def calculate(self, text1: str, text2: str) -> SimilarityResult:
        """
        Calculate similarity between two strings.
        
        Args:
            text1: First string to compare
            text2: Second string to compare
            
        Returns:
            SimilarityResult with score, confidence, and metadata
        """
        pass
    
    def batch_calculate(self, text: str, candidates: list[str]) -> list[SimilarityResult]:
        """
        Calculate similarity between one text and multiple candidates.
        
        Args:
            text: The text to compare against all candidates
            candidates: List of candidate strings to compare with
            
        Returns:
            List of SimilarityResult objects, one for each candidate
        """
        results = []
        for candidate in candidates:
            result = self.calculate(text, candidate)
            results.append(result)
        return results
    
    def find_best_match(self, text: str, candidates: list[str], 
                       threshold: float = 0.7) -> Optional[SimilarityResult]:
        """
        Find the best matching candidate that meets the threshold.
        
        Args:
            text: The text to find a match for
            candidates: List of candidate strings
            threshold: Minimum similarity score to consider a match
            
        Returns:
            Best SimilarityResult above threshold, or None if no good match
        """
        results = self.batch_calculate(text, candidates)
        
        # Filter results that meet the threshold
        valid_results = [r for r in results if r.is_match(threshold)]
        
        if not valid_results:
            return None
            
        # Return the result with the highest score
        return max(valid_results, key=lambda r: r.score)


class AbbreviationExpander:
    """
    Utility class for expanding common abbreviations used in database field names.
    """
    
    def __init__(self):
        self.ABBREVIATIONS = NEO4J_ABBREVIATIONS
    
    def expand_text(self, text: str) -> str:
        """
        Expand abbreviations in the given text, handling combined words.
        
        Args:
            text: Input text that may contain abbreviations
            
        Returns:
            Text with abbreviations expanded
        """
        # Convert to lowercase and handle delimiters
        import re
        processed_text = re.sub(r'([a-z])([A-Z])', r'\1_\2', text)  # CamelCase to snake_case
        processed_text = re.sub(r'[\s_-]+', '_', processed_text).lower()  # Normalize delimiters
        
        parts = processed_text.split('_')
        expanded_parts = []
        
        for part in parts:
            # Try to expand each part as a whole first
            if part in self.ABBREVIATIONS:
                expanded_parts.append(self.ABBREVIATIONS[part])
            else:
                # For complex abbreviations like "custnum", try greedy matching
                remaining_part = part
                expanded_sub_parts = []
                
                # Sort abbreviations by length to match longest ones first
                sorted_abbrevs = sorted(self.ABBREVIATIONS.keys(), key=len, reverse=True)
                
                while remaining_part:
                    found_match = False
                    for abbrev in sorted_abbrevs:
                        if remaining_part.startswith(abbrev):
                            expanded_sub_parts.append(self.ABBREVIATIONS[abbrev])
                            remaining_part = remaining_part[len(abbrev):]
                            found_match = True
                            break
                    
                    if not found_match:
                        # If no abbreviation found, keep the original part
                        expanded_sub_parts.append(remaining_part)
                        break
                
                expanded_parts.append('_'.join(expanded_sub_parts))
        
        return '_'.join(expanded_parts)
    
    def get_variations(self, text: str) -> list[str]:
        """
        Get various representations of the text including abbreviated and expanded forms.
        
        Args:
            text: Input text
            
        Returns:
            List of text variations (original, expanded, common variations)
        """
        variations = [text, text.lower(), text.upper()]
        
        # Add expanded version
        expanded = self.expand_text(text)
        if expanded != text.lower():
            variations.append(expanded)
            # Also add camelCase and PascalCase versions
            variations.append(self._to_camel_case(expanded))
            variations.append(self._to_pascal_case(expanded))
        
        # Add common formatting variations
        # Handle underscores and spaces
        if '_' in text:
            variations.append(text.replace('_', ''))  # Remove underscores
            variations.append(text.replace('_', ' '))  # Spaces instead of underscores
        
        # Handle camelCase breakdown
        import re
        if re.search(r'[a-z][A-Z]', text):  # Has camelCase
            snake_case = re.sub(r'([a-z])([A-Z])', r'\1_\2', text).lower()
            variations.append(snake_case)
            variations.append(snake_case.replace('_', ' '))
        
        # Add reverse expansions - try to find abbreviated forms of the target
        if not any(c in text for c in '_-'):  # If it's a compound word without delimiters
            # Try to break it into parts and abbreviate
            words = self._extract_words(text)
            if len(words) > 1:
                abbreviated = ''.join(word[:1].upper() for word in words)
                variations.append(abbreviated)
                abbreviated_with_underscores = '_'.join(word[:1].upper() for word in words)
                variations.append(abbreviated_with_underscores)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(variations))
    
    def _extract_words(self, text: str) -> list[str]:
        """Extract individual words from camelCase or compound text."""
        import re
        # Handle camelCase
        words = re.findall(r'[A-Z][a-z]*|[a-z]+', text)
        return [word.lower() for word in words if word]
    
    def _to_camel_case(self, text: str) -> str:
        """Convert text to camelCase."""
        components = text.replace('_', ' ').split()
        return components[0].lower() + ''.join(word.capitalize() for word in components[1:])
    
    def _to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase."""
        components = text.replace('_', ' ').split()
        return ''.join(word.capitalize() for word in components)