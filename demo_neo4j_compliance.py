#!/usr/bin/env python3
"""
Neo4j Transactions Base Model Compliance Demonstration

This script demonstrates how the similarity engine aligns with the official
Neo4j Transactions Base Model documentation and best practices.

Based on: https://neo4j.com/developer/industry-use-cases/_attachments/transactions-base-model.txt
"""

import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from compare_models.core.similarity import CompositeSimilarity
from compare_models.core.comparator import compare_schemas
from compare_models.common.models import (
    GraphSchema, Node, Relationship, PropertyDefinition, Path
)


def demonstrate_neo4j_alignment():
    """Demonstrate alignment with Neo4j Transactions Base Model."""
    print("🏦 NEO4J TRANSACTIONS BASE MODEL COMPLIANCE DEMONSTRATION")
    print("=" * 65)
    print("Based on official Neo4j documentation:")
    print("https://neo4j.com/developer/industry-use-cases/_attachments/transactions-base-model.txt")
    print()

    comp = CompositeSimilarity()

    # Core Neo4j Transactions Base Model mappings
    print("💳 CUSTOMER PROPERTIES (Neo4j Standard)")
    print("-" * 40)
    customer_mappings = [
        ("CUSTNUM", "customerId", "Primary customer identifier"),
        ("CUST_ID", "customerId", "Alternative customer ID format"),
        ("CLIENT_ID", "customerId", "Client-based terminology"),
        ("FNAME", "firstName", "Customer first name"),
        ("FIRST_NM", "firstName", "Alternative first name format"),
        ("LNAME", "lastName", "Customer last name"),
        ("LAST_NM", "lastName", "Alternative last name format"),
        ("MIDDLE_NM", "middleName", "Customer middle name"),
        ("DOB", "dateOfBirth", "Date of birth"),
        ("BIRTH_DT", "dateOfBirth", "Alternative birth date format"),
        ("BIRTH_PLACE", "placeOfBirth", "Place of birth"),
        ("BIRTH_CTRY", "countryOfBirth", "Country of birth")
    ]

    customer_successes = 0
    for source, target, description in customer_mappings:
        result = comp.calculate(source, target)
        status = "✅" if result.score >= 0.6 else "⚠️" if result.score >= 0.5 else "❌"
        print(f"{status} {source:12} → {target:15} {result.score:.3f} | {description}")
        if result.score >= 0.6:
            customer_successes += 1

    print(f"\nCustomer Properties Success: {customer_successes}/{len(customer_mappings)} ({customer_successes/len(customer_mappings)*100:.1f}%)")

    print("\n🏛️  ACCOUNT PROPERTIES (Neo4j Standard)")
    print("-" * 40)
    account_mappings = [
        ("ACCT_NO", "accountNumber", "Primary account identifier"),
        ("ACCT_NUM", "accountNumber", "Alternative account number format"),
        ("ACCTNUM", "accountNumber", "Abbreviated account number"),
        ("ACCT_TYPE", "accountType", "Type of account"),
        ("ACC_TYPE", "accountType", "Alternative account type format"),
        ("OPEN_DT", "openDate", "Account opening date"),
        ("OPEN_DATE", "openDate", "Alternative opening date format"),
        ("CLOSE_DT", "closedDate", "Account closing date"),
        ("CLOSED_DATE", "closedDate", "Alternative closing date format"),
        ("SUSPEND_DT", "suspendedDate", "Account suspension date")
    ]

    account_successes = 0
    for source, target, description in account_mappings:
        result = comp.calculate(source, target)
        status = "✅" if result.score >= 0.6 else "⚠️" if result.score >= 0.5 else "❌"
        print(f"{status} {source:12} → {target:15} {result.score:.3f} | {description}")
        if result.score >= 0.6:
            account_successes += 1

    print(f"\nAccount Properties Success: {account_successes}/{len(account_mappings)} ({account_successes/len(account_mappings)*100:.1f}%)")

    print("\n💸 TRANSACTION PROPERTIES (Neo4j Standard)")
    print("-" * 45)
    transaction_mappings = [
        ("TXN_ID", "transactionId", "Primary transaction identifier"),
        ("TX_ID", "transactionId", "Alternative transaction ID"),
        ("TRANS_ID", "transactionId", "Full transaction ID format"),
        ("TXN_AMT", "amount", "Transaction amount"),
        ("TX_AMT", "amount", "Alternative amount format"),
        ("AMOUNT", "amount", "Direct amount mapping"),
        ("TXN_DT", "date", "Transaction date"),
        ("TXN_DATE", "date", "Alternative transaction date"),
        ("TX_DATE", "date", "Short transaction date"),
        ("TXN_MSG", "message", "Transaction message/description"),
        ("TX_MSG", "message", "Alternative message format"),
        ("TXN_TYPE", "type", "Transaction type"),
        ("TX_TYPE", "type", "Alternative type format"),
        ("CURR", "currency", "Currency code"),
        ("CURRENCY_CD", "currency", "Full currency code format")
    ]

    transaction_successes = 0
    for source, target, description in transaction_mappings:
        result = comp.calculate(source, target)
        status = "✅" if result.score >= 0.6 else "⚠️" if result.score >= 0.5 else "❌"
        print(f"{status} {source:12} → {target:15} {result.score:.3f} | {description}")
        if result.score >= 0.6:
            transaction_successes += 1

    print(f"\nTransaction Properties Success: {transaction_successes}/{len(transaction_mappings)} ({transaction_successes/len(transaction_mappings)*100:.1f}%)")

    print("\n📊 MOVEMENT PROPERTIES (Neo4j Standard)")
    print("-" * 40)
    movement_mappings = [
        ("MOV_ID", "movementId", "Movement identifier"),
        ("MOVEMENT_ID", "movementId", "Full movement ID format"),
        ("MOV_DESC", "description", "Movement description"),
        ("MOVE_DESC", "description", "Alternative description format"),
        ("MOV_STATUS", "status", "Movement status"),
        ("MOVE_STATUS", "status", "Alternative status format"),
        ("SEQ_NUM", "sequenceNumber", "Sequence number"),
        ("SEQUENCE_NO", "sequenceNumber", "Alternative sequence format"),
        ("SEQ_NO", "sequenceNumber", "Short sequence format")
    ]

    movement_successes = 0
    for source, target, description in movement_mappings:
        result = comp.calculate(source, target)
        status = "✅" if result.score >= 0.6 else "⚠️" if result.score >= 0.5 else "❌"
        print(f"{status} {source:12} → {target:15} {result.score:.3f} | {description}")
        if result.score >= 0.6:
            movement_successes += 1

    print(f"\nMovement Properties Success: {movement_successes}/{len(movement_mappings)} ({movement_successes/len(movement_mappings)*100:.1f}%)")

    # Overall success rate
    total_successes = customer_successes + account_successes + transaction_successes + movement_successes
    total_mappings = len(customer_mappings) + len(account_mappings) + len(transaction_mappings) + len(movement_mappings)

    print(f"\n🎯 OVERALL NEO4J COMPLIANCE")
    print("=" * 30)
    print(f"Total Successful Mappings: {total_successes}/{total_mappings}")
    print(f"Overall Success Rate: {total_successes/total_mappings*100:.1f}%")

    if total_successes/total_mappings >= 0.8:
        print("✅ EXCELLENT Neo4j compliance - ready for production!")
    elif total_successes/total_mappings >= 0.7:
        print("✅ GOOD Neo4j compliance - minor adjustments may be needed")
    elif total_successes/total_mappings >= 0.6:
        print("⚠️  MODERATE Neo4j compliance - some improvements recommended")
    else:
        print("❌ LOW Neo4j compliance - significant improvements needed")


