from os import getenv


class Config:
    """Base config."""
    SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://' \
                              f'{getenv("DB_USER")}:{getenv("DB_PASSWORD")}@' \
                              f'{getenv("DB_HOST")}:{getenv("DB_PORT")}/{getenv("DB_NAME")}'
    SQLALCHEMY_ECHO = True
