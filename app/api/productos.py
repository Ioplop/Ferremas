from flask import Blueprint, request, jsonify, current_app, abort
from ..models import Producto
from .. import db
import os
from werkzeug.utils import secure_filename
from flask import url_for
from functools import wraps
from .validation import require_api_key

api_productos = Blueprint('api_productos', __name__, url_prefix='/api/productos')

@api_productos.route('/', methods=['GET'])
def listar_productos():
    productos = Producto.query.all()
    resultado = []
    for p in productos:
        imagen_url = url_for('static', filename=f"{current_app.config['PRODUCT_IMAGES_URL']}/{p.imagen}", _external=True)
        resultado.append({
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            'precio': p.precio,
            'stock': p.stock,
            'imagen': imagen_url
        })
    return jsonify(resultado)

@api_productos.route('/', methods=['POST'])
@require_api_key
def crear_producto():
    nombre = request.form['nombre']
    descripcion = request.form.get('descripcion', '')
    precio = float(request.form['precio'])
    stock = int(request.form['stock'])

    imagen_file = request.files['imagen']
    filename = secure_filename(imagen_file.filename)
    filepath = os.path.join(current_app.config['PRODUCT_IMAGES'], filename)
    imagen_file.save(filepath)

    nuevo = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        stock=stock,
        imagen=filename
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({'mensaje': 'Producto creado con éxito'}), 201