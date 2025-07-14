from flask import Flask
from flask_sqlalchemy import SQLAlchemy # Para conexiones a base de datos sqlite
from dotenv import load_dotenv # Para variables de entorno
import secrets # Creacion de clave de api
import os
import __main__ # Obtener ruta de archivo principal

db = SQLAlchemy()

def load_env(env_path: str):
    # Crear archivo env si no existe
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            pass
    # Cargar archivo env
    load_dotenv(env_path)

def add_dotenv_var(env_path: str, name: str, value: str):
    with open(env_path, 'a') as f:
        f.write(f"{name}={value}\n")
    os.environ[name] = value

def create_app():
    app = Flask(__name__)
    # Cargar variables de entorno
    # Verificar que exisa .env. Si no, crearlo
    env_path = os.path.abspath(os.path.join(os.path.dirname(__main__.__file__), '.env'))
    load_env(env_path)

    # Crear configuracion
    # Clave de api que permite hacer llamadas PATCH - POST - REMOVE
    # Crear so no existe
    apikey = os.getenv('SECRET_API_KEY')
    if not apikey:
        apikey = secrets.token_hex(32)
        add_dotenv_var(env_path, "SECRET_API_KEY", apikey)
    app.config['SECRET_API_KEY'] = apikey

    # Base de datos
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ferremas.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Carpeta de carga de archivos
    app.config['UPLOAD_FOLDER'] = os.path.join('app', 'static', 'uploads')
    # Carpeta de imagenes de productos
    app.config['PRODUCT_IMAGES'] = os.path.join('app', 'static', 'img', 'productos')
    # URL a imagenes de productos
    app.config['PRODUCT_IMAGES_URL'] = 'img/productos'
    # Crear carpeta de carga si no existe
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    # Crear carpeta de imagenes de producto si no existe
    os.makedirs(app.config['PRODUCT_IMAGES'], exist_ok=True)

    # Iniciar base de datos
    db.init_app(app)

    # Registrar blueprints de apis
    from .api.productos import api_productos
    from .api.cotizaciones import api_cotizaciones
    from .api.ordenes import api_ordenes
    from .api.pagos import api_pagos
    from .api.moneda import api_moneda
    app.register_blueprint(api_productos)
    app.register_blueprint(api_cotizaciones)
    app.register_blueprint(api_ordenes)
    app.register_blueprint(api_pagos)
    app.register_blueprint(api_moneda)

    with app.app_context():
        db.create_all()

    return app
