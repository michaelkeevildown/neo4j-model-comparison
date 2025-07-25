#!/usr/bin/env python3
"""
Neo4j Schema Comparison CLI

A rich command-line interface for comparing Neo4j database schemas
against standard models with support for Aura credential files and
interactive database selection.
"""

import sys
import os
import tempfile
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

# Add the src directory to Python path so we can import the core modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aura_support import (
    parse_aura_credentials_file, 
    AuraCredentialError,
    extract_connection_info,
    get_connection_instructions,
    suggest_credential_files
)
from database_discovery import DatabaseDiscovery, DatabaseDiscoveryError, get_recommended_database
from rich_formatters import (
    console, print_header, print_success, print_warning, print_error, print_info,
    format_credentials_info, format_connection_instructions, format_database_table,
    prompt_database_selection, prompt_confirm, display_schema_comparison_results,
    show_welcome_message, show_completion_message, format_progress_context
)

# Import core comparison functionality
from compare_models.orchestrator import SchemaComparator
from compare_models.common.config import Neo4jSettings


@click.group()
@click.version_option(version="1.0.0", prog_name="neo4j-compare")
def cli():
    """
    Neo4j Schema Comparison Tool
    
    Compare your Neo4j database schemas against standard models with 
    beautiful terminal output and interactive features.
    """
    pass


@cli.command()
@click.option(
    '--aura-file', 
    type=click.Path(exists=True, path_type=Path),
    help='Path to Neo4j Aura credentials file'
)
@click.option(
    '--uri',
    help='Neo4j connection URI (alternative to --aura-file)'
)
@click.option(
    '--username',
    help='Neo4j username (alternative to --aura-file)'
)
@click.option(
    '--password',
    help='Neo4j password (alternative to --aura-file)'
)
@click.option(
    '--database',
    help='Specific database to analyze (skips interactive selection)'
)
@click.option(
    '--standard',
    default='transactions',
    help='Standard model to compare against',
    type=click.Choice(['transactions'], case_sensitive=False)
)
@click.option(
    '--threshold',
    default=0.7,
    type=click.FloatRange(0.0, 1.0),
    help='Similarity threshold for field matching'
)
@click.option(
    '--adaptive/--fixed',
    default=True,
    help='Use adaptive similarity weighting'
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='Include raw JSON output'
)
@click.option(
    '--all-databases',
    is_flag=True,
    help='Compare all non-system databases'
)
@click.option(
    '--list-databases',
    is_flag=True,
    help='List available databases and exit'
)
def compare(
    aura_file: Optional[Path],
    uri: Optional[str],
    username: Optional[str], 
    password: Optional[str],
    database: Optional[str],
    standard: str,
    threshold: float,
    adaptive: bool,
    output_json: bool,
    all_databases: bool,
    list_databases: bool
):
    """
    Compare Neo4j database schema against standard models.
    
    This command connects to your Neo4j database, discovers available databases,
    and performs comprehensive schema comparison with detailed recommendations.
    """
    show_welcome_message()
    
    # Handle credential sources
    connection_info = None
    
    if aura_file:
        connection_info = _load_aura_credentials(aura_file)
        if not connection_info:
            return
    elif uri and username and password:
        connection_info = {
            'NEO4J_URI': uri,
            'NEO4J_USERNAME': username,
            'NEO4J_PASSWORD': password,
            'NEO4J_DATABASE': database or 'neo4j'
        }
    else:
        # Try to suggest credential files
        suggested_files = suggest_credential_files(".")
        if suggested_files:
            print_info("Found potential credential files:")
            for file_path in suggested_files[:3]:  # Show up to 3 suggestions
                console.print(f"  • {file_path}")
            console.print()
            
        print_error("Please provide connection credentials using one of these options:")
        console.print("  • --aura-file /path/to/credentials.txt")
        console.print("  • --uri neo4j://... --username ... --password ...")
        console.print("  • Set NEO4J_* environment variables")
        return
    
    # Discover databases
    try:
        with format_progress_context() as progress:
            task = progress.add_task("Connecting to Neo4j...", total=None)
            
            with DatabaseDiscovery(
                connection_info['NEO4J_URI'],
                connection_info['NEO4J_USERNAME'],
                connection_info['NEO4J_PASSWORD']
            ) as discovery:
                progress.update(task, description="Discovering databases...")
                databases = discovery.discover_databases(include_system=False)
        
        print_success(f"Connected successfully! Found {len(databases)} database(s)")
        
        # Handle list-databases option
        if list_databases:
            _display_database_list(databases)
            return
        
        # Handle database selection
        if all_databases:
            selected_databases = [db.name for db in databases if not db.is_system]
            if not selected_databases:
                print_error("No non-system databases found")
                return
        elif database:
            # Validate specified database exists
            available_names = [db.name for db in databases]
            if database not in available_names:
                print_error(f"Database '{database}' not found. Available: {', '.join(available_names)}")
                return
            selected_databases = [database]
        else:
            # Interactive selection
            selected_db = prompt_database_selection(databases)
            if not selected_db:
                return
            selected_databases = [selected_db]
        
        # Perform comparisons
        for db_name in selected_databases:
            _perform_comparison(
                connection_info, db_name, standard, threshold, adaptive, output_json
            )
            
            if len(selected_databases) > 1:
                console.print("\n" + "="*50 + "\n")
    
    except DatabaseDiscoveryError as e:
        print_error(f"Database discovery failed: {e}")
        return
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return


