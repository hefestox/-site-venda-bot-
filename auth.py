import os
import bcrypt
import jwt
from flask import Blueprint, request, jsonify
from db import get_conn, release_conn
from auth_middleware import admin_required

auth_routes = Blueprint("auth", __name__)


@auth_routes.route("/register", methods=["POST"])
@admin_required
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    senha = (data.get("senha") or "").strip()
    role  = (data.get("role")  or "usuario").strip()

    if not email or not senha:
        return jsonify({"error": "Email e senha são obrigatórios."}), 400

    hashed = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute(
                "INSERT INTO usuarios (email, senha, role) VALUES (%s, %s, %s) RETURNING id",
                (email, hashed, role)
            )
            user_id = cur.fetchone()[0]
        c.commit()
    except Exception as e:
        c.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        release_conn(c)

    return jsonify({"id": user_id}), 201


@auth_routes.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    senha = (data.get("senha") or "").strip()

    if not email or not senha:
        return jsonify({"error": "Email e senha são obrigatórios."}), 400

    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT id, email, senha, role FROM usuarios WHERE email = %s", (email,))
            user = cur.fetchone()
    finally:
        release_conn(c)

    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 400

    if not bcrypt.checkpw(senha.encode(), user[2].encode()):
        return jsonify({"error": "Senha inválida"}), 400

    token = jwt.encode(
        {"id": user[0], "role": user[3]},
        os.getenv("JWT_SECRET"),
        algorithm="HS256"
    )
    return jsonify({"token": token})
