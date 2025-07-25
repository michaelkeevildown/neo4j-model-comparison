"""
Rich terminal formatting utilities for the CLI.

This module provides beautiful terminal output formatting using the Rich library,
including tables, progress bars, status messages, and formatted comparison results.
"""

import json
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.tree import Tree
from rich.columns import Columns
from rich.prompt import Prompt, Confirm
from rich.pretty import Pretty
from database_discovery import DatabaseInfo


# Global console instance
console = Console()


class StatusIndicators:
    """Status indicator emojis and symbols."""
    SUCCESS = "✅"
    WARNING = "⚠️ "
    ERROR = "❌"
    INFO = "ℹ️ "
    LOADING = "🔄"
    DATABASE = "🗄️ "
    NEO4J = "🔵"
    ANALYSIS = "🔍"
    RESULTS = "📊"
    RECOMMENDATIONS = "💡"
    CRITICAL = "🚨"
    ARROW = "→"


def print_header(title: str, subtitle: Optional[str] = None):
    """
    Print a formatted header.
    
    Args:
        title: Main title text
        subtitle: Optional subtitle text
    """
    text = Text(title, style="bold blue")
    if subtitle:
        text.append(f"\n{subtitle}", style="dim")
    
    panel = Panel(text, border_style="blue")
    console.print(panel)


def print_success(message: str):
    """Print a success message."""
    console.print(f"{StatusIndicators.SUCCESS} {message}", style="green")


def print_warning(message: str):
    """Print a warning message."""
    console.print(f"{StatusIndicators.WARNING} {message}", style="yellow")


def print_error(message: str):
    """Print an error message."""
    console.print(f"{StatusIndicators.ERROR} {message}", style="red")


def print_info(message: str):
    """Print an info message."""
    console.print(f"{StatusIndicators.INFO} {message}", style="blue")


