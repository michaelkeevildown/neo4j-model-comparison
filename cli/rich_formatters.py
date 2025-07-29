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
from rich.syntax import Syntax
from rich.markdown import Markdown
try:
    from database_discovery import DatabaseInfo
except ImportError:
    DatabaseInfo = None


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
    
    table.add_column("Current Label", style="bright_yellow", width=25)
    table.add_column("", style="dim", width=3)
    table.add_column("Standard Label", style="bright_blue", width=25)
    table.add_column("Priority", style="bold", width=10)
    table.add_column("Cypher Command", style="bright_magenta", width=60)
    
    for rename in renames:
        priority_color = {
            'CRITICAL': 'bright_red',
            'HIGH': 'bright_yellow',
            'MEDIUM': 'bright_cyan',
            'LOW': 'bright_white'
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
    
    table.add_column("#", style="bright_white", width=3)
    table.add_column("Current Type", style="bright_yellow", width=25)
    table.add_column("", style="dim", width=3)
    table.add_column("Standard Type", style="bright_blue", width=25)
    table.add_column("Priority", style="bold", width=10)
    
    for i, rename in enumerate(renames, 1):
        priority_color = {
            'CRITICAL': 'bright_red',
            'HIGH': 'bright_yellow',
            'MEDIUM': 'bright_cyan',
            'LOW': 'bright_white'
        }.get(rename['priority'], 'white')
        
        table.add_row(
            str(i),
            rename['current_type'],
            StatusIndicators.ARROW,
            rename['standard_type'],
            f"[{priority_color}]{rename['priority']}[/{priority_color}]"
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
    
    table.add_column("Element", style="bright_white", width=10)
    table.add_column("Name", style="bright_cyan", width=15)
    table.add_column("Current", style="bright_yellow", width=18)
    table.add_column("", style="dim", width=3)
    table.add_column("Standard", style="bright_blue", width=18)
    table.add_column("Priority", style="bold", width=8)
    table.add_column("Cypher Command", style="bright_magenta", width=90)
    
    for rename in renames:
        priority_color = {
            'CRITICAL': 'bright_red',
            'HIGH': 'bright_yellow',
            'MEDIUM': 'bright_cyan',
            'LOW': 'bright_white'
        }.get(rename['priority'], 'white')
        
        priority_display = rename['priority']
        if len(priority_display) > 6:
            priority_display = priority_display[:6]
        
        table.add_row(
            rename['element_type'],
            rename['element_name'],
            rename['current_property'],
            StatusIndicators.ARROW,
            rename['standard_property'],
            f"[{priority_color}]{priority_display}[/{priority_color}]",
            rename.get('cypher_command', '')
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
    # Create table with reference numbers for commands
    table = Table(title="Missing Indexes (Execute After Node Renames)", show_lines=True)
    
    table.add_column("#", style="bright_white", width=3)
    table.add_column("Index Type", style="bright_cyan", width=10)
    table.add_column("Label", style="bright_blue", width=15)
    table.add_column("Properties", style="bright_magenta", no_wrap=False)
    table.add_column("Priority", style="bold", width=8)
    
    for i, index in enumerate(indexes, 1):
        priority_color = {
            'CRITICAL': 'red',
            'HIGH': 'yellow',
            'MEDIUM': 'blue',
            'LOW': 'dim'
        }.get(index['priority'], 'white')
        
        table.add_row(
            str(i),
            index['index_type'],
            index['element_label'],
            ', '.join(index['properties']),
            f"[{priority_color}]{index['priority']}[/{priority_color}]"
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
    
    table.add_column("Element Type", style="bright_white", width=12)
    table.add_column("Element.Property", style="bright_cyan", width=35)
    table.add_column("Current Type", style="bright_yellow", width=20)
    table.add_column("", style="dim", width=3)
    table.add_column("Expected Type", style="bright_blue", width=20)
    table.add_column("Priority", style="bold", width=10)
    
    for mismatch in mismatches:
        priority_color = {
            'CRITICAL': 'bright_red',
            'HIGH': 'bright_yellow',
            'MEDIUM': 'bright_cyan',
            'LOW': 'bright_white'
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


def format_entity_centric_node(node_data: Dict[str, Any]) -> Panel:
    """
    Format a single node in entity-centric view.
    
    Args:
        node_data: Node information from entity-centric formatter
        
    Returns:
        Rich Panel with node details
    """
    tree = Tree(f"[bold]🔍 NODE: {node_data['source']['label']}[/bold]")
    
    # Match information
    if node_data.get('match'):
        match = node_data['match']
        match_color = {
            'exact': 'green',
            'strong': 'bright_green',
            'moderate': 'yellow',
            'weak': 'orange1',
            'no_match': 'red'
        }.get(match['type'], 'white')
        
        match_node = tree.add(f"[{match_color}]Match: {match['label']} (Score: {match['score']:.2f})[/{match_color}]")
        
        # Add similarity breakdown if available
        if match.get('similarity_breakdown'):
            breakdown = match['similarity_breakdown']
            techniques_node = match_node.add("Techniques:")
            for tech, score in breakdown.get('techniques', {}).items():
                techniques_node.add(f"{tech}: {score:.2f}")
    else:
        tree.add("[red]Match: No suitable match found[/red]")
        if node_data.get('recommendations'):
            rec_node = tree.add("Recommendations:")
            for rec in node_data['recommendations']:
                rec_node.add(f"[yellow]{rec}[/yellow]")
    
    # Properties
    if 'properties' in node_data:
        props = node_data['properties']
        props_node = tree.add("Properties:")
        
        # Matched properties
        if props.get('matches'):
            matches_node = props_node.add(f"[green]Matched ({len(props['matches'])})[/green]")
            for prop in props['matches']:
                prop_text = f"{prop['source']} → {prop['target']} ({prop['score']:.2f})"
                if prop.get('recommendations'):
                    prop_text += f" [yellow]{prop['recommendations'][0]}[/yellow]"
                matches_node.add(prop_text)
        
        # Missing properties
        if props.get('missing'):
            missing_node = props_node.add(f"[yellow]Missing ({len(props['missing'])})[/yellow]")
            for prop in props['missing']:
                mandatory = " [red](mandatory)[/red]" if prop['mandatory'] else ""
                missing_node.add(f"{prop['name']}: {prop['type']}{mandatory}")
        
        # Extra properties
        if props.get('extra'):
            extra_node = props_node.add(f"[dim]Extra ({len(props['extra'])})[/dim]")
            for prop in props['extra'][:3]:
                extra_node.add(f"{prop['name']}")
            if len(props['extra']) > 3:
                extra_node.add(f"... and {len(props['extra']) - 3} more")
    
    # Validation warnings
    if node_data.get('validation', {}).get('warnings'):
        warnings_node = tree.add("[yellow]⚠️  Validation Warnings:[/yellow]")
        for warning in node_data['validation']['warnings']:
            warnings_node.add(f"[yellow]{warning}[/yellow]")
    
    # Confidence
    if node_data.get('match', {}).get('confidence'):
        confidence = node_data['match']['confidence']
        conf_color = 'green' if confidence > 0.8 else 'yellow' if confidence > 0.6 else 'red'
        tree.add(f"[{conf_color}]Confidence: {confidence:.1%}[/{conf_color}]")
    
    return Panel(tree, border_style="blue", width=100)


def format_entity_centric_relationship(rel_data: Dict[str, Any]) -> Panel:
    """
    Format a single relationship in entity-centric view.
    
    Args:
        rel_data: Relationship information from entity-centric formatter
        
    Returns:
        Rich Panel with relationship details
    """
    tree = Tree(f"[bold]🔗 RELATIONSHIP: {rel_data['source']['type']}[/bold]")
    
    # Show paths
    if rel_data['source'].get('paths'):
        paths_node = tree.add("Paths:")
        for path in rel_data['source']['paths'][:2]:
            paths_node.add(f"[dim]{path}[/dim]")
    
    # Match information
    if rel_data.get('match'):
        match = rel_data['match']
        match_color = {
            'exact': 'green',
            'strong': 'bright_green',
            'moderate': 'yellow',
            'weak': 'orange1',
            'no_match': 'red'
        }.get(match['match_type'], 'white')
        
        match_node = tree.add(f"[{match_color}]Match: {match['type']} (Score: {match['score']:.2f})[/{match_color}]")
        
        # Add similarity breakdown if available
        if match.get('similarity_breakdown'):
            breakdown = match['similarity_breakdown']
            techniques_node = match_node.add("Techniques:")
            for tech, score in breakdown.get('techniques', {}).items():
                techniques_node.add(f"{tech}: {score:.2f}")
    else:
        tree.add("[red]Match: No suitable match found[/red]")
        if rel_data.get('recommendations'):
            rec_node = tree.add("Recommendations:")
            for rec in rel_data['recommendations']:
                rec_node.add(f"[yellow]{rec}[/yellow]")
    
    # Properties (similar to nodes but usually fewer)
    if 'properties' in rel_data and rel_data['properties'].get('matches'):
        props_node = tree.add("Properties:")
        for prop in rel_data['properties']['matches']:
            props_node.add(f"{prop['source']} → {prop['target']} ({prop['score']:.2f})")
    
    # Validation warnings
    if rel_data.get('validation', {}).get('warnings'):
        warnings_node = tree.add("[yellow]⚠️  Validation Warnings:[/yellow]")
        for warning in rel_data['validation']['warnings']:
            warnings_node.add(f"[yellow]{warning}[/yellow]")
    
    return Panel(tree, border_style="cyan", width=100)


def format_matching_statistics(stats: Dict[str, Any]) -> Panel:
    """
    Format matching statistics summary.
    
    Args:
        stats: Statistics from the comparison
        
    Returns:
        Rich Panel with statistics
    """
    # Create summary table
    summary_table = Table(title="Matching Statistics", show_header=False)
    summary_table.add_column("Metric", style="bold")
    summary_table.add_column("Value", justify="right")
    
    overview = stats.get('overview', {})
    summary_table.add_row("Total Nodes Analyzed", str(overview.get('total_nodes_analyzed', 0)))
    summary_table.add_row("Node Match Rate", f"{overview.get('node_match_rate', 0):.1%}")
    summary_table.add_row("Total Relationships Analyzed", str(overview.get('total_relationships_analyzed', 0)))
    summary_table.add_row("Relationship Match Rate", f"{overview.get('relationship_match_rate', 0):.1%}")
    summary_table.add_row("Total Properties Analyzed", str(overview.get('total_properties_analyzed', 0)))
    summary_table.add_row("Property Match Rate", f"{overview.get('property_match_rate', 0):.1%}")
    
    # Create technique effectiveness table
    tech_table = Table(title="Technique Effectiveness")
    tech_table.add_column("Technique", style="cyan")
    tech_table.add_column("Usage", justify="right")
    tech_table.add_column("Success Rate", justify="right")
    tech_table.add_column("Avg Score", justify="right")
    
    tech_effectiveness = stats.get('technique_effectiveness', {})
    for technique, data in tech_effectiveness.items():
        tech_table.add_row(
            technique,
            str(data['usage_count']),
            f"{data['success_rate']:.1%}",
            f"{data['average_score']:.2f}"
        )
    
    # Create match distribution visualization
    dist_text = Text("Match Distribution:\n", style="bold")
    
    node_dist = stats.get('match_distribution', {}).get('nodes', {})
    if node_dist:
        dist_text.append("\nNodes: ", style="bold cyan")
        for match_type, count in node_dist.items():
            color = {
                'exact': 'green',
                'strong': 'bright_green',
                'moderate': 'yellow',
                'weak': 'orange1',
                'no_match': 'red'
            }.get(match_type, 'white')
            dist_text.append(f"{match_type}={count} ", style=color)
    
    rel_dist = stats.get('match_distribution', {}).get('relationships', {})
    if rel_dist:
        dist_text.append("\nRelationships: ", style="bold cyan")
        for match_type, count in rel_dist.items():
            color = {
                'exact': 'green',
                'strong': 'bright_green',
                'moderate': 'yellow',
                'weak': 'orange1',
                'no_match': 'red'
            }.get(match_type, 'white')
            dist_text.append(f"{match_type}={count} ", style=color)
    
    # Combine all elements
    columns = Columns([summary_table, tech_table], equal=True, expand=True)
    
    tree = Tree("📊 Matching Statistics")
    tree.add(columns)
    tree.add(dist_text)
    
    # Add common issues if present
    common_issues = stats.get('common_issues', {})
    if any(common_issues.values()):
        issues_node = tree.add("Common Issues Found:")
        if common_issues.get('case_mismatches', 0) > 0:
            issues_node.add(f"[yellow]Case mismatches: {common_issues['case_mismatches']}[/yellow]")
        if common_issues.get('abbreviations_found', 0) > 0:
            issues_node.add(f"[yellow]Abbreviations: {common_issues['abbreviations_found']}[/yellow]")
        
        naming_issues = common_issues.get('naming_convention_issues', {})
        if any(naming_issues.values()):
            naming_node = issues_node.add("Naming Convention Issues:")
            for issue_type, count in naming_issues.items():
                if count > 0:
                    naming_node.add(f"{issue_type}: {count}")
    
    return Panel(tree, border_style="green", width=120)


def format_verbose_match_explanation(match_data: Dict[str, Any]) -> Text:
    """
    Format verbose explanation of why a match was made.
    
    Args:
        match_data: Match data with rationale and candidates
        
    Returns:
        Rich Text with explanation
    """
    text = Text()
    
    # Show match rationale
    if match_data.get('match_rationale'):
        text.append(match_data['match_rationale'] + "\n", style="bright_white")
    
    # Show all candidates if available
    if match_data.get('all_candidates'):
        text.append("\nAll candidates considered:\n", style="bold")
        for i, (candidate, score) in enumerate(match_data['all_candidates'][:5], 1):
            candidate_name = candidate.label if hasattr(candidate, 'label') else candidate.type
            if score >= 0.7:
                style = "green"
            elif score >= 0.5:
                style = "yellow"
            else:
                style = "dim"
            
            text.append(f"  {i}. {candidate_name}: {score:.2f}\n", style=style)
        
        if len(match_data['all_candidates']) > 5:
            text.append(f"  ... and {len(match_data['all_candidates']) - 5} more\n", style="dim")
    
    # Show validation warnings
    if match_data.get('validation_warnings'):
        text.append("\n⚠️  Validation Warnings:\n", style="yellow bold")
        for warning in match_data['validation_warnings']:
            text.append(f"  • {warning}\n", style="yellow")
    
    return text


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


def display_schema_comparison_results(results: Dict[str, Any], show_json: bool = False,
                                    entity_centric: bool = False, verbose: bool = False):
    """
    Display comprehensive schema comparison results.
    
    Args:
        results: Comparison results dictionary
        show_json: Whether to show raw JSON output
        entity_centric: Whether to use entity-centric formatting
        verbose: Whether to show verbose details
    """
    # Handle entity-centric format
    if entity_centric and 'entities' in results:
        # Entity-centric view
        print_header("Entity-Centric Schema Comparison", 
                    "All information grouped by entity")
        
        # Display nodes
        if results['entities'].get('nodes'):
            console.print("\n[bold bright_blue]📦 NODES[/bold bright_blue]\n")
            for node_data in results['entities']['nodes']:
                panel = format_entity_centric_node(node_data)
                console.print(panel)
                console.print()
                
                # Show verbose match explanation if enabled
                if verbose and node_data.get('match'):
                    explanation = format_verbose_match_explanation(node_data)
                    console.print(explanation)
                    console.print()
        
        # Display relationships
        if results['entities'].get('relationships'):
            console.print("\n[bold bright_cyan]🔗 RELATIONSHIPS[/bold bright_cyan]\n")
            for rel_data in results['entities']['relationships']:
                panel = format_entity_centric_relationship(rel_data)
                console.print(panel)
                console.print()
                
                # Show verbose match explanation if enabled
                if verbose and rel_data.get('match'):
                    explanation = format_verbose_match_explanation(rel_data)
                    console.print(explanation)
                    console.print()
        
        # Show statistics if verbose
        if verbose and 'statistics' in results:
            stats_panel = format_matching_statistics(results['statistics'])
            console.print(stats_panel)
            console.print()
            
            # Show recommendations from statistics
            if results.get('statistics_recommendations'):
                console.print("[bold]📊 Statistics-Based Recommendations:[/bold]")
                for rec in results['statistics_recommendations']:
                    console.print(f"  • {rec}")
                console.print()
        
        # Show summary at the end
        if 'summary' in results:
            summary_panel = format_comparison_summary(results)
            console.print(summary_panel)
            console.print()
        
        return  # Don't show standard format
    
    # Standard format
    # Summary panel
    summary_panel = format_comparison_summary(results)
    console.print(summary_panel)
    console.print()
    
    # Show statistics in verbose mode
    if verbose and 'statistics' in results:
        stats_panel = format_matching_statistics(results['statistics'])
        console.print(stats_panel)
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
            
            # Print commands separately to avoid truncation
            console.print("\n[bold bright_magenta]Cypher Commands:[/bold bright_magenta]")
            for i, rename in enumerate(recs_by_type['relationship_renames'], 1):
                # Use Text object to ensure proper wrapping
                from rich.text import Text
                cmd_text = Text()
                cmd_text.append(f"{i}. ", style="bright_white")
                cmd_text.append(rename['cypher_command'], style="bright_cyan")
                console.print(cmd_text)
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
            
            # Print commands separately to avoid truncation
            console.print("\n[bold bright_magenta]Cypher Commands:[/bold bright_magenta]")
            for i, index in enumerate(recs_by_type['missing_indexes'], 1):
                # Use Text object to ensure proper wrapping
                from rich.text import Text
                cmd_text = Text()
                cmd_text.append(f"{i}. ", style="bright_white")
                cmd_text.append(index['cypher_command'], style="bright_cyan")
                console.print(cmd_text)
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
    
    # Generate and display unified compliance script if there are recommendations
    if 'recommendations_by_type' in results:
        recs = results['recommendations_by_type']
        if any(recs.values()):  # If there are any recommendations
            # Generate the unified script
            unified_script = generate_unified_compliance_script(recs)
            
            # Display with syntax highlighting but no side borders
            from rich.syntax import Syntax
            from rich.rule import Rule
            
            console.print("\n")
            # Header with accessible blue
            console.print(Rule("[bold bright_blue]📋 Unified Compliance Script[/bold bright_blue]", style="bright_blue"))
            console.print()
            
            # Script content with colorblind-friendly syntax highlighting
            # Using 'github-dark' theme which has good contrast and colorblind-friendly colors
            console.print(Syntax(unified_script, "cypher", theme="github-dark", line_numbers=False))
            console.print()
            
            # Footer
            console.print(Rule("[dim bright_blue]Copy and execute in Neo4j Browser or cypher-shell[/dim bright_blue]", style="bright_blue"))
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


def generate_unified_compliance_script(recommendations_by_type: Dict[str, List]) -> str:
    """
    Generate a unified Cypher script that includes all compliance recommendations.
    
    Args:
        recommendations_by_type: Dictionary of categorized recommendations
        
    Returns:
        Complete Cypher script as a string
    """
    script_lines = []
    
    # Header
    script_lines.append("// Neo4j Schema Compliance Script")
    script_lines.append("// Generated by Neo4j Schema Comparison Tool")
    script_lines.append("// Execute this script to bring your schema into compliance")
    script_lines.append("//")
    script_lines.append("// WARNING: This script will modify your graph schema.")
    script_lines.append("// Please backup your database before executing.")
    script_lines.append("")
    
    # 1. Node label renames (must be done first)
    if recommendations_by_type.get('node_renames'):
        script_lines.append("// ===== STEP 1: Node Label Changes =====")
        script_lines.append("// Rename node labels to match the standard")
        script_lines.append("")
        
        for rename in recommendations_by_type['node_renames']:
            script_lines.append(f"// Rename {rename['current_label']} to {rename['standard_label']}")
            script_lines.append(rename['cypher_command'] + ";")
            script_lines.append("")
    
    # 2. Relationship type renames
    if recommendations_by_type.get('relationship_renames'):
        script_lines.append("// ===== STEP 2: Relationship Type Changes =====")
        script_lines.append("// Rename relationship types to match the standard")
        script_lines.append("")
        
        for rename in recommendations_by_type['relationship_renames']:
            script_lines.append(f"// Rename {rename['current_type']} to {rename['standard_type']}")
            script_lines.append(rename['cypher_command'] + ";")
            script_lines.append("")
    
    # 3. Property renames
    if recommendations_by_type.get('property_renames'):
        script_lines.append("// ===== STEP 3: Property Name Changes =====")
        script_lines.append("// Rename properties to match the standard")
        script_lines.append("")
        
        # Group by element for better organization
        node_props = [p for p in recommendations_by_type['property_renames'] if p['element_type'] == 'Node']
        rel_props = [p for p in recommendations_by_type['property_renames'] if p['element_type'] == 'Relationship']
        
        if node_props:
            script_lines.append("// Node properties:")
            for prop in node_props:
                script_lines.append(f"// {prop['element_name']}.{prop['current_property']} -> {prop['standard_property']}")
                script_lines.append(prop['cypher_command'] + ";")
                script_lines.append("")
        
        if rel_props:
            script_lines.append("// Relationship properties:")
            for prop in rel_props:
                script_lines.append(f"// {prop['element_name']}.{prop['current_property']} -> {prop['standard_property']}")
                script_lines.append(prop['cypher_command'] + ";")
                script_lines.append("")
    
    # 4. Create missing indexes (after renames so they use correct labels)
    if recommendations_by_type.get('missing_indexes'):
        script_lines.append("// ===== STEP 4: Create Missing Indexes =====")
        script_lines.append("// Add indexes that exist in the standard but are missing")
        script_lines.append("")
        
        for index in recommendations_by_type['missing_indexes']:
            script_lines.append(f"// {index['index_type']} index on {index['element_label']}({', '.join(index['properties'])})")
            script_lines.append(index['cypher_command'] + ";")
            script_lines.append("")
    
    # Footer
    script_lines.append("// ===== Script Complete =====")
    script_lines.append("// Your schema should now be compliant with the standard.")
    script_lines.append("// Run a new comparison to verify compliance.")
    
    return "\n".join(script_lines)


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