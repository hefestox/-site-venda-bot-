import csv
import io
from flask import Blueprint, jsonify, request, Response
from db import get_conn, release_conn
from auth_middleware import auth_required

dashboard_routes = Blueprint("dashboard", __name__)


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


@dashboard_routes.route("/", methods=["GET"])
@auth_required
def dashboard():
    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM pessoas")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM pessoas WHERE lideranca != 'Nenhuma'")
            liderancas_count = cur.fetchone()[0]
    finally:
        release_conn(c)
    return jsonify({"total": total, "liderancas": liderancas_count})


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

        c = get_conn()
        try:
            with c.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
        finally:
            release_conn(c)
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

    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute(
                """INSERT INTO pessoas (nome, endereco, telefone, municipio, data_nascimento, lideranca)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   RETURNING id, nome, endereco, telefone, municipio, data_nascimento, lideranca""",
                (nome, endereco, telefone, municipio, data_nascimento, lideranca),
            )
            row = cur.fetchone()
        c.commit()
    except Exception as e:
        c.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        release_conn(c)

    return jsonify({"ok": True, "pessoa": _row_to_dict(row)}), 201


@dashboard_routes.route("/pessoas/<int:pessoa_id>", methods=["DELETE"])
@auth_required
def deletar_pessoa(pessoa_id):
    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("DELETE FROM pessoas WHERE id = %s RETURNING id", (pessoa_id,))
            row = cur.fetchone()
        if not row:
            return jsonify({"error": "Pessoa não encontrada."}), 404
        c.commit()
    except Exception as e:
        c.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        release_conn(c)

    return jsonify({"ok": True, "deleted_id": pessoa_id})


@dashboard_routes.route("/exportar-csv", methods=["GET"])
@auth_required
def exportar_csv():
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

    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
    finally:
        release_conn(c)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Nome", "Endereço", "Telefone", "Município", "Data de Nascimento", "Liderança"])
    for row in rows:
        writer.writerow([
            row[0], row[1], row[2] or "", row[3] or "",
            row[4], str(row[5]) if row[5] else "", row[6]
        ])

    output.seek(0)
    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=campanha_pessoas.csv"}
    )