def format_database_table(databases: List[DatabaseInfo]) -> Table:
    """
    Format a list of databases as a rich table.
    
    Args:
        databases: List of database information
        
    Returns:
        Rich Table object
    """
    table = Table(title="Available Databases")
    
    table.add_column("Database", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Role", style="blue") 
    table.add_column("Default", justify="center")
    table.add_column("Type", style="dim")
    
    for db in databases:
        # Format status with appropriate color
        if db.status.lower() == "online":
            status = f"[green]{db.status}[/green]"
        elif db.status.lower() in ["offline", "failed"]:
            status = f"[red]{db.status}[/red]"
        else:
            status = f"[yellow]{db.status}[/yellow]"
        
        # Format default indicator
        default_indicator = "✓" if db.is_default else ""
        
        # Format type
        db_type = "system" if db.is_system else "user"
        
        table.add_row(
            db.name,
            status,
            db.role,
            default_indicator,
            db_type
        )
    
    return table


def format_credentials_info(credentials) -> Panel:
    """
    Format Aura credentials information as a panel.
    
    Args:
        credentials: AuraCredentials object
        
    Returns:
        Rich Panel with credential information
    """
    info_text = Text()
    info_text.append(f"{StatusIndicators.NEO4J} Neo4j Aura Connection\n", style="bold blue")
    
    if credentials.instance_name:
        info_text.append(f"Instance: {credentials.instance_name}\n", style="cyan")
    
    if credentials.instance_id:
        info_text.append(f"Instance ID: {credentials.instance_id}\n", style="dim")
    
    # Extract hostname for display
    try:
        if 'databases.neo4j.io' in credentials.uri:
            hostname = credentials.uri.split('//')[1].split('.')[0]
            info_text.append(f"Database: {hostname}\n", style="green")
    except (IndexError, AttributeError):
        pass
    
    info_text.append(f"Username: {credentials.username}\n", style="blue")
    info_text.append(f"Default Database: {credentials.database}", style="blue")
    
    return Panel(info_text, border_style="blue", title="Connection Details")


def format_connection_instructions(instructions: List[str]) -> Optional[Panel]:
    """
    Format connection instructions as a panel.
    
    Args:
        instructions: List of instruction strings
        
    Returns:
        Rich Panel with instructions or None if no instructions
    """
    if not instructions:
        return None
    
    instruction_text = Text()
    for instruction in instructions:
        if "wait" in instruction.lower() and "second" in instruction.lower():
            instruction_text.append(f"⏰ {instruction}\n", style="yellow")
        else:
            instruction_text.append(f"• {instruction}\n", style="dim")
    
    return Panel(instruction_text, border_style="yellow", title="Important Notes")


def format_comparison_summary(results: Dict[str, Any]) -> Panel:
    """
    Format comparison results summary as a panel.
    
    Args:
        results: Comparison results dictionary
        
    Returns:
        Rich Panel with summary information
    """
    summary = results.get('summary', {})
    
    # Create summary text
    summary_text = Text()
    
    # Overall score
    score = summary.get('overall_compliance_score', 0)
    score_color = "green" if score >= 0.8 else "yellow" if score >= 0.6 else "red"
    summary_text.append(f"Overall Compliance Score: ", style="bold")
    summary_text.append(f"{score:.1%}\n", style=f"bold {score_color}")
    
    # Compliance level
    level = results.get('compliance_level', 'unknown').upper()
    level_color = {
        'EXCELLENT': 'green',
        'GOOD': 'blue', 
        'FAIR': 'yellow',
        'POOR': 'orange',
        'CRITICAL': 'red'
    }.get(level, 'white')
    
    summary_text.append(f"Compliance Level: ", style="bold")
    summary_text.append(f"{level}\n\n", style=f"bold {level_color}")
    
    # Match statistics
    summary_text.append("Match Statistics:\n", style="bold")
    summary_text.append(f"  Nodes: {summary.get('matched_nodes', 0)}/{summary.get('total_customer_nodes', 0)}\n")
    summary_text.append(f"  Relationships: {summary.get('matched_relationships', 0)}/{summary.get('total_customer_relationships', 0)}\n")
    summary_text.append(f"  Properties: {summary.get('matched_properties', 0)}/{summary.get('total_customer_properties', 0)}")
    
    return Panel(summary_text, border_style="green", title=f"{StatusIndicators.RESULTS} Comparison Summary")


def format_recommendations_table(recommendations: Dict[str, List]) -> Table:
    """
    Format recommendations as a rich table.
    
    Args:
        recommendations: Categorized recommendations dictionary
        
    Returns:
        Rich Table with recommendations
    """
    table = Table(title="Compliance Recommendations")
    
    table.add_column("Priority", style="bold", width=10)
    table.add_column("Issue", style="cyan", width=50)
    table.add_column("Suggestion", style="green", width=60)
    
    # Add critical issues
    for rec in recommendations.get('critical', []):
        table.add_row(
            f"[red]{StatusIndicators.CRITICAL} CRITICAL[/red]",
            rec.get('message', ''),
            rec.get('suggestion', '')
        )
    
    # Add important issues
    for rec in recommendations.get('important', []):
        table.add_row(
            f"[yellow]{StatusIndicators.WARNING} IMPORTANT[/yellow]",
            rec.get('message', ''),
            rec.get('suggestion', '')
        )
    
    # Add style recommendations
    for rec in recommendations.get('style', []):
        table.add_row(
            f"[blue]{StatusIndicators.INFO} STYLE[/blue]",
            rec.get('message', ''),
            rec.get('suggestion', '')
        )
    
    return table


def format_node_renames_table(renames: List[Dict]) -> Table:
    """
    Format node label renames as a rich table.
    
    Args:
        renames: List of node rename recommendations
        
    Returns:
        Rich Table with node renames
    """
    table = Table(title="Node Label Changes Required")
    
    table.add_column("Current Label", style="cyan", width=25)
    table.add_column("", style="dim", width=3)
    table.add_column("Standard Label", style="green", width=25)
    table.add_column("Priority", style="bold", width=10)
    table.add_column("Cypher Command", style="blue", width=60)
    
    for rename in renames:
        priority_color = {
            'CRITICAL': 'red',
            'HIGH': 'yellow',
            'MEDIUM': 'blue',
            'LOW': 'dim'
        }.get(rename['priority'], 'white')
        
        table.add_row(
            rename['current_label'],
            StatusIndicators.ARROW,
            rename['standard_label'],
            f"[{priority_color}]{rename['priority']}[/{priority_color}]",
            rename['cypher_command']
        )
    
    return table


def format_relationship_renames_table(renames: List[Dict]) -> Table:
    """
    Format relationship type renames as a rich table.
    
    Args:
        renames: List of relationship rename recommendations
        
    Returns:
        Rich Table with relationship renames
    """
    table = Table(title="Relationship Type Changes Required")
    
    table.add_column("Current Type", style="cyan", width=25)
    table.add_column("", style="dim", width=3)
    table.add_column("Standard Type", style="green", width=25)
    table.add_column("Priority", style="bold", width=10)
    table.add_column("Cypher Command", style="blue", width=60)
    
    for rename in renames:
        priority_color = {
            'CRITICAL': 'red',
            'HIGH': 'yellow',
            'MEDIUM': 'blue',
            'LOW': 'dim'
        }.get(rename['priority'], 'white')
        
        # Truncate long Cypher commands for display
        cypher_lines = rename['cypher_command'].split('\n')
        cypher_display = cypher_lines[0] if cypher_lines else rename['cypher_command']
        if len(cypher_lines) > 1:
            cypher_display += " ..."
        
        table.add_row(
            rename['current_type'],
            StatusIndicators.ARROW,
            rename['standard_type'],
            f"[{priority_color}]{rename['priority']}[/{priority_color}]",
            cypher_display
        )
    
    return table


def format_property_renames_table(renames: List[Dict]) -> Table:
    """
    Format property renames as a rich table.
    
    Args:
        renames: List of property rename recommendations
        
    Returns:
        Rich Table with property renames
    """
    table = Table(title="Property Name Changes Required")
    
    table.add_column("Element Type", style="dim", width=12)
    table.add_column("Element Name", style="cyan", width=20)
    table.add_column("Current Property", style="red", width=25)
    table.add_column("", style="dim", width=3)
    table.add_column("Standard Property", style="green", width=25)
    table.add_column("Priority", style="bold", width=10)
    
    for rename in renames:
        priority_color = {
            'CRITICAL': 'red',
            'HIGH': 'yellow',
            'MEDIUM': 'blue',
            'LOW': 'dim'
        }.get(rename['priority'], 'white')
        
        table.add_row(
            rename['element_type'],
            rename['element_name'],
            rename['current_property'],
            StatusIndicators.ARROW,
            rename['standard_property'],
            f"[{priority_color}]{rename['priority']}[/{priority_color}]"
        )
    
    return table


def format_missing_indexes_table(indexes: List[Dict]) -> Table:
    """
    Format missing indexes as a rich table.
    
    Args:
        indexes: List of missing index recommendations
        
    Returns:
        Rich Table with missing indexes
    """
    table = Table(title="Missing Indexes")
    
    table.add_column("Element Label", style="cyan", width=25)
    table.add_column("Index Type", style="blue", width=15)
    table.add_column("Properties", style="green", width=30)
    table.add_column("Priority", style="bold", width=10)
    table.add_column("Cypher Command", style="blue", width=50)
    
    for index in indexes:
        priority_color = {
            'CRITICAL': 'red',
            'HIGH': 'yellow',
            'MEDIUM': 'blue',
            'LOW': 'dim'
        }.get(index['priority'], 'white')
        
        properties_display = ', '.join(index['properties'])
        
        table.add_row(
            index['element_label'],
            index['index_type'],
            properties_display,
            f"[{priority_color}]{index['priority']}[/{priority_color}]",
            index['cypher_command']
        )
    
    return table


def format_data_type_mismatches_table(mismatches: List[Dict]) -> Table:
    """
    Format data type mismatches as a rich table.
    
    Args:
        mismatches: List of data type mismatch recommendations
        
    Returns:
        Rich Table with data type mismatches
    """
    table = Table(title="Data Type Mismatches")
    
    table.add_column("Element Type", style="dim", width=12)
    table.add_column("Element.Property", style="cyan", width=35)
    table.add_column("Current Type", style="red", width=20)
    table.add_column("", style="dim", width=3)
    table.add_column("Expected Type", style="green", width=20)
    table.add_column("Priority", style="bold", width=10)
    
    for mismatch in mismatches:
        priority_color = {
            'CRITICAL': 'red',
            'HIGH': 'yellow',
            'MEDIUM': 'blue',
            'LOW': 'dim'
        }.get(mismatch['priority'], 'white')
        
        current_types = ', '.join(mismatch['current_types'])
        expected_types = ', '.join(mismatch['expected_types'])
        
        table.add_row(
            mismatch['element_type'],
            mismatch['element_property'],
            current_types,
            StatusIndicators.ARROW,
            expected_types,
            f"[{priority_color}]{mismatch['priority']}[/{priority_color}]"
        )
    
    return table


def format_progress_context():
    """
    Create a progress context for long-running operations.
    
    Returns:
        Rich Progress context manager
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    )


def prompt_database_selection(databases: List[DatabaseInfo]) -> Optional[str]:
    """
    Prompt user to select a database interactively.
    
    Args:
        databases: List of available databases
        
    Returns:
        Selected database name or None if cancelled
    """
    if not databases:
        print_error("No databases available for selection")
        return None
    
    # Filter to selectable databases
    selectable = [db for db in databases if not db.is_system and db.status.lower() == "online"]
    
    if not selectable:
        print_error("No selectable databases found")
        return None
    
    # Display table
    table = format_database_table(selectable)
    console.print(table)
    
    # Create choices
    choices = []
    display_choices = []
    
    for i, db in enumerate(selectable, 1):
        choices.append(str(i))
        display_name = db.name
        if db.is_default:
            display_name += " (recommended)"
        display_choices.append(f"{i}. {display_name}")
    
    # Show choices
    console.print("\nSelect a database:")
    for choice in display_choices:
        console.print(f"  {choice}")
    
    # Get user input
    try:
        choice = Prompt.ask(
            "Enter choice",
            choices=choices,
            default="1"
        )
        
        selected_db = selectable[int(choice) - 1]
        print_success(f"Selected database: {selected_db.name}")
        return selected_db.name
        
    except (ValueError, IndexError, KeyboardInterrupt):
        print_info("Selection cancelled")
        return None


def prompt_confirm(message: str, default: bool = True) -> bool:
    """
    Prompt user for confirmation.
    
    Args:
        message: Message to display
        default: Default choice
        
    Returns:
        User's choice
    """
    return Confirm.ask(message, default=default)


def format_json_output(data: Dict[str, Any], title: str = "Results") -> None:
    """
    Format and display JSON data with syntax highlighting.
    
    Args:
        data: Data to display as JSON
        title: Title for the output
    """
    json_text = json.dumps(data, indent=2)
    panel = Panel(Pretty(json_text), border_style="dim", title=title)
    console.print(panel)


def display_schema_comparison_results(results: Dict[str, Any], show_json: bool = False):
    """
    Display comprehensive schema comparison results.
    
    Args:
        results: Comparison results dictionary
        show_json: Whether to show raw JSON output
    """
    # Summary panel
    summary_panel = format_comparison_summary(results)
    console.print(summary_panel)
    console.print()
    
    # Display new categorized recommendations by type if available
    if 'recommendations_by_type' in results:
        recs_by_type = results['recommendations_by_type']
        
        # Node renames
        if recs_by_type.get('node_renames'):
            table = format_node_renames_table(recs_by_type['node_renames'])
            console.print(table)
            console.print()
        
        # Relationship renames
        if recs_by_type.get('relationship_renames'):
            table = format_relationship_renames_table(recs_by_type['relationship_renames'])
            console.print(table)
            console.print()
        
        # Property renames
        if recs_by_type.get('property_renames'):
            table = format_property_renames_table(recs_by_type['property_renames'])
            console.print(table)
            console.print()
        
        # Missing indexes
        if recs_by_type.get('missing_indexes'):
            table = format_missing_indexes_table(recs_by_type['missing_indexes'])
            console.print(table)
            console.print()
        
        # Data type mismatches
        if recs_by_type.get('data_type_mismatches'):
            table = format_data_type_mismatches_table(recs_by_type['data_type_mismatches'])
            console.print(table)
            console.print()
    
    # Fall back to old-style recommendations if new format not available
    elif 'categorized_recommendations' in results:
        recommendations = results['categorized_recommendations']
        if any(recommendations.values()):  # If there are any recommendations
            rec_table = format_recommendations_table(recommendations)
            console.print(rec_table)
            console.print()
    
    # Raw JSON output if requested
    if show_json:
        format_json_output(results, "Raw Comparison Results")


def show_welcome_message():
    """Display welcome message."""
    welcome_text = Text()
    welcome_text.append("Neo4j Schema Comparison Tool", style="bold blue")
    welcome_text.append("\nCompare your Neo4j database schema against standard models", style="dim")
    
    panel = Panel(welcome_text, border_style="blue")
    console.print(panel)
    console.print()


def show_completion_message(database_name: str, compliance_score: float):
    """
    Show completion message with results summary.
    
    Args:
        database_name: Name of analyzed database
        compliance_score: Overall compliance score
    """
    score_color = "green" if compliance_score >= 0.8 else "yellow" if compliance_score >= 0.6 else "red"
    
    completion_text = Text()
    completion_text.append(f"{StatusIndicators.SUCCESS} Analysis Complete!\n\n", style="bold green")
    completion_text.append(f"Database: {database_name}\n", style="cyan")
    completion_text.append(f"Compliance Score: ", style="bold")
    completion_text.append(f"{compliance_score:.1%}", style=f"bold {score_color}")
    
    panel = Panel(completion_text, border_style="green", title="Results Summary")
    console.print(panel)