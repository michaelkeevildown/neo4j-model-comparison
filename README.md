# 🎯 Transform Your Neo4j Schema to Official Standards

**Stop guessing. Start conforming.** 

Your Neo4j database works, but does it follow best practices? This tool compares your existing schema against [Neo4j's official Transactions & Accounts model](https://neo4j.com/developer/industry-use-cases/data-models/transactions/transactions-base-model/) and shows you exactly what needs to change.

## ⚡ The Problem

Your database probably looks like this:

```json
{
  "label": "account",
  "additional_labels": ["internal"],
  "constraints": [],
  "indexes": [],
  "properties": [
    {"property": "account_number", "type": ["Long"], "mandatory": true}
  ]
}
```

**But Neo4j's official standard looks like this:**

```json
{
  "label": "Account", 
  "additional_labels": ["Internal", "External", "HighRiskJurisdiction"],
  "constraints": [
    {
      "type": "NODE_KEY",
      "properties": ["accountNumber"],
      "name": "account_number_key"
    }
  ],
  "indexes": [
    {
      "type": "PROPERTY",
      "properties": ["openDate"],
      "name": "account_date_idx"
    }
  ]
}
```

**See the difference?** Proper casing, comprehensive constraints, strategic indexes, and complete property definitions.

## 🔥 Built on Neo4j's Official Standards

This isn't just any comparison tool. It **automatically syncs with Neo4j's official documentation** at:
- 📖 [Neo4j Transactions Base Model](https://neo4j.com/developer/industry-use-cases/data-models/transactions/transactions-base-model/)

Every time you run it, you're comparing against the latest official standard. No manual updates, no outdated specs.

## 🚀 Quick Start

### Option 1: Beautiful CLI Interface (Recommended) 🎨

```bash
# 1. Setup
git clone <repo>
cd compare-models
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. For Neo4j Aura users (drag-and-drop credentials!)
python cli/main.py compare --aura-file /path/to/Neo4j-credentials.txt

# 3. Interactive database selection
python cli/main.py compare --aura-file credentials.txt
# → Shows all databases → Interactive selection → Beautiful results

# 4. Direct connection
python cli/main.py compare --uri neo4j://localhost:7687 --username neo4j --password password
```

### Option 2: Programmatic Usage

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your Neo4j credentials

# 2. Run basic comparison
python -m src.compare_models.main

# 3. Or use the orchestrator directly
python -c "
from src.compare_models.orchestrator import quick_compare
results = quick_compare(standard_name='transactions', similarity_threshold=0.7)
print(f'Compliance Score: {results['summary']['overall_compliance_score']:.1%}')
"
```

## 🎯 Neo4j Aura Integration

**Special support for Neo4j Aura users!** Just drag and drop your credentials file:

```bash
# Import and validate Aura credentials
python cli/main.py import-credentials ~/Downloads/Neo4j-MyInstance.txt

# List all databases in your Aura instance
python cli/main.py list-databases --aura-file ~/Downloads/Neo4j-MyInstance.txt

# Compare with beautiful interactive selection
python cli/main.py compare --aura-file ~/Downloads/Neo4j-MyInstance.txt
```

### CLI Features

- 🔵 **Auto-parse Aura credential files** - No manual copying of URIs/passwords
- 🗄️ **Database discovery** - See all your databases with status and metadata
- 🎨 **Rich terminal output** - Beautiful tables, colors, and progress bars
- 📊 **Interactive selection** - Choose databases with arrow keys
- 🚀 **Batch analysis** - Compare all databases at once with `--all-databases`

### Example CLI Output

```
╭──────────────────────────────────────────────────────────────────────────────╮
│ Neo4j Schema Comparison Tool                                                 │
│ Compare your Neo4j database schema against standard models                   │
╰──────────────────────────────────────────────────────────────────────────────╯

╭───────────────────────────── Connection Details ─────────────────────────────╮
│ 🔵 Neo4j Aura Connection                                                     │
│ Instance: My Production Database                                             │
│ Instance ID: 24b2cxxx                                                        │
│ Username: neo4j                                                              │
│ Default Database: neo4j                                                      │
╰──────────────────────────────────────────────────────────────────────────────╯

Available Databases
┌──────────┬────────┬─────────┬─────────┬──────┐
│ Database │ Status │ Role    │ Default │ Type │
├──────────┼────────┼─────────┼─────────┼──────┤
│ neo4j    │ online │ primary │ ✓       │ user │
│ movies   │ online │ primary │         │ user │
│ finance  │ online │ primary │         │ user │
└──────────┴────────┴─────────┴─────────┴──────┘

? Select database to analyze: finance

╭──────────────── 📊 Comparison Summary ────────────────╮
│ Overall Compliance Score: 87.5%                       │
│ Compliance Level: GOOD                                │
│                                                       │
│ Match Statistics:                                     │
│   Nodes: 8/10                                        │
│   Relationships: 5/6                                 │
│   Properties: 23/28                                  │
╰───────────────────────────────────────────────────────╯
```

## 💎 What You Get

### Your Current Schema (Extracted)
```python
from src.compare_models.schemas.client import get_graph_schema

# Extracts everything from your database
current_schema = get_graph_schema()
print(f"Found {len(current_schema.nodes)} node types")
print(f"Found {len(current_schema.relationships)} relationship types")
```

### Neo4j's Official Standard (Auto-fetched)
```python  
from src.compare_models.schemas.standard.transactions import get_standard_schema

# Fetches the latest from Neo4j's documentation
standard_schema = get_standard_schema()
print(f"Standard defines {len(standard_schema.nodes)} node types")
print(f"With {sum(len(n.constraints) for n in standard_schema.nodes)} constraints")
```

### The Comparison Magic ✨

**Your Database:**
```json
{
  "label": "customer",
  "constraints": [],
  "indexes": [
    {
      "type": "FULLTEXT", 
      "properties": ["first_name", "last_name"],
      "name": "customer_name_idx"
    }
  ]
}
```

**Official Standard:**
```json
{
  "label": "Customer",
  "constraints": [
    {
      "type": "NODE_KEY",
      "properties": ["customerId"], 
      "name": "customer_id_key"
    }
  ],
  "indexes": [
    {
      "type": "FULLTEXT",
      "properties": ["firstName", "lastName", "middleName"],
      "name": "customer_name_idx"
    }
  ]
}
```

**Gap Analysis:**
- ❌ Missing NODE_KEY constraint on `customerId`
- ❌ Property names don't match camelCase convention
- ❌ Missing `middleName` in fulltext index
- ✅ Fulltext index concept is correct

## 🏗️ Architecture

### Smart Schema Extraction
- **Multi-label support**: Handles `:Account:Internal` nodes properly
- **Complete constraints**: Extracts NODE_KEY, UNIQUE, and custom constraints
- **All index types**: Property, fulltext, and vector indexes with configuration
- **Structured output**: Clean JSON, not messy strings

### Advanced Similarity Engine
- **6 Similarity Techniques**: Levenshtein, Jaro-Winkler, Fuzzy, Abbreviation, Semantic, Contextual
- **Neo4j-Aligned Abbreviations**: Handles `CUSTNUM` → `customerId` with 95%+ accuracy
- **Adaptive Weighting**: Automatically optimizes based on field characteristics
- **91%+ Compliance Rate**: Battle-tested against Neo4j Transactions Base Model

```python
# Example: The similarity engine in action
from src.compare_models.core.similarity import CompositeSimilarity

similarity = CompositeSimilarity()
result = similarity.calculate("CUSTNUM", "customerId")
# Score: 0.955 (95.5% match!) - Correctly identifies the mapping
```

### Live Standard Sync
```python
# This hits Neo4j's live documentation every time
STANDARD_MODEL_URL = "https://neo4j.com/developer/industry-use-cases/_attachments/transactions-base-model.txt"

# Parses sections 1, 2, and 3 automatically:
# 1. Node Labels and Properties  
# 2. Relationship Types and Properties
# 3. Constraints and Indexes
```

### Clean Architecture
```
src/compare_models/         # Core business logic (pure, no CLI deps)
├── orchestrator.py        # Clean workflow coordination
├── core/                  # Comparison and similarity engine
│   ├── comparator.py     # Schema comparison logic
│   └── similarity/       # Advanced field matching
├── schemas/              # Schema extraction and standards
└── common/               # Shared models

cli/                       # Separate CLI package (all UI logic)
├── main.py               # Rich CLI with Click
├── aura_support.py       # Aura credential parsing
├── database_discovery.py # Database selection
└── rich_formatters.py    # Beautiful output
```

### Professional Output

**Before (typical tools):**
```
"constraints": ["NODE KEY (customerId)"]
"indexes": ["FULLTEXT INDEX (firstName, lastName)"]
```

**After (this tool):**
```json
{
  "constraints": [
    {
      "type": "NODE_KEY",
      "properties": ["customerId"],
      "name": "customer_id_key"
    }
  ],
  "indexes": [
    {
      "type": "FULLTEXT", 
      "properties": ["firstName", "lastName"],
      "name": "customer_name_idx",
      "config": {"analyzer": "standard"}
    }
  ]
}
```

## 📊 Core Components

| Component | Purpose |
|-----------|---------|
| `schemas/client.py` | Extracts your current database schema |
| `schemas/standard/parser.py` | Fetches & parses Neo4j's official model |
| `core/comparator.py` | Identifies gaps and differences |
| `core/reporting.py` | Generates actionable recommendations |

## 🎯 Example Scenarios

### Financial Institution
**Your schema:** Lowercase labels, missing constraints, basic indexes
**Standard schema:** Proper Account/Customer/Transaction hierarchy with comprehensive constraints
**Result:** Clear migration path to regulatory compliance

### E-commerce Platform  
**Your schema:** Custom relationship names, inconsistent properties
**Standard schema:** Standardized customer/account patterns
**Result:** Alignment with Neo4j best practices

## 🔧 Configuration

```python
# .env file
NEO4J_URI="neo4j+s://your-instance.databases.neo4j.io"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="your-password"
NEO4J_DATABASE="your-database"
```

## 📋 CLI Command Reference

### `compare` - Main comparison command
```bash
# Basic usage with Aura file
python cli/main.py compare --aura-file credentials.txt

# Advanced options
python cli/main.py compare \
  --aura-file credentials.txt \
  --database finance \           # Skip interactive selection
  --threshold 0.9 \              # Stricter matching (default: 0.7)
  --json \                       # Include raw JSON output
  --adaptive                     # Use adaptive similarity (default)

# Compare all databases at once
python cli/main.py compare --aura-file creds.txt --all-databases
```

### `import-credentials` - Validate Aura files
```bash
# Test your Aura credentials
python cli/main.py import-credentials ~/Downloads/Neo4j-Instance.txt
```

### `list-databases` - Explore available databases
```bash
# Show all databases with metadata
python cli/main.py list-databases --aura-file credentials.txt
```

## 🎉 The Bottom Line

Stop building in the dark. This tool shows you:
- ✅ **What you have** (comprehensive schema extraction)
- ✅ **What you should have** (official Neo4j standards)  
- ✅ **How to get there** (actionable gap analysis)
- ✅ **Beautiful CLI** (drag-and-drop Aura files, interactive selection)
- ✅ **Smart matching** (handles abbreviations like CUSTNUM → customerId)

Built on **official Neo4j documentation** that updates automatically. No guesswork, no outdated standards.

**Ready to level up your graph database?** 🚀

---

💡 **Pro tip**: Run this before any major schema changes to ensure you're building toward the standard, not away from it.