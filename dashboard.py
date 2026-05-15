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
        cur.execute("SELECT COUNT(*) FROM pessoas WHERE lideranca != 'Nenhuma'")
        liderancas_count = cur.fetchone()[0]
    return jsonify({
        "total": total,
        "liderancas": liderancas_count,
    })


def _row_to_dict(row):
    return {
        "id":               row[0],
        "nome":             row[1],
        "endereco":         row[2],
        "telefone":         row[3],
        "municipio":        row[4],
        "data_nascimento":  str(row[5]) if row[5] else "",
        "lideranca":        row[6],
    }


@dashboard_routes.route("/pessoas", methods=["GET", "POST"])
@auth_required
def pessoas():
    if request.method == "GET":
        municipio = request.args.get("municipio", "").strip()
        lideranca = request.args.get("lideranca", "").strip()

        query = "SELECT id, nome, endereco, telefone, municipio, data_nascimento, lideranca FROM pessoas"
        filters, params = [], []

        if municipio:
            filters.append("municipio = %s")
            params.append(municipio)
        if lideranca:
            filters.append("lideranca = %s")
            params.append(lideranca)

        if filters:
            query += " WHERE " + " AND ".join(filters)
        query += " ORDER BY id DESC"

        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        return jsonify({"pessoas": [_row_to_dict(r) for r in rows]})

    # POST
    data            = request.get_json(silent=True) or {}
    nome            = (data.get("nome")            or "").strip()
    endereco        = (data.get("endereco")        or "").strip()
    telefone        = (data.get("telefone")        or "").strip()
    municipio       = (data.get("municipio")       or "").strip()
    data_nascimento = data.get("data_nascimento")  or None
    lideranca       = (data.get("lideranca")       or "Nenhuma").strip()

    if not nome or not municipio:
        return jsonify({"error": "Nome e município são obrigatórios."}), 400

    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO pessoas (nome, endereco, telefone, municipio, data_nascimento, lideranca)
               VALUES (%s, %s, %s, %s, %s, %s)
               RETURNING id, nome, endereco, telefone, municipio, data_nascimento, lideranca""",
            (nome, endereco, telefone, municipio, data_nascimento, lideranca),
        )
        row = cur.fetchone()
    conn.commit()
    return jsonify({"ok": True, "pessoa": _row_to_dict(row)}), 201


@dashboard_routes.route("/pessoas/<int:pessoa_id>", methods=["DELETE"])
@auth_required
def deletar_pessoa(pessoa_id):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM pessoas WHERE id = %s RETURNING id", (pessoa_id,))
        row = cur.fetchone()
    if not row:
        return jsonify({"error": "Pessoa não encontrada."}), 404
    conn.commit()
    return jsonify({"ok": True, "deleted_id": pessoa_id})
