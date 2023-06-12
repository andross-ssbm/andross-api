from os import getenv


class Config:
    """Base config."""
    SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://' \
                              f'{getenv("DB_USER")}:{getenv("DB_PASSWORD")}@' \
                              f'{getenv("DB_HOST")}:{getenv("DB_PORT")}/{getenv("DB_NAME")}'
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 60,
        'pool_pre_ping': True
    }


class ProdConfig(Config):
    SQLALCHEMY_ECHO = False