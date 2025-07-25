"""
Neo4j database discovery and interactive selection.

This module provides functionality to discover available databases in a Neo4j
instance and present them to users for interactive selection.
"""

import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError, ConfigurationError


@dataclass
class DatabaseInfo:
    """Information about a Neo4j database."""
    name: str
    status: str
    role: str
    is_default: bool
    is_system: bool
    address: Optional[str] = None
    error: Optional[str] = None


class DatabaseDiscoveryError(Exception):
    """Raised when database discovery fails."""
    pass


class DatabaseDiscovery:
    """Handles Neo4j database discovery and selection."""
    
    def __init__(self, uri: str, username: str, password: str):
        """
        Initialize database discovery.
        
        Args:
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
        """
        self.uri = uri
        self.username = username
        self.password = password
        self._driver = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def connect(self) -> None:
        """
        Establish connection to Neo4j.
        
        Raises:
            DatabaseDiscoveryError: If connection fails
        """
        try:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            # Test the connection
            with self._driver.session() as session:
                session.run("RETURN 1")
        except ServiceUnavailable as e:
            raise DatabaseDiscoveryError(f"Could not connect to Neo4j at {self.uri}: {e}")
        except AuthError as e:
            raise DatabaseDiscoveryError(f"Authentication failed: {e}")
        except Exception as e:
            raise DatabaseDiscoveryError(f"Connection error: {e}")
    
    def close(self) -> None:
        """Close the Neo4j connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
    
    def discover_databases(self, include_system: bool = False) -> List[DatabaseInfo]:
        """
        Discover all available databases.
        
        Args:
            include_system: Whether to include system databases
            
        Returns:
            List of DatabaseInfo objects
            
        Raises:
            DatabaseDiscoveryError: If discovery fails
        """
        if not self._driver:
            raise DatabaseDiscoveryError("Not connected to Neo4j")
        
        databases = []
        
        try:
            with self._driver.session() as session:
                # Try to get database information
                try:
                    result = session.run("SHOW DATABASES")
                    for record in result:
                        db_info = self._parse_database_record(record)
                        
                        # Filter system databases if requested
                        if not include_system and db_info.is_system:
                            continue
                        
                        databases.append(db_info)
                        
                except Exception as e:
                    # Fallback for older Neo4j versions or limited permissions
                    if "procedure" in str(e).lower() or "permission" in str(e).lower():
                        # Try to get current database info
                        try:
                            result = session.run("CALL db.info()")
                            record = result.single()
                            if record:
                                current_db = DatabaseInfo(
                                    name=record.get("databaseName", "neo4j"),
                                    status="online",
                                    role="primary",
                                    is_default=True,
                                    is_system=False
                                )
                                databases.append(current_db)
                        except Exception:
                            # Last resort - assume default database
                            default_db = DatabaseInfo(
                                name="neo4j",
                                status="online", 
                                role="primary",
                                is_default=True,
                                is_system=False
                            )
                            databases.append(default_db)
                    else:
                        raise DatabaseDiscoveryError(f"Failed to discover databases: {e}")
        
        except Exception as e:
            if isinstance(e, DatabaseDiscoveryError):
                raise
            raise DatabaseDiscoveryError(f"Database discovery failed: {e}")
        
        return databases
    
    def _parse_database_record(self, record) -> DatabaseInfo:
        """
        Parse a database record from SHOW DATABASES.
        
        Args:
            record: Neo4j record from SHOW DATABASES
            
        Returns:
            DatabaseInfo object
        """
        name = record.get("name", "unknown")
        
        # Determine if it's a system database
        is_system = (
            name == "system" or 
            name.startswith("system") or
            record.get("type") == "system"
        )
        
        return DatabaseInfo(
            name=name,
            status=record.get("currentStatus", "unknown"),
            role=record.get("role", "unknown"),
            is_default=record.get("default", False),
            is_system=is_system,
            address=record.get("address")
        )
    
    def validate_database_access(self, database_name: str) -> bool:
        """
        Check if the user has access to a specific database.
        
        Args:
            database_name: Name of the database to check
            
        Returns:
            True if access is available
        """
        if not self._driver:
            return False
        
        try:
            with self._driver.session(database=database_name) as session:
                session.run("RETURN 1")
                return True
        except Exception:
            return False
    
    def get_database_stats(self, database_name: str) -> Dict[str, Any]:
        """
        Get basic statistics about a database.
        
        Args:
            database_name: Name of the database
            
        Returns:
            Dictionary with database statistics
        """
        if not self._driver:
            return {}
        
        stats = {
            "nodes": 0,
            "relationships": 0,
            "labels": [],
            "relationship_types": [],
            "accessible": False
        }
        
        try:
            with self._driver.session(database=database_name) as session:
                # Check if we can access the database
                session.run("RETURN 1")
                stats["accessible"] = True
                
                # Get node count
                try:
                    result = session.run("MATCH (n) RETURN count(n) as count")
                    record = result.single()
                    if record:
                        stats["nodes"] = record["count"]
                except Exception:
                    pass
                
                # Get relationship count
                try:
                    result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                    record = result.single()
                    if record:
                        stats["relationships"] = record["count"]
                except Exception:
                    pass
                
                # Get labels
                try:
                    result = session.run("CALL db.labels()")
                    stats["labels"] = [record["label"] for record in result]
                except Exception:
                    pass
                
                # Get relationship types
                try:
                    result = session.run("CALL db.relationshipTypes()")
                    stats["relationship_types"] = [record["relationshipType"] for record in result]
                except Exception:
                    pass
                    
        except Exception as e:
            stats["error"] = str(e)
        
        return stats


def filter_selectable_databases(databases: List[DatabaseInfo]) -> List[DatabaseInfo]:
    """
    Filter databases to only include those suitable for schema analysis.
    
    Args:
        databases: List of all discovered databases
        
    Returns:
        Filtered list of selectable databases
    """
    selectable = []
    
    for db in databases:
        # Skip system databases
        if db.is_system:
            continue
        
        # Skip offline databases
        if db.status.lower() not in ["online", "running"]:
            continue
        
        selectable.append(db)
    
    return selectable


def get_recommended_database(databases: List[DatabaseInfo]) -> Optional[DatabaseInfo]:
    """
    Get the recommended database for analysis.
    
    Args:
        databases: List of available databases
        
    Returns:
        Recommended database or None
    """
    selectable = filter_selectable_databases(databases)
    
    if not selectable:
        return None
    
    # Prefer the default database
    for db in selectable:
        if db.is_default:
            return db
    
    # If no default, prefer "neo4j" database
    for db in selectable:
        if db.name == "neo4j":
            return db
    
    # Otherwise, return the first selectable database
    return selectable[0]


def format_database_display_name(db: DatabaseInfo) -> str:
    """
    Format a database name for display in selection menus.
    
    Args:
        db: Database info object
        
    Returns:
        Formatted display name
    """
    name = db.name
    
    if db.is_default:
        name += " (default)"
    
    if db.status.lower() != "online":
        name += f" [{db.status}]"
    
    return name