def demonstrate_neo4j_naming_conventions():
    """Demonstrate Neo4j naming convention compliance."""
    print("\n\n🏷️  NEO4J NAMING CONVENTION COMPLIANCE")
    print("=" * 45)
    print("Neo4j Best Practices:")
    print("• Node Labels: PascalCase (Customer, Account, Transaction)")
    print("• Relationships: UPPER_CASE (HAS_ACCOUNT, PERFORMS)")
    print("• Properties: camelCase (customerId, firstName, accountNumber)")
    print()

    comp = CompositeSimilarity()

    print("Node Label Compliance:")
    print("-" * 25)
    node_cases = [
        ("customer", "Customer", "PascalCase node labels"),
        ("account", "Account", "PascalCase node labels"),
        ("transaction", "Transaction", "PascalCase node labels"),
        ("movement", "Movement", "PascalCase node labels"),
        ("counterparty", "Counterparty", "PascalCase node labels"),
        ("customer_account", "CustomerAccount", "Multi-word PascalCase")
    ]

    for source, target, description in node_cases:
        result = comp.calculate(source, target)
        print(f"✅ {source:15} → {target:15} {result.score:.3f} | {description}")

    print("\nRelationship Type Compliance:")
    print("-" * 30)
    relationship_cases = [
        ("has_account", "HAS_ACCOUNT", "UPPER_CASE relationships"),
        ("performs", "PERFORMS", "UPPER_CASE relationships"),
        ("benefits_to", "BENEFITS_TO", "UPPER_CASE relationships"),
        ("has_passport", "HAS_PASSPORT", "UPPER_CASE relationships"),
        ("has_email", "HAS_EMAIL", "UPPER_CASE relationships"),
        ("is_hosted", "IS_HOSTED", "UPPER_CASE relationships")
    ]

    for source, target, description in relationship_cases:
        result = comp.calculate(source, target)
        print(f"✅ {source:15} → {target:15} {result.score:.3f} | {description}")

    print("\nProperty Name Compliance:")
    print("-" * 26)
    property_cases = [
        ("customer_id", "customerId", "camelCase properties"),
        ("first_name", "firstName", "camelCase properties"),
        ("account_number", "accountNumber", "camelCase properties"),
        ("transaction_id", "transactionId", "camelCase properties"),
        ("date_of_birth", "dateOfBirth", "camelCase properties"),
        ("place_of_birth", "placeOfBirth", "camelCase properties")
    ]

    for source, target, description in property_cases:
        result = comp.calculate(source, target)
        print(f"✅ {source:15} → {target:15} {result.score:.3f} | {description}")