@cli.command()
@click.argument('credential_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--profile-name',
    help='Name for the saved connection profile'
)
def import_credentials(credential_file: Path, profile_name: Optional[str]):
    """
    Import and validate Neo4j Aura credential files.
    
    This command parses Aura credential files, validates the connection,
    and optionally saves them as reusable profiles.
    """
    show_welcome_message()
    
    try:
        # Parse credentials
        credentials = parse_aura_credentials_file(str(credential_file))
        
        # Display credential info
        cred_panel = format_credentials_info(credentials)
        console.print(cred_panel)
        
        # Show instructions if available
        instructions = get_connection_instructions(credentials)
        if instructions:
            instruction_panel = format_connection_instructions(instructions)
            console.print(instruction_panel)
        
        # Test connection
        connection_info = extract_connection_info(credentials)
        
        with format_progress_context() as progress:
            task = progress.add_task("Testing connection...", total=None)
            
            try:
                with DatabaseDiscovery(
                    connection_info['NEO4J_URI'],
                    connection_info['NEO4J_USERNAME'],
                    connection_info['NEO4J_PASSWORD']
                ) as discovery:
                    databases = discovery.discover_databases()
                
                print_success("Connection test successful!")
                print_info(f"Found {len(databases)} database(s)")
                
                # Optionally save as profile
                if profile_name:
                    # TODO: Implement profile saving
                    print_info(f"Profile saving not yet implemented. Would save as '{profile_name}'")
                
            except Exception as e:
                print_error(f"Connection test failed: {e}")
                return
    
    except AuraCredentialError as e:
        print_error(f"Credential parsing failed: {e}")
        return
    except Exception as e:
        print_error(f"Import failed: {e}")
        return


@cli.command()
@click.option(
    '--aura-file',
    type=click.Path(exists=True, path_type=Path),
    help='Path to Neo4j Aura credentials file'
)
@click.option(
    '--uri',
    help='Neo4j connection URI'
)
@click.option(
    '--username',
    help='Neo4j username'
)
@click.option(
    '--password',
    help='Neo4j password'
)
def list_databases(aura_file: Optional[Path], uri: Optional[str], username: Optional[str], password: Optional[str]):
    """
    List all available databases in a Neo4j instance.
    
    This command connects to Neo4j and displays all available databases
    with their status and metadata.
    """
    show_welcome_message()
    
    # Handle credentials
    connection_info = None
    
    if aura_file:
        connection_info = _load_aura_credentials(aura_file)
        if not connection_info:
            return
    elif uri and username and password:
        connection_info = {
            'NEO4J_URI': uri,
            'NEO4J_USERNAME': username,
            'NEO4J_PASSWORD': password,
            'NEO4J_DATABASE': 'neo4j'
        }
    else:
        print_error("Please provide connection credentials")
        return
    
    try:
        with format_progress_context() as progress:
            task = progress.add_task("Discovering databases...", total=None)
            
            with DatabaseDiscovery(
                connection_info['NEO4J_URI'],
                connection_info['NEO4J_USERNAME'],
                connection_info['NEO4J_PASSWORD']
            ) as discovery:
                databases = discovery.discover_databases(include_system=True)
        
        _display_database_list(databases)
        
    except DatabaseDiscoveryError as e:
        print_error(f"Database discovery failed: {e}")
    except Exception as e:
        print_error(f"Error: {e}")


def _load_aura_credentials(aura_file: Path) -> Optional[dict]:
    """Load and validate Aura credentials from file."""
    try:
        credentials = parse_aura_credentials_file(str(aura_file))
        
        # Display credential info
        cred_panel = format_credentials_info(credentials)
        console.print(cred_panel)
        
        # Show instructions if available
        instructions = get_connection_instructions(credentials)
        if instructions:
            instruction_panel = format_connection_instructions(instructions)
            console.print(instruction_panel)
        
        return extract_connection_info(credentials)
        
    except AuraCredentialError as e:
        print_error(f"Failed to parse Aura credentials: {e}")
        return None


def _display_database_list(databases):
    """Display formatted list of databases."""
    if not databases:
        print_warning("No databases found")
        return
    
    # Display table
    table = format_database_table(databases)
    console.print(table)
    
    # Show recommendation
    recommended = get_recommended_database(databases)
    if recommended:
        print_info(f"Recommended for analysis: {recommended.name}")


def _perform_comparison(connection_info: dict, database_name: str, standard: str, threshold: float, adaptive: bool, output_json: bool):
    """Perform schema comparison for a specific database."""
    print_header(f"Analyzing Database: {database_name}")
    
    # Set up environment for the orchestrator
    os.environ.update(connection_info)
    os.environ['NEO4J_DATABASE'] = database_name
    
    try:
        with format_progress_context() as progress:
            task = progress.add_task("Extracting schema...", total=None)
            
            # Create comparator
            comparator = SchemaComparator()
            
            progress.update(task, description="Comparing against standard...")
            
            # Perform comparison
            results = comparator.compare_database_to_standard(
                standard_name=standard,
                similarity_threshold=threshold,
                use_adaptive=adaptive
            )
        
        # Display results
        display_schema_comparison_results(results, show_json=output_json)
        
        # Show completion message
        summary = results.get('summary', {})
        compliance_score = summary.get('overall_compliance_score', 0)
        show_completion_message(database_name, compliance_score)
        
    except Exception as e:
        print_error(f"Comparison failed for database '{database_name}': {e}")
        console.print_exception()


if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        print_info("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        console.print_exception()
        sys.exit(1)