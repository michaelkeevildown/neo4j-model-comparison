"""
Neo4j Aura credential file parsing and management.

This module handles the parsing of Neo4j Aura credential files (.txt format)
and provides utilities for connection management and profile storage.
"""

import os
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class AuraCredentials:
    """Parsed Neo4j Aura credentials."""
    uri: str
    username: str
    password: str
    database: str = "neo4j"
    instance_id: Optional[str] = None
    instance_name: Optional[str] = None
    instructions: List[str] = None
    
    def __post_init__(self):
        if self.instructions is None:
            self.instructions = []


class AuraCredentialError(Exception):
    """Raised when there are issues with Aura credential parsing."""
    pass


def parse_aura_credentials_file(file_path: str) -> AuraCredentials:
    """
    Parse a Neo4j Aura credentials file.
    
    Args:
        file_path: Path to the Neo4j Aura credentials file
        
    Returns:
        AuraCredentials object with parsed information
        
    Raises:
        AuraCredentialError: If file cannot be parsed or required fields are missing
        FileNotFoundError: If the credential file doesn't exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Credentials file not found: {file_path}")
    
    credentials = {}
    instructions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Capture comments and instructions
                if line.startswith('#'):
                    instructions.append(line)
                    continue
                
                # Parse key=value pairs
                if '=' in line and not line.startswith('#'):
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        credentials[key] = value
                        
                    except ValueError:
                        raise AuraCredentialError(
                            f"Invalid format on line {line_num}: {line}"
                        )
    
    except Exception as e:
        if isinstance(e, AuraCredentialError):
            raise
        raise AuraCredentialError(f"Error reading credentials file: {e}")
    
    # Validate required fields
    required_fields = ['NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD']
    missing_fields = [field for field in required_fields if field not in credentials]
    
    if missing_fields:
        raise AuraCredentialError(
            f"Missing required fields in credentials file: {missing_fields}"
        )
    
    # Extract database name from URI or use default
    database = credentials.get('NEO4J_DATABASE', 'neo4j')
    
    return AuraCredentials(
        uri=credentials['NEO4J_URI'],
        username=credentials['NEO4J_USERNAME'],
        password=credentials['NEO4J_PASSWORD'],
        database=database,
        instance_id=credentials.get('AURA_INSTANCEID'),
        instance_name=credentials.get('AURA_INSTANCENAME'),
        instructions=instructions
    )


def validate_aura_uri(uri: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a Neo4j Aura URI format.
    
    Args:
        uri: The URI to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not uri:
        return False, "URI cannot be empty"
    
    # Check for Aura-specific patterns
    aura_patterns = [
        r'^neo4j\+s://[a-zA-Z0-9-]+\.databases\.neo4j\.io$',
        r'^bolt\+s://[a-zA-Z0-9-]+\.databases\.neo4j\.io:\d+$',
    ]
    
    is_aura = any(re.match(pattern, uri) for pattern in aura_patterns)
    
    if not is_aura:
        # Check for general Neo4j URI patterns
        general_patterns = [
            r'^neo4j://.*',
            r'^bolt://.*',
            r'^neo4j\+s://.*',
            r'^bolt\+s://.*'
        ]
        
        is_neo4j = any(re.match(pattern, uri) for pattern in general_patterns)
        
        if not is_neo4j:
            return False, "URI does not appear to be a valid Neo4j connection string"
        else:
            # Valid Neo4j URI but not Aura - that's okay
            return True, None
    
    return True, None


def extract_connection_info(credentials: AuraCredentials) -> Dict[str, str]:
    """
    Extract connection information in a format suitable for environment variables.
    
    Args:
        credentials: Parsed Aura credentials
        
    Returns:
        Dictionary with environment variable mappings
    """
    return {
        'NEO4J_URI': credentials.uri,
        'NEO4J_USERNAME': credentials.username,
        'NEO4J_PASSWORD': credentials.password,
        'NEO4J_DATABASE': credentials.database
    }


def get_connection_instructions(credentials: AuraCredentials) -> List[str]:
    """
    Get human-readable connection instructions from the credentials.
    
    Args:
        credentials: Parsed Aura credentials
        
    Returns:
        List of instruction strings
    """
    instructions = []
    
    # Add any instructions from the file
    for instruction in credentials.instructions:
        # Clean up the instruction text
        clean_instruction = instruction.lstrip('#').strip()
        if clean_instruction:
            instructions.append(clean_instruction)
    
    # Add general Aura connection info
    if credentials.instance_name:
        instructions.append(f"Instance: {credentials.instance_name}")
    
    if credentials.instance_id:
        instructions.append(f"Instance ID: {credentials.instance_id}")
    
    # Extract hostname for display
    try:
        if 'databases.neo4j.io' in credentials.uri:
            hostname = credentials.uri.split('//')[1].split('.')[0]
            instructions.append(f"Aura Database: {hostname}")
    except (IndexError, AttributeError):
        pass
    
    return instructions


def is_aura_credentials_file(file_path: str) -> bool:
    """
    Check if a file appears to be a Neo4j Aura credentials file.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if the file appears to be an Aura credentials file
    """
    if not os.path.exists(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Look for Aura-specific patterns
        aura_indicators = [
            'NEO4J_URI',
            'NEO4J_USERNAME', 
            'NEO4J_PASSWORD',
            'AURA_INSTANCEID',
            'databases.neo4j.io',
            'console.neo4j.io'
        ]
        
        return any(indicator in content for indicator in aura_indicators)
        
    except Exception:
        return False


def suggest_credential_files(directory: str = ".") -> List[str]:
    """
    Suggest potential credential files in a directory.
    
    Args:
        directory: Directory to search in
        
    Returns:
        List of potential credential file paths
    """
    search_dir = Path(directory)
    if not search_dir.exists():
        return []
    
    potential_files = []
    
    # Common patterns for Neo4j credential files
    patterns = [
        "*.txt",
        "*neo4j*",
        "*aura*",
        "*credentials*",
        ".env*"
    ]
    
    for pattern in patterns:
        for file_path in search_dir.glob(pattern):
            if file_path.is_file() and is_aura_credentials_file(str(file_path)):
                potential_files.append(str(file_path))
    
    return sorted(list(set(potential_files)))  # Remove duplicates and sort