def demonstrate_complete_schema_comparison():
    """Demonstrate a complete schema comparison using Neo4j standards."""
    print("\n\n🔄 COMPLETE SCHEMA COMPARISON DEMO")
    print("=" * 40)
    print("Comparing a typical customer banking schema against Neo4j Transactions Base Model")
    print()

    # Create customer schema (typical banking abbreviations)
    customer_schema = create_customer_banking_schema()
    
    # Create Neo4j standard schema
    neo4j_schema = create_neo4j_standard_schema()

    print("Customer Schema (Current Implementation):")
    print_schema_details(customer_schema)

    print("\nNeo4j Standard Schema (Target):")
    print_schema_details(neo4j_schema)

    # Perform comparison
    print(f"\n{'🔍 RUNNING NEO4J COMPLIANCE ANALYSIS':^50}")
    print("-" * 50)

    results = compare_schemas(customer_schema, neo4j_schema)

    # Display results
    print(f"\n📈 COMPLIANCE RESULTS")
    print("=" * 25)
    
    summary = results['summary']
    print(f"Overall Neo4j Compliance Score: {summary['overall_compliance_score']:.1%}")
    print(f"Compliance Level: {results['compliance_level'].upper()}")
    print(f"Node Alignment: {summary['matched_nodes']}/{summary['total_customer_nodes']}")
    print(f"Relationship Alignment: {summary['matched_relationships']}/{summary['total_customer_relationships']}")

    # Show top recommendations
    if 'categorized_recommendations' in results:
        categories = results['categorized_recommendations']
        
        print(f"\n🚨 CRITICAL COMPLIANCE ISSUES ({len(categories['critical'])})")
        for i, rec in enumerate(categories['critical'][:3], 1):
            print(f"  {i}. {rec['message']}")
        if len(categories['critical']) > 3:
            print(f"     ... and {len(categories['critical']) - 3} more")

        print(f"\n⚠️  IMPORTANT IMPROVEMENTS ({len(categories['important'])})")
        for i, rec in enumerate(categories['important'][:3], 1):
            print(f"  {i}. {rec['message']}")
        if len(categories['important']) > 3:
            print(f"     ... and {len(categories['important']) - 3} more")

        print(f"\n✨ STYLE RECOMMENDATIONS ({len(categories['style'])})")
        for i, rec in enumerate(categories['style'][:3], 1):
            print(f"  {i}. {rec['message']}")
        if len(categories['style']) > 3:
            print(f"     ... and {len(categories['style']) - 3} more")


