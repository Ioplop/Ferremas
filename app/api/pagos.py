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
from transbank.webpay.webpay_plus.transaction import Transaction, WebpayOptions
from transbank.common.integration_type import IntegrationType
from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes


api_pagos = Blueprint('api_pagos', __name__, url_prefix='/api/pagos')

@api_pagos.route('/', methods=['POST'])
def pagar_orden():
    orden_uuid = request.form.get('orden_uuid')
    if not orden_uuid:
        return jsonify({'mensaje' : 'Debe ingresar orden_uuid'}), 400
    orden_query = OrdenCompra.query
    
    # Obtener orden asociada a uuid
    orden : OrdenCompra = orden_query.filter_by(uuid=orden_uuid).first()
    # Validar que se encontro una orden de compra
    if not orden:
        return jsonify({'mensaje' : 'Orden de compra no encontrada'}), 404

    # Cambiar estado de orden a "pagando"
    orden.estado = "pagando"
    db.session.commit()

    # Obtener valor de la orden de compra
    total = orden.cotizacion.total

    # Luego debemos crear la transaccion en transbank
    # https://webpay3g.transbank.cl (ambiente produccion)
    # https://webpay3gint.transbank.cl/ (ambiente integracion)
    
    # Transaction viene configurado por defecto con opciones de integracion (de entorno desarrollo)
    options = WebpayOptions(IntegrationCommerceCodes.WEBPAY_PLUS, IntegrationApiKeys.WEBPAY, IntegrationType.TEST)
    tx = Transaction(options=options)
    response = tx.create(
        session_id=str(uuid.uuid4())[:12],
        buy_order=str(orden.id),
        amount=total,
        return_url="http://127.0.0.1:5001/static/index.html"
    )
    
    token = response['token']
    url = response['url']
    orden.transaccion = token
    orden.url = url
    db.session.commit()
    return jsonify({"url_pago": url, "token":token}), 201


@api_pagos.route('/', methods=['PATCH'])
def validar_orden():
    orden_uuid = request.form.get('orden_uuid')
    if not orden_uuid:
        return jsonify({'mensaje' : 'Debe ingresar orden_uuid'}), 400
    orden_query = OrdenCompra.query
    
    # Obtener orden asociada a uuid
    orden : OrdenCompra = orden_query.filter_by(uuid=orden_uuid).first()
    # Validar que se encontro una orden de compra
    if not orden:
        return jsonify({'mensaje' : 'Orden de compra no encontrada'}), 404
    
    tx = Transaction.build_for_integration(IntegrationCommerceCodes.WEBPAY_PLUS, IntegrationApiKeys.WEBPAY)
    resp = tx.commit(orden.transaccion)
    resultado = None
    if resp['status'] == "AUTHORIZED":
        orden.estado = "pagado"
        resultado = jsonify({"mensaje": "transaccion autorizada"}), 200
    else:
        orden.estado = "fallido"
        resultado = jsonify({"mensaje": "transaccion fallida"}), 400

    db.session.commit()
    return resultado