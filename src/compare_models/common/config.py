from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Neo4jSettings(BaseSettings):
    uri: str
    username: str
    password: str
    database: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="NEO4J_"
    )


def get_settings() -> Neo4jSettings:
    """
    Get fresh Neo4j settings from environment variables.
    This function creates a new settings instance each time it's called,
    ensuring it picks up any changes to environment variables.
    """
    return Neo4jSettings()


# For backward compatibility, create a default instance
# but recommend using get_settings() for dynamic loading
settings = Neo4jSettings()
