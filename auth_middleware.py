from flask import request, jsonify
import jwt
import os

def auth_required(f):
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