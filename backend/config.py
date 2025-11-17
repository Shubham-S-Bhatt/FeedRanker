"""
Configuration management from environment variables.
"""

from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # gRPC Configuration
    GRPC_HOST: str = os.getenv("GRPC_HOST", "localhost:50051")

    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://feedranker:feedranker@localhost:5432/feedranker"
    )

    # Security
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")

    # Model Configuration
    ENSEMBLE_WEIGHT_LAMBDAMART: float = float(os.getenv("ENSEMBLE_WEIGHT_LM", "0.5"))
    ENSEMBLE_WEIGHT_CTR: float = float(os.getenv("ENSEMBLE_WEIGHT_CTR", "0.5"))

    class Config:
        env_file = ".env"


settings = Settings()
