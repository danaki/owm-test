import os

from flask import Flask
from tinymongo import TinyMongoClient
from flask_jwt_simple import JWTManager

app = Flask(__name__)

app_settings = os.getenv(
    'APP_SETTINGS',
    'project.server.config.DevelopmentConfig'
)
app.config.from_object(app_settings)

connection = TinyMongoClient(app.config['DB_FILE'])
db = connection.db

from project.server.views import bp

app.register_blueprint(bp)

jwt = JWTManager(app)
