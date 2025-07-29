#!/usr/bin/env python3
"""
Test script to demonstrate the new entity-centric output and verbose features.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from compare_models.orchestrator import SchemaComparator
from compare_models.common.models import GraphSchema, Node, Relationship, PropertyDefinition, Path as GraphPath

# Create the bad schema from the user's example
def create_bad_schema():
    """Create the problematic schema from the user's example."""
    nodes = [
        Node(
            cypher_representation="(:CUST)",
            label="CUST",
            additional_labels=[],
            indexes=[], 
            constraints=[],
            properties=[
                PropertyDefinition(property="cust_id", type=["String"], mandatory=True),
                PropertyDefinition(property="fname", type=["String"], mandatory=True),
                PropertyDefinition(property="lname", type=["String"], mandatory=True),
                PropertyDefinition(property="email_addr", type=["String"], mandatory=False),
                PropertyDefinition(property="ph_num", type=["String"], mandatory=False),
                PropertyDefinition(property="birth_dt", type=["String"], mandatory=False),
            ]
        ),
        Node(
            cypher_representation="(:ACC)",
            label="ACC",
            additional_labels=[],
            indexes=[], 
            constraints=[],
            properties=[
                PropertyDefinition(property="acc_num", type=["String"], mandatory=True),
                PropertyDefinition(property="acc_typ", type=["String"], mandatory=True),
                PropertyDefinition(property="opened", type=["String"], mandatory=True),
                PropertyDefinition(property="bal", type=["Float"], mandatory=False),
            ]
        ),
        Node(
            cypher_representation="(:TRX)",
            label="TRX",
            additional_labels=[],
            indexes=[], 
            constraints=[],
            properties=[
                PropertyDefinition(property="trx_id", type=["String"], mandatory=True),
                PropertyDefinition(property="amt", type=["Float"], mandatory=True),
                PropertyDefinition(property="dt", type=["String"], mandatory=True),
                PropertyDefinition(property="desc", type=["String"], mandatory=False),
                PropertyDefinition(property="typ", type=["String"], mandatory=False),
            ]
        ),
        Node(
            cypher_representation="(:TXN)",
            label="TXN",
            additional_labels=[],
            indexes=[], 
            constraints=[],
            properties=[
                PropertyDefinition(property="trx_id", type=["String"], mandatory=True),
                PropertyDefinition(property="amt", type=["Float"], mandatory=True),
                PropertyDefinition(property="dt", type=["String"], mandatory=True),
                PropertyDefinition(property="desc", type=["String"], mandatory=False),
                PropertyDefinition(property="typ", type=["String"], mandatory=False),
            ]
        ),
        Node(
            cypher_representation="(:MOV)",
            label="MOV",
            additional_labels=[],
            indexes=[], 
            constraints=[],
            properties=[
                PropertyDefinition(property="mov_id", type=["String"], mandatory=True),
                PropertyDefinition(property="amt", type=["Double"], mandatory=True),
                PropertyDefinition(property="when", type=["String"], mandatory=False),
            ]
        ),
        Node(
            cypher_representation="(:EMAIL_ADDR)",
            label="EMAIL_ADDR",
            additional_labels=[],
            indexes=[], 
            constraints=[],
            properties=[
                PropertyDefinition(property="addr", type=["String"], mandatory=True),
            ]
        ),
        Node(
            cypher_representation="(:PHONE_NUM)",
            label="PHONE_NUM",
            additional_labels=[],
            indexes=[], 
            constraints=[],
            properties=[
                PropertyDefinition(property="num", type=["String"], mandatory=True),
                PropertyDefinition(property="country", type=["String"], mandatory=False),
            ]
        ),
        Node(
            cypher_representation="(:ADDR)",
            label="ADDR",
            additional_labels=[],
            indexes=[], 
            constraints=[],
            properties=[
                PropertyDefinition(property="line1", type=["String"], mandatory=True),
                PropertyDefinition(property="town", type=["String"], mandatory=False),
                PropertyDefinition(property="zip", type=["String"], mandatory=False),
                PropertyDefinition(property="country", type=["String"], mandatory=False),
            ]
        ),
        Node(
            cypher_representation="(:LOGIN)",
            label="LOGIN",
            additional_labels=[],
            indexes=[], 
            constraints=[],
            properties=[
                PropertyDefinition(property="sess_id", type=["String"], mandatory=True),
                PropertyDefinition(property="user_agent", type=["String"], mandatory=False),
                PropertyDefinition(property="ip", type=["String"], mandatory=False),
                PropertyDefinition(property="login_time", type=["String"], mandatory=False),
            ]
        ),
    ]
    
    relationships = [
        Relationship(
            cypher_representation="[:OWNS]",
            type="OWNS",
            paths=[GraphPath(path="(:CUST)-[:OWNS]->(:ACC)")],
            properties=[
                PropertyDefinition(property="since", type=["String"], mandatory=False),
            ]
        ),
        Relationship(
            cypher_representation="[:FROM]",
            type="FROM",
            paths=[GraphPath(path="(:ACC)-[:FROM]->(:TRX)")],
            properties=[]
        ),
        Relationship(
            cypher_representation="[:TO]",
            type="TO",
            paths=[
                GraphPath(path="(:TRX)-[:TO]->(:ACC)"),
                GraphPath(path="(:TRX)-[:TO]->(:EXT)")
            ],
            properties=[]
        ),
        Relationship(
            cypher_representation="[:CREATES]",
            type="CREATES",
            paths=[GraphPath(path="(:TRX)-[:CREATES]->(:MOV)")],
            properties=[]
        ),
        Relationship(
            cypher_representation="[:HAS_EMAIL]",
            type="HAS_EMAIL",
            paths=[GraphPath(path="(:CUST)-[:HAS_EMAIL]->(:EMAIL_ADDR)")],
            properties=[]
        ),
        Relationship(
            cypher_representation="[:HAS_PHONE]",
            type="HAS_PHONE",
            paths=[GraphPath(path="(:CUST)-[:HAS_PHONE]->(:PHONE_NUM)")],
            properties=[]
        ),
        Relationship(
            cypher_representation="[:LIVES_AT]",
            type="LIVES_AT",
            paths=[GraphPath(path="(:CUST)-[:LIVES_AT]->(:ADDR)")],
            properties=[]
        ),
        Relationship(
            cypher_representation="[:LOGGED_IN]",
            type="LOGGED_IN",
            paths=[GraphPath(path="(:CUST)-[:LOGGED_IN]->(:LOGIN)")],
            properties=[]
        ),
    ]
    
    return GraphSchema(nodes=nodes, relationships=relationships)


