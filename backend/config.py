from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://ontology:ontology@localhost:5432/ontology"
    redis_url: str = "redis://localhost:6379"

    github_token: str = ""
    sec_user_agent: str = "Ontology ontology@example.com"

    r2_endpoint: str = ""
    r2_access_key: str = ""
    r2_secret_key: str = ""
    r2_bucket: str = "ontology-raw"

    # Anthropic API (Agent Layer)
    anthropic_api_key: str = ""

    # New connector API keys
    alpha_vantage_key: str = ""
    finnhub_api_key: str = ""
    fred_api_key: str = ""
    eia_api_key: str = ""

    # Cache TTL in seconds
    cache_ttl: int = 3600

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
