from flask import Blueprint, request, jsonify, current_app, abort
from ..models import Cotizacion, Producto
from .. import db
import os
from werkzeug.utils import secure_filename
from flask import url_for
from .validation import require_api_key, valid_api_key
from datetime import datetime, timezone
import uuid

api_cotizaciones = Blueprint('api_cotizaciones', __name__, url_prefix='/api/cotizaciones')

@api_cotizaciones.route('/', methods=['GET'])
def ver_cotizacion():
    uuid_str = request.args.get('uuid')
    api_key = request.args.get('api_key')
    
    if uuid_str:
        cotizacion = Cotizacion.query.filter_by(uuid=uuid_str).first()
        if not cotizacion:
            return jsonify([]), 404
        productos = []
        for cp in cotizacion.productos:
            productos.append({
                'id': cp.producto.id,
                'nombre': cp.producto.nombre,
                'cantidad': cp.cantidad,
                'precio_unitario': cp.precio_unitario,
                'subtotal': cp.precio_unitario * cp.cantidad
            })
        return jsonify([{
            'uuid': cotizacion.uuid,
            'fecha': cotizacion.fecha.isoformat(),
            'bloqueado': cotizacion.bloqueado,
            'productos': productos
        }])
    elif api_key is not None:
        if not valid_api_key(api_key):
            return jsonify({'error': 'La api-key es invalida'}), 401
        cotizaciones = Cotizacion.query.all()
        resultado = []
        for cot in cotizaciones:
            productos = []
            for cp in cot.productos:
                productos.append({
                    'id': cp.producto.id,
                    'nombre': cp.producto.nombre,
                    'cantidad': cp.cantidad,
                    'precio_unitario': cp.precio_unitario,
                    'subtotal': cp.precio_unitario * cp.cantidad
                })

            resultado.append({
                'id': cot.id,
                'uuid': cot.uuid,
                'fecha': cot.fecha.isoformat(),
                'bloqueado': cot.bloqueado,
                'num_productos': len(cot.productos),
                'productos': productos
            })
        return jsonify(resultado)    
    else:
        return jsonify({'error': 'Se requiere el parámetro "uuid" o una api-key'}), 400

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

