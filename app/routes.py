from flask import Blueprint, request, jsonify, current_app, abort
from .models import Producto
from . import db
import os
from werkzeug.utils import secure_filename
from flask import url_for
from functools import wraps

api = Blueprint('api', __name__)

@api.route('/api/productos', methods=['GET'])
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

def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_key = request.form.get('api_key')
        if not api_key:
            return jsonify({'error': 'Se requiere api_key en el cuerpo de la solicitud'}), 401
        if api_key != current_app.config['SECRET_API_KEY']:
            return jsonify({'error': 'api_key inválida'}), 401
        return func(*args, **kwargs)
    return wrapper

@api.route('/api/productos', methods=['POST'])
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

@api.route('/api/comprar/<int:id>', methods=['POST'])
def comprar_producto(id):
    producto = Producto.query.get_or_404(id)
    cantidad = int(request.json.get('cantidad', 1))
    if producto.stock >= cantidad:
        producto.stock -= cantidad
        db.session.commit()
        return jsonify({'mensaje': 'Compra realizada correctamente'})
    else:
        return jsonify({'error': 'Stock insuficiente'})