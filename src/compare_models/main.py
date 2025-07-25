import json
import logging
from .orchestrator import quick_compare


# Suppress verbose warnings from the Neo4j driver
logging.getLogger("neo4j").setLevel(logging.ERROR)


def main():
    """
    Simple script demonstrating schema comparison using the orchestrator.
    
    This provides a basic example of how to use the orchestration layer.
    For more advanced features, use the CLI interface.
    """
    print("🔍 Starting Neo4j schema comparison...")
    
    try:
        # Use the orchestrator for clean, simple comparison
        comparison_results = quick_compare(
            standard_name="transactions",
            similarity_threshold=0.7,
            use_adaptive=True
        )
        
        print("\n📊 Comparison Results:")
        print(json.dumps(comparison_results, indent=2))
        
        # Display summary
        print(f"\n✨ Compliance Summary:")
        print(f"Overall Score: {comparison_results['summary']['overall_compliance_score']:.1%}")
        print(f"Compliance Level: {comparison_results['compliance_level'].upper()}")
        print(f"Matched Nodes: {comparison_results['summary']['matched_nodes']}/{comparison_results['summary']['total_customer_nodes']}")
        print(f"Matched Relationships: {comparison_results['summary']['matched_relationships']}/{comparison_results['summary']['total_customer_relationships']}")
        
        # Show key recommendations
        if 'categorized_recommendations' in comparison_results:
            categories = comparison_results['categorized_recommendations']
            
            if categories['critical']:
                print(f"\n🚨 Critical Issues ({len(categories['critical'])}):")
                for i, rec in enumerate(categories['critical'][:3], 1):
                    print(f"  {i}. {rec['message']}")
                if len(categories['critical']) > 3:
                    print(f"     ... and {len(categories['critical']) - 3} more")
            
            if categories['important']:
                print(f"\n⚠️  Important Issues ({len(categories['important'])}):")
                for i, rec in enumerate(categories['important'][:3], 1):
                    print(f"  {i}. {rec['message']}")
                if len(categories['important']) > 3:
                    print(f"     ... and {len(categories['important']) - 3} more")
        
        print(f"\n🎯 Use the CLI interface for advanced features like database selection and rich output!")
        
    except Exception as e:
        print(f"❌ Error during comparison: {e}")
        print("Make sure your Neo4j connection is configured in .env file")
        raise


if __name__ == "__main__":
    main()
