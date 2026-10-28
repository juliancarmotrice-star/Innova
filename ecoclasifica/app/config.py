"""
ECOCLASIFICA — Configuración de la aplicación.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    # Modelo con visión. Verifica el vigente en docs.claude.com antes de desplegar.
    modelo: str = "claude-sonnet-5-5"

    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    # IDs de Telegram (separados por coma) con acceso a /stats. Sin clave compartida.
    admin_telegram_ids: str = ""

    db_path: str = "ecoclasifica.db"
    # Por debajo de este valor se pide otra foto en vez de dar una respuesta dudosa.
    umbral_confianza: float = 0.6

    app_env: str = "dev"
    log_level: str = "info"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
