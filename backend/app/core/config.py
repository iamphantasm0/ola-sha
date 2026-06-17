from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 0G Compute (OpenAI-compatible router)
    OG_COMPUTE_API_KEY: str = ""
    OG_COMPUTE_BASE_URL: str = "https://router-api-testnet.integratenetwork.work/v1"
    OG_COMPUTE_MODEL: str = "MiniMax-M3"

    # 0G Storage sidecar
    STORAGE_SIDECAR_URL: str = "http://storage-sidecar:3001"
    SIDECAR_AUTH_TOKEN: str = ""

    # 0G Chain
    OG_CHAIN_RPC: str = "https://evmrpc-testnet.0g.ai"
    OG_CHAIN_ID: int = 16602
    PRIVATE_KEY: str = ""
    REGISTRY_CONTRACT_ADDRESS: str = ""

    # Paycrest
    PAYCREST_API_KEY: str = ""
    PAYCREST_WEBHOOK_SECRET: str = ""
    PAYCREST_REFUND_ADDRESS: str = ""
    PAYCREST_BASE_URL: str = "https://api.paycrest.io/v2"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ola:changeme@db:5432/ola"

    # App
    SECRET_KEY: str = "dev-secret"
    DEBUG: bool = True

    # Settlement poller cadence (seconds) — the no-webhook path to detecting settlement.
    RECONCILE_INTERVAL: int = 10


settings = Settings()
