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
from .cotizaciones import serializar_cotizacion

api_moneda = Blueprint('api_moneda', __name__, url_prefix='/api/moneda')