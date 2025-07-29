"""
Orchestration layer for schema comparison workflows.

This module provides clean entry points for different schema comparison workflows
without mixing CLI concerns into the core business logic. It orchestrates existing
functions to provide reusable workflows for CLI, REST API, or other interfaces.
"""

from typing import Dict, Any, Optional
from .schemas.client import get_graph_schema
from .schemas.standard.transactions import get_standard_schema
from .core.comparator import compare_schemas
from .common.models import GraphSchema


class SchemaComparator:
    """
    Main orchestrator for schema comparison workflows.
    
    This class coordinates the various components (schema loading, comparison,
    analysis) without containing CLI-specific logic, making it reusable across
    different interfaces (CLI, REST API, etc.).
    """
    
    def __init__(self):
        """Initialize the schema comparator."""
        pass
    
    def compare_database_to_standard(
        self,
        standard_name: str = "transactions",
        similarity_threshold: float = 0.7,
        use_adaptive: bool = True,
        verbose: bool = False,
        entity_centric: bool = False
    ) -> Dict[str, Any]:
        """
        Compare a database schema to a standard Neo4j model.
        
        This is the main entry point for schema comparison workflows.
        It orchestrates schema extraction, standard loading, and comparison.
        
        Args:
            standard_name: Name of the standard to compare against
            similarity_threshold: Minimum similarity score for matches
            use_adaptive: Whether to use adaptive similarity weighting
            
        Returns:
            Comprehensive comparison results with matches, gaps, and recommendations
        """
        # Load the existing database schema
        existing_schema = get_graph_schema()
        
        # Load the standard schema
        standard_schema = self._get_standard_schema(standard_name)
        
        # Perform the comparison
        comparison_results = compare_schemas(
            existing_schema, 
            standard_schema,
            similarity_threshold=similarity_threshold,
            use_adaptive=use_adaptive,
            verbose=verbose,
            entity_centric=entity_centric
        )
        
        return comparison_results
    
    def compare_schemas(
        self,
        existing_schema: GraphSchema,
        standard_schema: GraphSchema,
        similarity_threshold: float = 0.7,
        use_adaptive: bool = True,
        verbose: bool = False,
        entity_centric: bool = False
    ) -> Dict[str, Any]:
        """
        Compare two GraphSchema objects directly.
        
        Useful when you already have schema objects loaded and want to
        compare them without going through the database extraction process.
        
        Args:
            existing_schema: The current database schema
            standard_schema: The standard schema to compare against
            similarity_threshold: Minimum similarity score for matches
            use_adaptive: Whether to use adaptive similarity weighting
            
        Returns:
            Comprehensive comparison results
        """
        return compare_schemas(
            existing_schema,
            standard_schema,
            similarity_threshold=similarity_threshold,
            use_adaptive=use_adaptive,
            verbose=verbose,
            entity_centric=entity_centric
        )
    
    def get_database_schema(self) -> GraphSchema:
        """
        Extract schema from the configured database.
        
        Returns:
            GraphSchema object representing the current database structure
        """
        return get_graph_schema()
    
    def get_standard_schema(self, standard_name: str = "transactions") -> GraphSchema:
        """
        Load a standard Neo4j schema by name.
        
        Args:
            standard_name: Name of the standard schema to load
            
        Returns:
            GraphSchema object representing the standard structure
        """
        return self._get_standard_schema(standard_name)
    
    def _get_standard_schema(self, standard_name: str) -> GraphSchema:
        """
        Internal method to load standard schemas.
        
        Args:
            standard_name: Name of the standard schema
            
        Returns:
            GraphSchema object for the requested standard
            
        Raises:
            ValueError: If the standard name is not recognized
        """
        if standard_name.lower() == "transactions":
            return get_standard_schema()
        else:
            raise ValueError(f"Unknown standard schema: {standard_name}")
    
    def validate_similarity_settings(
        self,
        similarity_threshold: float,
        use_adaptive: bool
    ) -> Dict[str, Any]:
        """
        Validate and provide information about similarity settings.
        
        Args:
            similarity_threshold: Threshold to validate
            use_adaptive: Adaptive setting to validate
            
        Returns:
            Dictionary with validation results and recommendations
        """
        validation_result = {
            "valid": True,
            "warnings": [],
            "recommendations": []
        }
        
        # Validate similarity threshold
        if not 0.0 <= similarity_threshold <= 1.0:
            validation_result["valid"] = False
            validation_result["warnings"].append(
                f"Similarity threshold {similarity_threshold} must be between 0.0 and 1.0"
            )
        elif similarity_threshold < 0.5:
            validation_result["warnings"].append(
                f"Low similarity threshold ({similarity_threshold}) may produce many false matches"
            )
        elif similarity_threshold > 0.9:
            validation_result["warnings"].append(
                f"High similarity threshold ({similarity_threshold}) may miss valid matches"
            )
        
        # Provide adaptive recommendations
        if use_adaptive:
            validation_result["recommendations"].append(
                "Adaptive weighting will optimize similarity techniques based on field characteristics"
            )
        else:
            validation_result["recommendations"].append(
                "Fixed weighting uses predefined technique weights - consider adaptive for better results"
            )
        
        return validation_result


# Convenience instance for simple usage
comparator = SchemaComparator()


def quick_compare(
    standard_name: str = "transactions",
    similarity_threshold: float = 0.7,
    use_adaptive: bool = True
) -> Dict[str, Any]:
    """
    Quick comparison function for simple use cases.
    
    This is a convenience function that provides the most common comparison
    workflow in a single function call.
    
    Args:
        standard_name: Standard schema to compare against
        similarity_threshold: Minimum similarity score for matches
        use_adaptive: Whether to use adaptive similarity weighting
        
    Returns:
        Comprehensive comparison results
    """
    return comparator.compare_database_to_standard(
        standard_name=standard_name,
        similarity_threshold=similarity_threshold,
        use_adaptive=use_adaptive
    )