from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    ACCOUNT_ID: str
    SHOP_SECRET: str
    ADMIN_ROLE_NAME: str
    DISCORD_SERVER_ID: int

    class Config:
        case_sensitive = True
        env_file = "config.env"


config = Settings()
