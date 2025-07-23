"""
Semantic similarity calculation using embeddings and cosine similarity.
"""

import numpy as np
from typing import Optional, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity
from .base import SimilarityCalculator, SimilarityResult, AbbreviationExpander


class SemanticSimilarity(SimilarityCalculator):
    """
    Similarity calculator using semantic embeddings and cosine similarity.
    
    This approach understands the meaning behind field names, making it excellent
    for matching semantically similar but textually different terms like
    "customer_id" and "client_identifier".
    """
    
    def __init__(self, use_sentence_transformers: bool = True):
        super().__init__("semantic")
        self.expander = AbbreviationExpander()
        self.use_sentence_transformers = use_sentence_transformers
        self._model = None
        self._embedding_dim = 384  # For 'all-MiniLM-L6-v2'

        # Initialize the embedding model
        if use_sentence_transformers:
            try:
                from sentence_transformers import SentenceTransformer
                # Use a lightweight model good for short text similarity
                self._model = SentenceTransformer('all-MiniLM-L6-v2')
            except ImportError:
                print("Warning: sentence-transformers not available. SemanticSimilarity will be disabled.")
                self.use_sentence_transformers = False
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding vector for a text string."""
        if self._model:
            # Prepare text for better semantic understanding
            prepared_text = self._prepare_text_for_embedding(text)
            return self._model.encode([prepared_text])[0]
        else:
            # Return a zero vector if model is not available
            return np.zeros(self._embedding_dim)
    
    def _prepare_text_for_embedding(self, text: str) -> str:
        """
        Prepare text for better semantic embedding by expanding abbreviations
        and adding context.
        """
        # Expand abbreviations
        expanded = self.expander.expand_text(text)
        
        # Add context words to help the model understand this is a database field
        context_prefix = "database field property attribute"
        
        # Convert camelCase and snake_case to readable text
        readable = self._make_readable(expanded)
        
        return f"{context_prefix} {readable}"
    
    def _make_readable(self, text: str) -> str:
        """Convert field names to more readable format for embeddings."""
        import re
        
        # Handle camelCase
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        # Handle snake_case and kebab-case
        text = text.replace('_', ' ').replace('-', ' ')
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.lower().strip()
    
    def calculate(self, text1: str, text2: str) -> SimilarityResult:
        """Calculate semantic similarity between two strings."""
        if not self._model:
            return SimilarityResult(
                score=0.0,
                confidence=0.0,
                technique=self.name,
                metadata={"reason": "model_not_available"}
            )

        if not text1 or not text2:
            return SimilarityResult(
                score=0.0,
                confidence=1.0,
                technique=self.name,
                metadata={"reason": "empty_string"}
            )
        
        try:
            # Get embeddings for both texts
            embedding1 = self._get_embedding(text1)
            embedding2 = self._get_embedding(text2)
            
            # Calculate cosine similarity
            if len(embedding1.shape) == 1:
                embedding1 = embedding1.reshape(1, -1)
            if len(embedding2.shape) == 1:
                embedding2 = embedding2.reshape(1, -1)
            
            similarity = cosine_similarity(embedding1, embedding2)[0][0]
            
            # Ensure score is in [0, 1] range
            score = max(0.0, min(1.0, similarity))
            
            # Also try with expanded versions for comparison
            expanded_text1 = self.expander.expand_text(text1)
            expanded_text2 = self.expander.expand_text(text2)
            
            expanded_score = 0.0
            if expanded_text1 != text1.lower() or expanded_text2 != text2.lower():
                expanded_emb1 = self._get_embedding(expanded_text1)
                expanded_emb2 = self._get_embedding(expanded_text2)
                
                if len(expanded_emb1.shape) == 1:
                    expanded_emb1 = expanded_emb1.reshape(1, -1)
                if len(expanded_emb2.shape) == 1:
                    expanded_emb2 = expanded_emb2.reshape(1, -1)
                
                expanded_similarity = cosine_similarity(expanded_emb1, expanded_emb2)[0][0]
                expanded_score = max(0.0, min(1.0, expanded_similarity))
            
            # Use the better score
            final_score = max(score, expanded_score)
            
            # Confidence is generally high for semantic similarity
            confidence = 0.9 if final_score >= 0.8 else 0.8 if final_score >= 0.6 else 0.7
            
            return SimilarityResult(
                score=final_score,
                confidence=confidence,
                technique=self.name,
                metadata={
                    "raw_score": score,
                    "expanded_score": expanded_score,
                    "used_expansion": expanded_score > score,
                    "embedding_model": "sentence-transformers" if self.use_sentence_transformers else "disabled",
                    "prepared_text1": self._prepare_text_for_embedding(text1),
                    "prepared_text2": self._prepare_text_for_embedding(text2)
                }
            )
            
        except Exception as e:
            # If semantic similarity fails, return a low-confidence zero score
            return SimilarityResult(
                score=0.0,
                confidence=0.3,
                technique=self.name,
                metadata={
                    "error": str(e),
                    "fallback_reason": "embedding_calculation_failed"
                }
            )


class ContextualSimilarity(SimilarityCalculator):
    """
    Contextual similarity calculator that considers database and domain context.
    
    Uses predefined knowledge about common database field patterns and
    financial/banking domain terminology.
    """
    
    def __init__(self):
        super().__init__("contextual")
        self.expander = AbbreviationExpander()
        
        # Domain-specific synonyms and related terms
        self.domain_synonyms = {
            'customer': ['client', 'user', 'person', 'individual', 'holder'],
            'account': ['acct', 'acc', 'wallet', 'profile'],
            'transaction': ['txn', 'tx', 'trx', 'payment', 'transfer', 'operation'],
            'amount': ['amt', 'value', 'sum', 'total', 'balance'],
            'identifier': ['id', 'key', 'code', 'number', 'ref'],
            'date': ['dt', 'time', 'timestamp', 'when', 'created'],
            'type': ['typ', 'kind', 'category', 'class'],
            'status': ['state', 'condition', 'flag', 'indicator'],
            'description': ['desc', 'detail', 'info', 'comment'],
            'address': ['addr', 'location', 'place']
        }
        
        # Common field patterns in financial databases
        self.field_patterns = {
            'primary_key': ['id', 'key', 'identifier', 'number'],
            'foreign_key': ['ref', 'reference', 'link', 'pointer'],
            'monetary': ['amount', 'balance', 'sum', 'total', 'value'],
            'temporal': ['date', 'time', 'timestamp', 'created', 'updated'],
            'categorical': ['type', 'category', 'class', 'kind', 'status'],
            'descriptive': ['name', 'title', 'description', 'comment', 'note']
        }
    
    def _get_domain_score(self, text1: str, text2: str) -> float:
        """Calculate similarity based on domain knowledge."""
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        # Check for exact matches in synonyms
        for canonical, synonyms in self.domain_synonyms.items():
            all_terms = [canonical] + synonyms
            
            # Check if both texts contain terms from the same synonym group
            text1_matches = [term for term in all_terms if term in text1_lower]
            text2_matches = [term for term in all_terms if term in text2_lower]
            
            if text1_matches and text2_matches:
                return 0.9  # High score for domain synonym matches
        
        # Check field pattern similarity
        text1_patterns = []
        text2_patterns = []
        
        for pattern, keywords in self.field_patterns.items():
            if any(keyword in text1_lower for keyword in keywords):
                text1_patterns.append(pattern)
            if any(keyword in text2_lower for keyword in keywords):
                text2_patterns.append(pattern)
        
        # If both texts match the same pattern category
        common_patterns = set(text1_patterns) & set(text2_patterns)
        if common_patterns:
            return 0.7  # Good score for pattern matches
        
        return 0.0
    
    def calculate(self, text1: str, text2: str) -> SimilarityResult:
        """Calculate contextual similarity between two strings."""
        if not text1 or not text2:
            return SimilarityResult(
                score=0.0,
                confidence=1.0,
                technique=self.name,
                metadata={"reason": "empty_string"}
            )
        
        # Get domain-based score
        domain_score = self._get_domain_score(text1, text2)
        
        # Also check with expanded versions
        expanded_text1 = self.expander.expand_text(text1)
        expanded_text2 = self.expander.expand_text(text2)
        expanded_domain_score = self._get_domain_score(expanded_text1, expanded_text2)
        
        # Use the better score
        final_score = max(domain_score, expanded_domain_score)
        
        # Confidence is high when we have domain knowledge matches
        confidence = 0.95 if final_score >= 0.8 else 0.8 if final_score >= 0.6 else 0.6
        
        return SimilarityResult(
            score=final_score,
            confidence=confidence,
            technique=self.name,
            metadata={
                "domain_score": domain_score,
                "expanded_domain_score": expanded_domain_score,
                "used_expansion": expanded_domain_score > domain_score,
                "expanded_text1": expanded_text1,
                "expanded_text2": expanded_text2
            }
        )