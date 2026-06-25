from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime config, loaded from the monorepo root .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ─── 0G Compute (OpenAI-compatible router) ──────────────────────────
    OG_COMPUTE_API_KEY: str = ""
    OG_COMPUTE_BASE_URL: str = "https://router-api-testnet.integratenetwork.work/v1"
    OG_COMPUTE_MODEL: str = "zai-org/GLM-5-FP8"

    # ─── 0G Storage (via Node sidecar) ──────────────────────────────────
    OG_STORAGE_RPC: str = "https://evmrpc-testnet.0g.ai"
    OG_STORAGE_INDEXER: str = "https://indexer-storage-testnet-turbo.0g.ai"
    OG_STORAGE_PRIVATE_KEY: str = ""
    STORAGE_SIDECAR_URL: str = "http://storage-sidecar:3001"

    # ─── 0G Chain (OrderRegistry) ───────────────────────────────────────
    OG_CHAIN_RPC: str = "https://evmrpc-testnet.0g.ai"
    OG_CHAIN_ID: int = 16602
    DEPLOYER_PRIVATE_KEY: str = ""
    REGISTRY_CONTRACT_ADDRESS: str = ""

    # ─── Paycrest (Sender API v2) ───────────────────────────────────────
    # Use a SEPARATE sender account from Sterling Concierge — one webhook
    # URL per account.
    PAYCREST_API_KEY: str = ""
    PAYCREST_WEBHOOK_SECRET: str = ""
    PAYCREST_REFUND_ADDRESS: str = ""
    PAYCREST_BASE_URL: str = "https://api.paycrest.io/v2"
    PAYCREST_DEFAULT_NETWORK: str = "base"

    # ─── Database ───────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://ola:ola@db:5432/ola"

    # ─── App ────────────────────────────────────────────────────────────
    SECRET_KEY: str = "dev-secret-change-me"
    DEBUG: bool = True


settings = Settings()