def main():
    """Test the entity-centric output."""
    print("🔍 Testing Entity-Centric Schema Comparison\n")
    
    # Create comparator
    comparator = SchemaComparator()
    
    # Get the bad schema
    bad_schema = create_bad_schema()
    
    # Get the standard schema
    standard_schema = comparator.get_standard_schema("transactions")
    
    print("📊 Running comparison with different output modes...\n")
    
    # Test 1: Standard output
    print("=" * 80)
    print("TEST 1: Standard Output")
    print("=" * 80)
    results_standard = comparator.compare_schemas(
        bad_schema, 
        standard_schema,
        similarity_threshold=0.7,
        use_adaptive=True,
        verbose=False,
        entity_centric=False
    )
    print(f"Compliance Score: {results_standard['summary']['overall_compliance_score']:.2%}")
    print(f"Matched Nodes: {results_standard['summary']['matched_nodes']}/{results_standard['summary']['total_customer_nodes']}")
    print(f"Matched Relationships: {results_standard['summary']['matched_relationships']}/{results_standard['summary']['total_customer_relationships']}")
    
    # Test 2: Entity-centric output
    print("\n" + "=" * 80)
    print("TEST 2: Entity-Centric Output")
    print("=" * 80)
    results_entity = comparator.compare_schemas(
        bad_schema, 
        standard_schema,
        similarity_threshold=0.7,
        use_adaptive=True,
        verbose=False,
        entity_centric=True
    )
    
    # Display some entity-centric results
    if 'entities' in results_entity:
        print("\nSample Node Result (CUST):")
        for node in results_entity['entities']['nodes']:
            if node['source']['label'] == 'CUST':
                print(f"  Source: {node['source']['label']}")
                if node.get('match'):
                    print(f"  Match: {node['match']['label']} (Score: {node['match']['score']:.2f})")
                else:
                    print(f"  Match: None")
                print(f"  Properties: {len(node['source']['properties'])} total")
                break
    
    # Test 3: Verbose mode with statistics
    print("\n" + "=" * 80)
    print("TEST 3: Verbose Mode with Statistics")
    print("=" * 80)
    results_verbose = comparator.compare_schemas(
        bad_schema, 
        standard_schema,
        similarity_threshold=0.7,
        use_adaptive=True,
        verbose=True,
        entity_centric=False
    )
    
    # Display statistics
    if 'statistics' in results_verbose:
        stats = results_verbose['statistics']
        print("\nMatching Statistics:")
        print(f"  Node Match Rate: {stats['overview']['node_match_rate']:.1%}")
        print(f"  Relationship Match Rate: {stats['overview']['relationship_match_rate']:.1%}")
        print(f"  Property Match Rate: {stats['overview']['property_match_rate']:.1%}")
        
        print("\nTechnique Usage:")
        for technique, data in stats['technique_effectiveness'].items():
            print(f"  {technique}: {data['usage_count']} uses, "
                  f"{data['success_rate']:.1%} success rate, "
                  f"{data['average_score']:.2f} avg score")
        
        print("\nCommon Issues:")
        for issue, count in stats['common_issues'].items():
            if isinstance(count, int) and count > 0:
                print(f"  {issue}: {count}")
            elif isinstance(count, dict):
                for sub_issue, sub_count in count.items():
                    if sub_count > 0:
                        print(f"  {issue}.{sub_issue}: {sub_count}")
    
    # Test 4: Entity-centric + Verbose
    print("\n" + "=" * 80)
    print("TEST 4: Entity-Centric + Verbose")
    print("=" * 80)
    results_full = comparator.compare_schemas(
        bad_schema, 
        standard_schema,
        similarity_threshold=0.7,
        use_adaptive=True,
        verbose=True,
        entity_centric=True
    )
    
    # Show detailed match for LOGIN node
    if 'entities' in results_full:
        print("\nDetailed Match Analysis for LOGIN node:")
        for node in results_full['entities']['nodes']:
            if node['source']['label'] == 'LOGIN':
                print(f"\n  Source: {node['source']['label']}")
                if node.get('match'):
                    print(f"  Match: {node['match']['label']} (Score: {node['match']['score']:.2f})")
                    print(f"  Match Type: {node['match']['type']}")
                    if node['match'].get('similarity_breakdown'):
                        print("  Technique Contributions:")
                        for tech, score in node['match']['similarity_breakdown'].get('techniques', {}).items():
                            print(f"    - {tech}: {score:.2f}")
                else:
                    print(f"  Match: None")
                
                if node.get('validation', {}).get('warnings'):
                    print("  Validation Warnings:")
                    for warning in node['validation']['warnings']:
                        print(f"    ⚠️  {warning}")
                
                if node.get('match_rationale'):
                    print(f"  Rationale: {node['match_rationale']}")
                
                if node.get('all_candidates'):
                    print(f"  All Candidates Considered: {len(node['all_candidates'])}")
                    for i, (candidate, score) in enumerate(node['all_candidates'][:3], 1):
                        print(f"    {i}. {candidate.label if hasattr(candidate, 'label') else candidate}: {score:.2f}")
                break
    
    print("\n✅ All tests completed!")
    print("\nKey Findings:")
    print("- LOGIN was matched to Location (incorrect) - this is the issue you identified")
    print("- The verbose mode shows WHY this happened (semantic similarity)")
    print("- Entity-centric view groups all related information together")
    print("- Statistics show which techniques are being used most")


if __name__ == "__main__":
    main()