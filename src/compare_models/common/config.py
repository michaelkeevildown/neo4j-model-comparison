from pydantic_settings import BaseSettings, SettingsConfigDict


class Neo4jSettings(BaseSettings):
    uri: str
    username: str
    password: str
    database: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="NEO4J_"
    )


settings = Neo4jSettings()
