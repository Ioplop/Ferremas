from flask import Blueprint, request, jsonify, current_app, abort
from ..models import Producto, Cotizacion, OrdenCompra
from .. import db
import os
from werkzeug.utils import secure_filename
from flask import url_for
from .validation import require_api_key, valid_api_key
from datetime import datetime, timezone
import uuid
from typing import Tuple

api_ordenes = Blueprint('api_ordenes', __name__, url_prefix='/api/ordenes')

def validar_stock(cotizacion: Cotizacion) -> Tuple[bool, list]:
    """
    Verifica que haya stock disponible para todos los productos en la cotización.
    Retorna (True, []) si todo está bien, o (False, lista_de_errores) si falta stock.
    """
    errores = []
    for cp in cotizacion.productos:
        producto = cp.producto
        cantidad_pedida = cp.cantidad
        stock_disponible = producto.stock - producto.reservados

        if cantidad_pedida > stock_disponible:
            errores.append(f"Producto '{producto.nombre}' solo tiene {stock_disponible} en stock disponible, se pidió {cantidad_pedida}")

    return (len(errores) == 0, errores)

def reservar_stock(cotizacion: Cotizacion):
    """
    Para cada producto en la cotización, aumenta la reserva.
    """
    for cp in cotizacion.productos:
        producto = cp.producto
        cantidad = cp.cantidad
        producto.reservados += cantidad

    db.session.commit()

def liberar_stock(cotizacion: Cotizacion):
    """
    Para cada producto en la cotización, disminuye la reserva
    """
    for cp in cotizacion.productos:
        producto = cp.producto
        cantidad = cp.cantidad
        producto.reservados -= cantidad

    db.session.commit()

def consumir_stock(cotizacion: Cotizacion):
    """
    Para cada producto en la cotización, disminuye la reserva y la cantidad total de stock (porque el producto es retirado del inventario y enviado)
    """
    for cp in cotizacion.productos:
        producto = cp.producto
        cantidad = cp.cantidad
        producto.reservados -= cantidad
        producto.stock -= cantidad

    db.session.commit()

@api_ordenes.route('/', methods=['POST'])
def crear_orden():
    data = request.get_json()
    errors = []

    # Campos requeridos
    for campo in ('cotizacion_uuid', 'direccion_entrega', 'contacto_nombre', 'contacto_email', 'contacto_telefono', 'metodo_envio', 'metodo_pago'):
        if not data.get(campo):
            errors.append(f"Falta {campo}")

    if errors:
        return jsonify({'errors': errors}), 400

    # Validar cotización
    cot = Cotizacion.query.filter_by(uuid=data['cotizacion_uuid']).first()
    if not cot:
        return jsonify({'error': 'Cotización no encontrada'}), 404
    if not cot.bloqueado:
        return jsonify({'error': 'La cotización debe estar bloqueada antes de crear la orden'}), 400
    if hasattr(cot, 'orden_compra') and cot.orden_compra is not None:
        return jsonify({'error': 'Ya existe una orden para esta cotización'}), 400

    # Validar stock disponible
    stock_ok, errores_stock = validar_stock(cot)
    if not stock_ok:
        return jsonify({'error': 'No hay stock suficiente', 'detalles': errores_stock}), 400

    # Reservar stock
    reservar_stock(cot)

    # Crear orden
    nueva = OrdenCompra(
        uuid=str(uuid.uuid4()),
        cotizacion_id=cot.id,
        fecha_envio=datetime.now(timezone.utc),
        direccion_entrega=data['direccion_entrega'],
        contacto_nombre=data['contacto_nombre'],
        contacto_email=data['contacto_email'],
        contacto_telefono=data['contacto_telefono'],
        metodo_envio=data['metodo_envio'],
        metodo_pago=data['metodo_pago'],
        estado='pendiente'
    )
    db.session.add(nueva)
    db.session.commit()

    return jsonify({'orden_uuid': nueva.uuid}), 201

@api_ordenes.route('/', methods=['DELETE'])
def eliminar_orden():
    orden_uuid = request.form.get('uuid')
    if not orden_uuid:
        return jsonify({'error': 'Se requiere el UUID de la orden'}), 400

    orden = OrdenCompra.query.filter_by(uuid=orden_uuid).first()
    if not orden:
        return jsonify({'error': 'Orden no encontrada'}), 404

    if orden.estado != 'pendiente':
        return jsonify({'error': f"No se puede eliminar una orden en estado '{orden.estado}'"}), 403

    liberar_stock(orden.cotizacion)

    db.session.delete(orden)
    db.session.commit()

    return jsonify({'mensaje': 'Orden eliminada con éxito'}), 200

