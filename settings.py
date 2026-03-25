from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    db_name: str
    db_user: str
    db_password: SecretStr
    db_host: str
    db_port: int
    db_echo: bool

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )
    @property
    def db_url(self):
        return f'postgresql+asyncpg://{self.db_user}:{self.db_password.get_secret_value()}@{self.db_host}:{self.db_port}/{self.db_name}'

class Settings(BaseSettings):
    db_settings: DBSettings = DBSettings()
    bot_token: SecretStr
    proxy_port: int
    proxy_host: str

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )
    @property
    def proxy_url(self):
        return f'socks5://{self.proxy_host}:{self.proxy_port}'
settings = Settings()