from flask import request, jsonify, current_app
from functools import wraps

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