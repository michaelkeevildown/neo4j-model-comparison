# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Neo4j data model comparison and compliance project that helps organizations align their existing graph database schemas with standardized data models. The project's primary purpose is to:

1. **Extract and Analyze Existing Schemas** - Pull down schema information from customer Neo4j databases to understand their current data model implementation
2. **Compare Against Standards** - Compare the existing schema against Neo4j's standardized data models (e.g., the Transactions and Accounts model)
3. **Generate Compliance Reports** - Identify gaps and provide specific recommendations for achieving compliance with the standard

The project uses AI (OpenAI GPT-4o) to enrich both the existing schema documentation and provide intelligent analysis of the differences between what exists and what should be implemented according to the standard.

### Business Use Case
A typical scenario would be a financial institution that has already implemented their own Neo4j data model for handling transactions and accounts. This tool would:
- Connect to their database and extract their current schema
- Compare it against Neo4j's standardized Transactions and Accounts data model
- Identify discrepancies (e.g., node labels using lowercase "account" instead of standardized "Account")
- Provide specific recommendations for achieving compliance with the standard model

## Environment Setup

This project uses Python 3.13+ with a virtual environment located in `venv/`. 

### Dependencies
- `neo4j==5.28.1` - Neo4j Python driver for database connectivity
- `python-dotenv==1.1.1` - Environment variable management
- `pytz==2025.2` - Timezone handling
- `openai` - OpenAI API client (installed via pip in the sample script)
- `langchain` and `langchain-openai` - LangChain framework components

### Environment Variables
The project expects configuration through a config file (typically `config.cfg`) with sections for:
- `[OpenAI]` - API keys for OpenAI access
- `[PersonalEnv]` - Neo4j database connection details (url, username, password)

## Core Architecture

### Current Implementation
The `sample/dynamically_building_a_neo4j_data_model_representation_grounded_with_intent.py` script represents the foundation for schema extraction and analysis. It implements a 4-step process:

1. **Relationship Analysis** - Extracts relationships from Neo4j schema and enriches them with semantic descriptions using AI
2. **Node Analysis** - Extracts node labels and enriches them with contextual explanations  
3. **Relationship Properties** - Extracts and documents relationship properties with their intent
4. **Node Properties** - Extracts and documents node properties with their semantic meaning

The script builds a comprehensive graph schema representation stored in `finalised_graph_structure` containing:
- Nodes with labels, Cypher representations, indexes, constraints, and properties
- Relationships with types, paths, properties, and semantic details

### Target Standard Model
The project compares against Neo4j's standardized Transactions and Accounts data model which includes:

**Primary Node Types:**
- `Customer` - Core identity node for account holders
- `Account` (Internal/External) - Banking account entities
- `Transaction` - Financial transaction records
- `Movement` - Individual transaction components
- Identity verification nodes (`Passport`, `DrivingLicense`, `Face`)
- Digital access nodes (`Device`, `IP`, `Session`)

**Key Design Principles:**
- Standardized naming conventions (proper case node labels)
- Comprehensive property definitions with specific data types
- Explicit relationship semantics for regulatory compliance
- Support for multi-dimensional identity verification and KYC processes

### Comparison Workflow
The intended workflow combines the existing schema extraction with comparison logic:
1. Extract customer's existing schema using the current implementation
2. Load the standardized model definition
3. Compare structures, identifying naming discrepancies, missing nodes/relationships, and property differences
4. Generate specific compliance recommendations

## Common Commands

### Virtual Environment
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Main Script
```bash
python sample/dynamically_building_a_neo4j_data_model_representation_grounded_with_intent.py
```

### Database Connection
The script connects to Neo4j using the `run_query()` function and expects:
- Neo4j URI (bolt/neo4j+s protocol)
- Username and password
- Database name (typically "reports" or "schema")

## Development Notes

- The sample script is originally from a Colab notebook and contains some Colab-specific imports that are conditionally handled
- Uses OpenAI GPT-4o model for generating semantic descriptions of schema elements
- Implements JSON parsing with error handling for AI responses
- Contains hardcoded sample data for testing node properties functionality
- Vector embeddings are documented as 256 dimensions
- The current implementation focuses on schema extraction and documentation; comparison logic against the standard model needs to be built
- Future development should include loading the standardized Transactions and Accounts model definition and implementing comparison algorithms

## Reference Materials

- **Neo4j Transactions Base Model**: https://neo4j.com/developer/industry-use-cases/data-models/transactions/transactions-base-model/
- This represents the target standard that customer databases should be compared against for compliance