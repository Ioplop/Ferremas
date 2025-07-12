from flask import Blueprint, request, jsonify, current_app, abort
from ..models import Producto
from .. import db
import os
from werkzeug.utils import secure_filename
from flask import url_for
from .validation import require_api_key

api_productos = Blueprint('api_productos', __name__, url_prefix='/api/productos')

@api_productos.route('/', methods=['GET'])
def listar_productos():
    query = Producto.query

    # Filtros opcionales
    id = request.args.get('id', type=int)
    if id is not None:
        query = query.filter(Producto.id == id)

    nombre = request.args.get('nombre')
    if nombre:
        query = query.filter(Producto.nombre.ilike(f"%{nombre}%"))

    stock_min = request.args.get('stock_min', type=int)
    if stock_min is not None:
        query = query.filter(Producto.stock >= stock_min)

    precio_max = request.args.get('precio_max', type=float)
    if precio_max is not None:
        query = query.filter(Producto.precio <= precio_max)

    productos = query.all()

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

@api_productos.route('/', methods=['PATCH'])
@require_api_key
def modificar_producto():
    producto_id = int(request.form['id'])  # o 'producto_id' si prefieres

    producto = Producto.query.get_or_404(producto_id)

    if 'nombre' in request.form:
        producto.nombre = request.form['nombre']
    if 'descripcion' in request.form:
        producto.descripcion = request.form['descripcion']
    if 'precio' in request.form:
        producto.precio = float(request.form['precio'])
    if 'stock' in request.form:
        producto.stock = int(request.form['stock'])

    if 'imagen' in request.files:
        imagen_file = request.files['imagen']
        filename = secure_filename(imagen_file.filename)
        filepath = os.path.join(current_app.config['PRODUCT_IMAGES'], filename)
        imagen_file.save(filepath)
        producto.imagen = filename

    db.session.commit()
    return jsonify({'mensaje': 'Producto actualizado con éxito'})

@api_productos.route('/', methods=['DELETE'])
@require_api_key
def eliminar_producto():
    producto_id = request.form.get('id')
    if not producto_id:
        return jsonify({'error': 'Falta el ID del producto'}), 400

    producto = Producto.query.get_or_404(int(producto_id))
    db.session.delete(producto)
    db.session.commit()
    return jsonify({'mensaje': 'Producto eliminado con éxito'})
