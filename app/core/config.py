"""
Application configuration management
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # App Info
    APP_NAME: str = "Hệ thống Thanh toán QR Trường học"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "API cho hệ thống thanh toán học phí và phát hành hóa đơn điện tử"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-at-least-32-chars-long")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Database
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    DB_ECHO: bool = os.getenv("DB_ECHO", "false").lower() == "true"
    
    # CORS
    ALLOWED_ORIGINS: list = []  # set via ENV: comma-separated
    
    # External Services
    PAYMENT_GATEWAY_URL: str = os.getenv("PAYMENT_GATEWAY_URL", "https://api.demo-payment.com")
    PAYMENT_API_KEY: str = os.getenv("PAYMENT_API_KEY", "demo-key")
    MERCHANT_ID: str = os.getenv("MERCHANT_ID", "demo-merchant")
    
    EINVOICE_API_URL: str = os.getenv("EINVOICE_API_URL", "https://api.demo-einvoice.com")
    EINVOICE_API_KEY: str = os.getenv("EINVOICE_API_KEY", "demo-key")
    
    # Company Info
    COMPANY_TAX_CODE: str = os.getenv("COMPANY_TAX_CODE", "0123456789")
    COMPANY_NAME: str = os.getenv("COMPANY_NAME", "Trường Tiểu học ABC")
    COMPANY_ADDRESS: str = os.getenv("COMPANY_ADDRESS", "123 Đường ABC, Quận XYZ, TP. HCM")
    
    # Email Config
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    
    # File Upload
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def database_url(self) -> str:
        """Get database URL with SQLite fallback"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return "sqlite:///./school_payment.db"
    
    @property
    def is_mysql(self) -> bool:
        """Check if using MySQL database"""
        return self.database_url.startswith("mysql")

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def allowed_origins(self) -> list:
        """Compute allowed CORS origins from env (comma-separated)"""
        env_val = os.getenv("ALLOWED_ORIGINS", "")
        if not env_val:
            return ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000", "http://127.0.0.1:5000"]
        return [o.strip() for o in env_val.split(",") if o.strip()]


# Global settings instance
settings = Settings()