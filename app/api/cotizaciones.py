from flask import Blueprint, request, jsonify, current_app, abort
from ..models import Cotizacion, Producto, CotizacionProducto
from .. import db
import os
from werkzeug.utils import secure_filename
from flask import url_for
from .validation import require_api_key, valid_api_key
from datetime import datetime, timezone
import uuid

api_cotizaciones = Blueprint('api_cotizaciones', __name__, url_prefix='/api/cotizaciones')

def serializar_cotizacion(cotizacion: Cotizacion):
    productos = []
    for cp in cotizacion.productos:
        productos.append({
            'id': cp.producto.id,
            'nombre': cp.producto.nombre,
            'cantidad': cp.cantidad,
            'precio_unidad': cp.precio_unidad,
            'subtotal': cp.precio_unidad * cp.cantidad
        })

    return {
        'id': cotizacion.id,
        'uuid': cotizacion.uuid,
        'fecha': cotizacion.fecha.isoformat(),
        'bloqueado': cotizacion.bloqueado,
        'productos': productos,
        'total': cotizacion.total
    }

def calcular_cotizacion(cotizacion: Cotizacion) -> int:
    total = 0
    for cp in cotizacion.productos:
        total += cp.precio_unidad * cp.cantidad
    return total

@api_cotizaciones.route('/', methods=['GET'])
def ver_cotizacion():
    uuid_str = request.args.get('uuid')
    api_key = request.args.get('api_key')
    id = request.args.get('id')
    
    if uuid_str:
        cotizacion = Cotizacion.query.filter_by(uuid=uuid_str).first()
        if not cotizacion:
            return jsonify([]), 404
        return jsonify([serializar_cotizacion(cotizacion)])
    elif api_key is not None:
        if not valid_api_key(api_key):
            return jsonify({'error': 'La api-key es invalida'}), 401
        if id is None:
            cotizaciones = Cotizacion.query.all()
        else:
            cotizaciones = Cotizacion.query.filter(Cotizacion.id == id).all()
        resultado = []
        for cot in cotizaciones:
            resultado.append(serializar_cotizacion(cot))
        return jsonify(resultado)    
    else:
        return jsonify({'error': 'Se requiere el parámetro "uuid" o una api-key'}), 400

# 
@api_cotizaciones.route('/', methods=['POST'])
def crear_cotizacion():
    nueva_cotizacion = Cotizacion(
        uuid=str(uuid.uuid4()),
        fecha=datetime.now(timezone.utc),
        bloqueado=False
    )
    db.session.add(nueva_cotizacion)
    db.session.commit()

    return jsonify({'cotizacion_uuid': nueva_cotizacion.uuid}), 201

@api_cotizaciones.route('/producto', methods=['PATCH'])
def agregar_o_actualizar_producto():
    uuid = request.form.get('uuid')
    producto_id = request.form.get('producto_id', type=int)
    cantidad = request.form.get('cantidad', type=int)

    if not uuid or producto_id is None or cantidad is None:
        return jsonify({'error': 'Se requiere uuid, producto_id y cantidad'}), 400

    cot = Cotizacion.query.filter_by(uuid=uuid).first()
    if not cot:
        return jsonify({'error': 'Cotización no encontrada'}), 404
    if cot.bloqueado:
        return jsonify({'error': 'La cotización está bloqueada y no se puede modificar'}), 403

    producto = Producto.query.get(producto_id)
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404

    cp = CotizacionProducto.query.filter_by(
        cotizacion_id=cot.id,
        producto_id=producto.id
    ).first()

    # cantidad==0 indica que el usuario quiere ELIMINAR el producto del carrito.
    if cantidad == 0:
        if cp:
            db.session.delete(cp)
            db.session.commit()
            return jsonify({'mensaje': 'Producto eliminado del carrito'}), 200
        else:
            return jsonify({'mensaje': 'El producto no estaba en el carrito'}), 200

    # Queremos actualizar la cantidad de productos en el carrito. Debemos primero ver si ya existe el producto en el carro.
    if cp: # Se usa relacion ya existente
        cp.cantidad = cantidad
        cp.precio_unidad = producto.precio
    else: # Se crea nueva relacion
        cp = CotizacionProducto(
            cotizacion_id=cot.id,
            producto_id=producto.id,
            cantidad=cantidad,
            precio_unidad=producto.precio
        )
        db.session.add(cp)
    cot.total = calcular_cotizacion(cot)
    db.session.commit()
    return jsonify({'mensaje': 'Producto agregado/modificado exitosamente'}), 200

@api_cotizaciones.route('/', methods=['DELETE'])
@require_api_key
def eliminar_cotizacion():
    cotizacion_id = request.form.get('id', type=int)
    
    if not cotizacion_id:
        return jsonify({'error': 'Se requiere el parámetro id'}), 400

    cotizacion = Cotizacion.query.get(cotizacion_id)
    if not cotizacion:
        return jsonify({'error': 'Cotización no encontrada'}), 404

    if cotizacion.bloqueado:
        return jsonify({'error': 'La cotización está bloqueada y no puede eliminarse'}), 403

    db.session.delete(cotizacion)
    db.session.commit()

    return jsonify({'mensaje': 'Cotización eliminada con éxito'}), 200

@api_cotizaciones.route('/desbloquear', methods=['PATCH'])
def desbloquear_cotizacion():
    uuid_str = request.form.get('uuid')
    if not uuid_str:
        return jsonify({'error': 'Se requiere el UUID'}), 400

    cot = Cotizacion.query.filter_by(uuid=uuid_str).first()
    if not cot:
        return jsonify({'error': 'Cotización no encontrada'}), 404

    if cot.bloqueado is False:
        return jsonify({'error': 'La cotización ya está desbloqueada'}), 400

    if cot.orden_compra:
        return jsonify({'error': 'No se puede desbloquear: ya existe una orden asociada'}), 403

    cot.bloqueado = False
    db.session.commit()

    return jsonify({'mensaje': 'Cotización desbloqueada con éxito'}), 200

@api_cotizaciones.route('/bloquear', methods=['PATCH'])
def bloquear_cotizacion():
    uuid_str = request.form.get('uuid')
    if not uuid_str:
        return jsonify({'error': 'Se requiere el UUID'}), 400

    cot = Cotizacion.query.filter_by(uuid=uuid_str).first()
    if not cot:
        return jsonify({'error': 'Cotización no encontrada'}), 404

    if cot.bloqueado:
        return jsonify({'error': 'La cotización ya está bloqueada'}), 400

    cot.bloqueado = True
    db.session.commit()

    return jsonify({'mensaje': 'Cotización bloqueada con éxito'}), 200
