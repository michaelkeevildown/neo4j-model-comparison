import json
import logging
from .schemas.client import get_graph_schema
from .core.comparator import compare_schemas
from .schemas.standard.transactions import get_standard_schema


# Suppress verbose warnings from the Neo4j driver
logging.getLogger("neo4j").setLevel(logging.ERROR)


def main():
    # 1. Extract the existing graph schema
    existing_schema = get_graph_schema()
    print("Successfully extracted existing schema:")
    print(json.dumps(existing_schema.model_dump(), indent=2))

    # 2. Load the standard schema
    standard_schema = get_standard_schema()
    print("\nSuccessfully loaded standard schema:")
    print(json.dumps(standard_schema.model_dump(), indent=2))

    # 3. Compare the two schemas
    comparison_results = compare_schemas(existing_schema, standard_schema)
    print("\nSchema comparison results:")
    print(json.dumps(comparison_results, indent=2))

    # 4. Display basic results summary
    print(f"\nCompliance Summary:")
    print(f"Overall Score: {comparison_results['summary']['overall_compliance_score']:.1%}")
    print(f"Compliance Level: {comparison_results['compliance_level'].upper()}")
    print(f"Matched Nodes: {comparison_results['summary']['matched_nodes']}/{comparison_results['summary']['total_customer_nodes']}")
    print(f"Matched Relationships: {comparison_results['summary']['matched_relationships']}/{comparison_results['summary']['total_customer_relationships']}")


if __name__ == "__main__":
    main()
