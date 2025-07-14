from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')  # Asegúrate de tener este archivo

    db.init_app(app)
    CORS(app)

    # 👉 Registra todos tus blueprints
    from .api.productos import api_productos
    from .api.cotizaciones import api_cotizaciones
    from .api.utiles import api_utiles  # 💰 aquí va la API del dólar

    app.register_blueprint(api_productos)
    app.register_blueprint(api_cotizaciones)
    app.register_blueprint(api_utiles)

    return app
