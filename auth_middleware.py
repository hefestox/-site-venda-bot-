from flask import request, jsonify
from functools import wraps
import jwt
import os

def auth_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Sem token"}), 401
        try:
            decoded = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
            request.user = decoded
        except:
            return jsonify({"error": "Token inválido"}), 401
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Sem token"}), 401
        try:
            decoded = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
            request.user = decoded
        except:
            return jsonify({"error": "Token inválido"}), 401
        if decoded.get("role") != "admin":
            return jsonify({"error": "Acesso restrito a administradores"}), 403
        return f(*args, **kwargs)
    return wrapper

def coordenador_required(f):
    """Permite admin e coordenador"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Sem token"}), 401
        try:
            decoded = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
            request.user = decoded
        except:
            return jsonify({"error": "Token inválido"}), 401
        if decoded.get("role") not in ("admin", "coordenador"):
            return jsonify({"error": "Acesso restrito a coordenadores e administradores"}), 403
        return f(*args, **kwargs)
    return wrapper
