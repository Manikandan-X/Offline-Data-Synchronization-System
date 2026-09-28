from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str
    app_version: str
    debug: bool

    mysql_host: str
    mysql_port: int
    mysql_database: str
    mysql_user: str
    mysql_password: str
    mysql_root_password: str

    redis_host: str
    redis_port: int
    redis_db: int
    redis_url: str
    redis_cache_ttl: int

    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int

    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()