@api_ordenes.route('/', methods=['GET'])
def ver_orden():
    uuid_str = request.args.get('uuid')
    api_key = request.args.get('api_key')

    if uuid_str:
        orden = OrdenCompra.query.filter_by(uuid=uuid_str).first()
        if not orden:
            return jsonify({'error': 'Orden no encontrada'}), 404

        cot = orden.cotizacion
        productos = []
        for cp in cot.productos:
            productos.append({
                'id': cp.producto.id,
                'nombre': cp.producto.nombre,
                'cantidad': cp.cantidad,
                'precio_unitario': cp.precio_unitario,
                'subtotal': cp.precio_unitario * cp.cantidad
            })

        return jsonify({
            'uuid': orden.uuid,
            'estado': orden.estado,
            'fecha_envio': orden.fecha_envio.isoformat() if orden.fecha_envio else None,
            'direccion_entrega': orden.direccion_entrega,
            'contacto_nombre': orden.contacto_nombre,
            'contacto_email': orden.contacto_email,
            'contacto_telefono': orden.contacto_telefono,
            'metodo_envio': orden.metodo_envio,
            'metodo_pago': orden.metodo_pago,
            'productos': productos
        }), 200

    elif api_key:
        if not valid_api_key(api_key):
            return jsonify({'error': 'La api-key es inválida'}), 401

        ordenes = OrdenCompra.query.all()
        resultado = []
        for orden in ordenes:
            cot = orden.cotizacion
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
                'id': orden.id,
                'uuid': orden.uuid,
                'estado': orden.estado,
                'fecha_envio': orden.fecha_envio.isoformat() if orden.fecha_envio else None,
                'direccion_entrega': orden.direccion_entrega,
                'contacto_nombre': orden.contacto_nombre,
                'contacto_email': orden.contacto_email,
                'contacto_telefono': orden.contacto_telefono,
                'metodo_envio': orden.metodo_envio,
                'metodo_pago': orden.metodo_pago,
                'productos': productos
            })

        return jsonify(resultado), 200

    else:
        return jsonify({'error': 'Se requiere el parámetro "uuid" o una api-key'}), 400

@api_ordenes.route('/', methods=['PATCH'])
def modificar_orden():
    uuid_str = request.form.get('uuid')
    api_key = request.form.get('api_key')

    if not uuid_str:
        return jsonify({'error': 'Se requiere el UUID'}), 400

    orden = OrdenCompra.query.filter_by(uuid=uuid_str).first()
    if not orden:
        return jsonify({'error': 'Orden no encontrada'}), 404

    if orden.estado != 'pendiente':
        return jsonify({'error': 'Solo se pueden modificar órdenes en estado pendiente'}), 403

    # Solo actualizar campos permitidos (NO estado)
    if 'direccion_entrega' in request.form:
        orden.direccion_entrega = request.form['direccion_entrega']
    if 'contacto_nombre' in request.form:
        orden.contacto_nombre = request.form['contacto_nombre']
    if 'contacto_email' in request.form:
        orden.contacto_email = request.form['contacto_email']
    if 'contacto_telefono' in request.form:
        orden.contacto_telefono = request.form['contacto_telefono']
    if 'metodo_envio' in request.form:
        orden.metodo_envio = request.form['metodo_envio']
    if 'metodo_pago' in request.form:
        orden.metodo_pago = request.form['metodo_pago']
    
    # Intento de modificar estado:
    if 'estado' in request.form:
        if api_key and valid_api_key(api_key):
            orden.estado = request.form['estado']
        else:
            return jsonify({'error': 'Se requiere API key válida para modificar el estado'}), 401
    db.session.commit()
    return jsonify({'mensaje': 'Orden actualizada con éxito'}), 200

@api_ordenes.route('/estado', methods=['PATCH'])
@require_api_key
def cambiar_estado_orden():
    uuid_str = request.form.get('uuid')
    nuevo_estado = request.form.get('estado')

    if not uuid_str or not nuevo_estado:
        return jsonify({'error': 'Se requieren uuid y estado'}), 400

    orden = OrdenCompra.query.filter_by(uuid=uuid_str).first()
    if not orden:
        return jsonify({'error': 'Orden no encontrada'}), 404

    if orden.estado == "pagado" and nuevo_estado == "enviando":
        consumir_stock(orden.cotizacion)
    orden.estado = nuevo_estado
    db.session.commit()

    return jsonify({'mensaje': 'Estado de orden actualizado correctamente'}), 200