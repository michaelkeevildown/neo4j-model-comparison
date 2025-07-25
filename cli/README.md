# Neo4j Schema Comparison CLI

A beautiful, feature-rich command-line interface for comparing Neo4j database schemas against standard models, with special support for Neo4j Aura credential files and interactive database selection.

## Features

🔵 **Neo4j Aura Support**
- Drag-and-drop credential file import
- Automatic parsing of Aura `.txt` files
- Connection validation and testing

🗄️ **Database Discovery**
- Automatic discovery of all databases
- Interactive database selection
- Support for multi-database comparisons

📊 **Rich Analysis**
- Comprehensive schema comparison
- Detailed compliance reports
- Categorized recommendations (Critical, Important, Style)

✨ **Beautiful Output**
- Rich terminal formatting with colors and tables
- Progress bars for long operations
- Interactive prompts and confirmations

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Basic Usage with Aura Credentials
```bash
# Interactive comparison with database selection
python cli/main.py compare --aura-file /path/to/credentials.txt

# Compare specific database
python cli/main.py compare --aura-file /path/to/credentials.txt --database mydb

# Compare all databases
python cli/main.py compare --aura-file /path/to/credentials.txt --all-databases
```

### 3. Using Direct Connection
```bash
python cli/main.py compare --uri neo4j://localhost:7687 --username neo4j --password password
```

## Commands

### `compare`
Main command for schema comparison with comprehensive options:

```bash
python cli/main.py compare [OPTIONS]
```

**Options:**
- `--aura-file PATH` - Neo4j Aura credentials file
- `--uri TEXT` - Neo4j connection URI
- `--username TEXT` - Neo4j username  
- `--password TEXT` - Neo4j password
- `--database TEXT` - Specific database to analyze
- `--standard transactions` - Standard model to compare against
- `--threshold FLOAT` - Similarity threshold (0.0-1.0)
- `--adaptive/--fixed` - Similarity weighting mode
- `--json` - Include raw JSON output
- `--all-databases` - Compare all non-system databases
- `--list-databases` - List databases and exit

### `import-credentials`
Import and validate Aura credential files:

```bash
python cli/main.py import-credentials /path/to/credentials.txt
```

### `list-databases`
List all available databases:

```bash
python cli/main.py list-databases --aura-file /path/to/credentials.txt
```

## Neo4j Aura Integration

The CLI provides seamless integration with Neo4j Aura:

1. **Download** your credentials file from Neo4j Aura Console
2. **Drag and drop** or specify the file path with `--aura-file`
3. **Automatic parsing** of connection details and instance information
4. **Connection validation** with helpful error messages

### Example Aura Workflow
```bash
# Test your Aura credentials
python cli/main.py import-credentials ~/Downloads/Neo4j-MyInstance.txt

# List available databases
python cli/main.py list-databases --aura-file ~/Downloads/Neo4j-MyInstance.txt

# Run comparison with interactive database selection
python cli/main.py compare --aura-file ~/Downloads/Neo4j-MyInstance.txt
```

## Output Examples

### Database Selection
```
Available Databases
┌──────────┬────────┬─────────┬─────────┬──────┐
│ Database │ Status │ Role    │ Default │ Type │
├──────────┼────────┼─────────┼─────────┼──────┤
│ neo4j    │ online │ primary │ ✓       │ user │
│ movies   │ online │ primary │         │ user │
│ finance  │ online │ primary │         │ user │
└──────────┴────────┴─────────┴─────────┴──────┘
```

### Comparison Results
```
╭──────────────── Comparison Summary ────────────────╮
│ 📊 Overall Compliance Score: 87.5%                │
│ Compliance Level: GOOD                             │
│                                                    │
│ Match Statistics:                                  │
│   Nodes: 8/10                                      │
│   Relationships: 5/6                               │
│   Properties: 23/28                                │
╰────────────────────────────────────────────────────╯
```

## Advanced Usage

### Custom Similarity Settings
```bash
# Strict matching (higher threshold)
python cli/main.py compare --aura-file creds.txt --threshold 0.9

# Fixed weighting instead of adaptive
python cli/main.py compare --aura-file creds.txt --fixed

# Include raw JSON output
python cli/main.py compare --aura-file creds.txt --json
```

### Batch Analysis
```bash
# Compare all databases in one command
python cli/main.py compare --aura-file creds.txt --all-databases
```

## Architecture

The CLI is built with clean separation of concerns:

- **`main.py`** - Click-based CLI interface and command routing
- **`aura_support.py`** - Neo4j Aura credential file parsing
- **`database_discovery.py`** - Database discovery and connection management
- **`rich_formatters.py`** - Beautiful terminal output formatting

The CLI connects to the core comparison engine through the orchestration layer, keeping all CLI-specific code separate from the business logic.

## Error Handling

The CLI provides helpful error messages and suggestions:

- **Connection errors** - Clear messages about connectivity issues
- **Credential parsing** - Detailed validation errors for malformed files
- **Database access** - Informative messages about permission issues
- **File not found** - Suggestions for locating credential files

## Future Enhancements

- Connection profile management (save/load named profiles)
- Export results to HTML/PDF reports
- Batch processing multiple credential files
- Custom standard model definitions
- REST API integration for web interfaces