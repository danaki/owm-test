import os

class BaseConfig:
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'my_precious')
    DEBUG = False

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    DB_FILE = 'dev'

class TestingConfig(BaseConfig):
    DEBUG = True
    TESTING = True
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    DB_FILE = 'test'

class ProductionConfig(BaseConfig):
    JWT_SECRET_KEY = 'my_precious'
    DEBUG = False
    DB_FILE = 'prod'
