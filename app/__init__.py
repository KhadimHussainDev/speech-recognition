from flask import Flask
from app.routes import app as app_blueprint

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.register_blueprint(app_blueprint)
    return app