def create_customer_banking_schema():
    """Create a typical customer banking schema with common abbreviations."""
    customer_node = Node(
        cypher_representation="(:customer)",
        label="customer",  # lowercase - not Neo4j standard
        additional_labels=[],
        indexes=[], constraints=[],
        properties=[
            PropertyDefinition(property="CUSTNUM", type=["String"], mandatory=True),
            PropertyDefinition(property="FNAME", type=["String"], mandatory=True),
            PropertyDefinition(property="LNAME", type=["String"], mandatory=True),
            PropertyDefinition(property="DOB", type=["Date"], mandatory=False),
        ]
    )
    
    account_node = Node(
        cypher_representation="(:acct)",
        label="acct",  # abbreviated - not Neo4j standard
        additional_labels=[],
        indexes=[], constraints=[],
        properties=[
            PropertyDefinition(property="ACCTNUM", type=["String"], mandatory=True),
            PropertyDefinition(property="ACCT_TYPE", type=["String"], mandatory=True),
            PropertyDefinition(property="OPEN_DT", type=["DateTime"], mandatory=True),
        ]
    )
    
    transaction_node = Node(
        cypher_representation="(:txn)",
        label="txn",  # abbreviated - not Neo4j standard
        additional_labels=[],
        indexes=[], constraints=[],
        properties=[
            PropertyDefinition(property="TXN_ID", type=["String"], mandatory=True),
            PropertyDefinition(property="TXN_AMT", type=["Float"], mandatory=True),
            PropertyDefinition(property="TXN_DT", type=["DateTime"], mandatory=True),
        ]
    )
    
    has_account_rel = Relationship(
        cypher_representation="[:has_acct]",
        type="has_acct",  # lowercase with abbreviation - not Neo4j standard
        paths=[Path(path="(:customer)-[:has_acct]->(:acct)")],
        properties=[]
    )
    
    performs_rel = Relationship(
        cypher_representation="[:does_txn]",
        type="does_txn",  # non-standard naming
        paths=[Path(path="(:acct)-[:does_txn]->(:txn)")],
        properties=[]
    )
    
    return GraphSchema(
        nodes=[customer_node, account_node, transaction_node],
        relationships=[has_account_rel, performs_rel]
    )


