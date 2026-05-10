from flask import Blueprint, request, jsonify
from db import conn
import bcrypt
import jwt
import os

auth_routes = Blueprint("auth", __name__)

@auth_routes.route("/register", methods=["POST"])
def register():
    # Only admins may create new users
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Acesso negado: token não fornecido"}), 403

    try:
        decoded = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
    except Exception:
        return jsonify({"error": "Token inválido"}), 403

    if decoded.get("role") != "admin":
        return jsonify({"error": "Acesso negado: apenas administradores podem criar usuários"}), 403

    data = request.json
    senha = bcrypt.hashpw(data['senha'].encode(), bcrypt.gensalt()).decode()

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO usuarios (email, senha, role) VALUES (%s,%s,%s) RETURNING id",
            (data['email'], senha, data['role'])
        )
        user_id = cur.fetchone()[0]
        conn.commit()

    return jsonify({"id": user_id}), 201

@auth_routes.route("/login", methods=["POST"])
def login():
    data = request.json

    with conn.cursor() as cur:
        cur.execute("SELECT * FROM usuarios WHERE email=%s", (data['email'],))
        user = cur.fetchone()

    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 400

    if not bcrypt.checkpw(data['senha'].encode(), user[2].encode()):
        return jsonify({"error": "Senha inválida"}), 400

    token = jwt.encode({"id": user[0], "role": user[3]}, os.getenv("JWT_SECRET"), algorithm="HS256")

    return jsonify({"token": token})
