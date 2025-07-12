from flask import Blueprint, request, jsonify, current_app
from .models import Producto
from . import db
import os
from werkzeug.utils import secure_filename

api = Blueprint('api', __name__)

@api.route('/api/productos', methods=['GET'])
def listar_productos():
    productos = Producto.query.all()
    resultado = []
    for p in productos:
        resultado.append({
            'id': p.id,
            'nombre': p.nombre,
            'descripcion': p.descripcion,
            'precio': p.precio,
            'stock': p.stock,
            'imagen': p.imagen
        })
    return jsonify(resultado)

@api.route('/api/productos', methods=['POST'])
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