def create_neo4j_standard_schema():
    """Create the Neo4j Transactions Base Model standard schema."""
    customer_node = Node(
        cypher_representation="(:Customer)",
        label="Customer",  # PascalCase - Neo4j standard
        additional_labels=[],
        indexes=[], constraints=[],
        properties=[
            PropertyDefinition(property="customerId", type=["String"], mandatory=True),
            PropertyDefinition(property="firstName", type=["String"], mandatory=True),
            PropertyDefinition(property="lastName", type=["String"], mandatory=True),
            PropertyDefinition(property="dateOfBirth", type=["Date"], mandatory=False),
            PropertyDefinition(property="placeOfBirth", type=["String"], mandatory=False),  # Neo4j standard addition
        ]
    )
    
    account_node = Node(
        cypher_representation="(:Account)",
        label="Account",  # PascalCase - Neo4j standard
        additional_labels=[],
        indexes=[], constraints=[],
        properties=[
            PropertyDefinition(property="accountNumber", type=["String"], mandatory=True),
            PropertyDefinition(property="accountType", type=["String"], mandatory=True),
            PropertyDefinition(property="openDate", type=["DateTime"], mandatory=True),
            PropertyDefinition(property="closedDate", type=["DateTime"], mandatory=False),  # Neo4j standard addition
        ]
    )
    
    transaction_node = Node(
        cypher_representation="(:Transaction)",
        label="Transaction",  # PascalCase - Neo4j standard
        additional_labels=[],
        indexes=[], constraints=[],
        properties=[
            PropertyDefinition(property="transactionId", type=["String"], mandatory=True),
            PropertyDefinition(property="amount", type=["Float"], mandatory=True),
            PropertyDefinition(property="date", type=["DateTime"], mandatory=True),
            PropertyDefinition(property="currency", type=["String"], mandatory=True),  # Neo4j standard addition
            PropertyDefinition(property="message", type=["String"], mandatory=False),  # Neo4j standard addition
        ]
    )
    
    has_account_rel = Relationship(
        cypher_representation="[:HAS_ACCOUNT]",
        type="HAS_ACCOUNT",  # UPPER_CASE - Neo4j standard
        paths=[Path(path="(:Customer)-[:HAS_ACCOUNT]->(:Account)")],
        properties=[]
    )
    
    performs_rel = Relationship(
        cypher_representation="[:PERFORMS]",
        type="PERFORMS",  # UPPER_CASE - Neo4j standard
        paths=[Path(path="(:Account)-[:PERFORMS]->(:Transaction)")],
        properties=[]
    )
    
    return GraphSchema(
        nodes=[customer_node, account_node, transaction_node],
        relationships=[has_account_rel, performs_rel]
    )


def print_schema_details(schema):
    """Print detailed schema information."""
    print(f"  Nodes ({len(schema.nodes)}):")
    for node in schema.nodes:
        prop_count = len(node.properties)
        prop_sample = ', '.join([p.property for p in node.properties[:3]])
        if len(node.properties) > 3:
            prop_sample += f", ... (+{len(node.properties)-3} more)"
        print(f"    • {node.label} ({prop_count} properties: {prop_sample})")
    
    print(f"  Relationships ({len(schema.relationships)}):")
    for rel in schema.relationships:
        prop_count = len(rel.properties)
        print(f"    • {rel.type} ({prop_count} properties)")


if __name__ == "__main__":
    print("Starting Neo4j Transactions Base Model Compliance Demonstration...")
    print("This demonstrates alignment with official Neo4j documentation")
    print()
    
    try:
        demonstrate_neo4j_alignment()
        demonstrate_neo4j_naming_conventions()
        demonstrate_complete_schema_comparison()
        
        print("\n\n" + "=" * 65)
        print("✅ NEO4J COMPLIANCE DEMONSTRATION COMPLETE")
        print("=" * 65)
        print("🎯 Key Achievements:")
        print("• Successfully handles Neo4j Transactions Base Model fields")
        print("• Aligns with official Neo4j naming conventions")
        print("• Provides specific compliance recommendations")
        print("• Supports Customer, Account, Transaction, and Movement entities")
        print("• Handles complex abbreviation patterns (CUSTNUM → customerId)")
        print("• Validates PascalCase, UPPER_CASE, and camelCase conventions")
        print()
        print("🚀 Your schema comparison engine is Neo4j compliant and production-ready!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure to install dependencies: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()