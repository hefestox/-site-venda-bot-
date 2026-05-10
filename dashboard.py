from flask import Blueprint, jsonify, request
from db import conn
from auth_middleware import auth_required

dashboard_routes = Blueprint("dashboard", __name__)


@dashboard_routes.route("/", methods=["GET"])
@auth_required
def dashboard():
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM pessoas")
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM liderancas")
        liderancas = cur.fetchone()[0]

    return jsonify({
        "total": total,
        "liderancas": liderancas,
    })


def _row_to_dict(row):
    return {"id": row[0], "nome": row[1], "municipio": row[2]}


@dashboard_routes.route("/pessoas", methods=["GET", "POST"])
@auth_required
def pessoas():
    if request.method == "GET":
        with conn.cursor() as cur:
            cur.execute("SELECT id, nome, municipio FROM pessoas ORDER BY id DESC")
            rows = cur.fetchall()
        return jsonify({"pessoas": [_row_to_dict(r) for r in rows]})

    data = request.get_json(silent=True) or {}
    nome = (data.get("nome") or "").strip()
    municipio = (data.get("municipio") or "").strip()
    if not nome or not municipio:
        return jsonify({"error": "Nome e município são obrigatórios."}), 400

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO pessoas (nome, municipio) VALUES (%s, %s) RETURNING id, nome, municipio",
            (nome, municipio),
        )
        row = cur.fetchone()

    return jsonify({"ok": True, "pessoa": _row_to_dict(row)}), 201


@dashboard_routes.route("/liderancas", methods=["GET", "POST"])
@auth_required
def liderancas():
    if request.method == "GET":
        with conn.cursor() as cur:
            cur.execute("SELECT id, nome, municipio FROM liderancas ORDER BY id DESC")
            rows = cur.fetchall()
        return jsonify({"liderancas": [_row_to_dict(r) for r in rows]})

    data = request.get_json(silent=True) or {}
    nome = (data.get("nome") or "").strip()
    municipio = (data.get("municipio") or "").strip()
    if not nome or not municipio:
        return jsonify({"error": "Nome e município são obrigatórios."}), 400

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO liderancas (nome, municipio) VALUES (%s, %s) RETURNING id, nome, municipio",
            (nome, municipio),
        )
        row = cur.fetchone()

    return jsonify({"ok": True, "lideranca": _row_to_dict(row)}), 201
