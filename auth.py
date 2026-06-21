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
    data      = request.get_json(silent=True) or {}
    email     = (data.get("email")     or "").strip()
    senha     = (data.get("senha")     or "").strip()
    role      = (data.get("role")      or "operador").strip()
    municipio = (data.get("municipio") or "").strip()

    if not email or not senha:
        return jsonify({"error": "Email e senha são obrigatórios."}), 400

    # Coordenador precisa ter município definido
    if role == "coordenador" and not municipio:
        return jsonify({"error": "Coordenador precisa ter um município."}), 400

    hashed = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute(
                "INSERT INTO usuarios (email, senha, role, municipio) VALUES (%s, %s, %s, %s) RETURNING id",
                (email, hashed, role, municipio or None)
            )
            user_id = cur.fetchone()[0]
        c.commit()
    except Exception as e:
        c.rollback()
        if "unique" in str(e).lower():
            return jsonify({"error": "E-mail já cadastrado."}), 409
        return jsonify({"error": str(e)}), 500
    finally:
        release_conn(c)

    return jsonify({"id": user_id}), 201


@auth_routes.route("/login", methods=["POST"])
def login():
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    senha = (data.get("senha") or "").strip()

    if not email or not senha:
        return jsonify({"error": "Email e senha são obrigatórios."}), 400

    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT id, email, senha, role, municipio FROM usuarios WHERE email = %s", (email,))
            user = cur.fetchone()
    finally:
        release_conn(c)

    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 400

    if not bcrypt.checkpw(senha.encode(), user[2].encode()):
        return jsonify({"error": "Senha inválida"}), 400

    token = jwt.encode(
        {"id": user[0], "role": user[3], "municipio": user[4] or ""},
        os.getenv("JWT_SECRET"),
        algorithm="HS256"
    )
    return jsonify({"token": token})


@auth_routes.route("/usuarios", methods=["GET"])
@admin_required
def listar_usuarios():
    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT id, email, role, municipio FROM usuarios ORDER BY id DESC")
            rows = cur.fetchall()
    finally:
        release_conn(c)
    return jsonify({"usuarios": [
        {"id": r[0], "email": r[1], "role": r[2], "municipio": r[3] or ""}
        for r in rows
    ]})


@auth_routes.route("/usuarios/<int:user_id>", methods=["DELETE"])
@admin_required
def deletar_usuario(user_id):
    # Não deixa deletar o próprio usuário
    if request.user.get("id") == user_id:
        return jsonify({"error": "Você não pode deletar seu próprio usuário."}), 400

    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("DELETE FROM usuarios WHERE id = %s RETURNING id", (user_id,))
            row = cur.fetchone()
        if not row:
            return jsonify({"error": "Usuário não encontrado."}), 404
        c.commit()
    except Exception as e:
        c.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        release_conn(c)
    return jsonify({"ok": True})
