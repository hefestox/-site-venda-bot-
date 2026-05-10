from collections import defaultdict

from flask import Blueprint, jsonify, request
from db import conn
from auth_middleware import auth_required

dashboard_routes = Blueprint("dashboard", __name__)


# ── Coordenadas aproximadas (centro) dos municípios do Acre ──
AC_MUNICIPIOS_COORDS = {
    "Acrelândia": (-9.8258, -66.8972),
    "Assis Brasil": (-10.9428, -69.5658),
    "Brasiléia": (-10.9948, -68.7487),
    "Bujari": (-9.8153, -67.9550),
    "Capixaba": (-10.5680, -67.6861),
    "Cruzeiro do Sul": (-7.6276, -72.6756),
    "Epitaciolândia": (-11.0188, -68.7424),
    "Feijó": (-8.1705, -70.3510),
    "Jordão": (-9.4309, -71.8974),
    "Mâncio Lima": (-7.6166, -72.8997),
    "Manoel Urbano": (-8.8329, -69.2679),
    "Marechal Thaumaturgo": (-8.9389, -72.7908),
    "Plácido de Castro": (-10.2806, -67.1856),
    "Porto Acre": (-9.5814, -67.5478),
    "Porto Walter": (-8.2683, -72.7437),
    "Rio Branco": (-9.9754, -67.8243),
    "Rodrigues Alves": (-7.7386, -72.6619),
    "Santa Rosa do Purus": (-9.4464, -70.4902),
    "Senador Guiomard": (-10.1497, -67.7362),
    "Sena Madureira": (-9.0659, -68.6569),
    "Tarauacá": (-8.1614, -70.7657),
    "Xapuri": (-10.6516, -68.4969),
}


def _norm_municipio(nome: str) -> str:
    if not nome:
        return ""
    return " ".join(nome.strip().split())


def _row_to_dict(row):
    return {"id": row[0], "nome": row[1], "municipio": row[2]}


@dashboard_routes.route("/", methods=["GET"])
@auth_required
def dashboard():
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM pessoas")
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM liderancas")
        liderancas_count = cur.fetchone()[0]

    return jsonify({
        "total": total,
        "liderancas": liderancas_count,
    })


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


@dashboard_routes.route("/mapa", methods=["GET"])
@auth_required
def mapa_dados():
    agg = defaultdict(lambda: {"pessoas": 0, "liderancas": 0})

    with conn.cursor() as cur:
        cur.execute("SELECT municipio, COUNT(*) FROM pessoas GROUP BY municipio")
        for municipio, cnt in cur.fetchall():
            key = _norm_municipio(municipio or "")
            if key:
                agg[key]["pessoas"] = int(cnt)

        cur.execute("SELECT municipio, COUNT(*) FROM liderancas GROUP BY municipio")
        for municipio, cnt in cur.fetchall():
            key = _norm_municipio(municipio or "")
            if key:
                agg[key]["liderancas"] = int(cnt)

    pontos = []
    for municipio, dados in agg.items():
        coords = AC_MUNICIPIOS_COORDS.get(municipio)
        if not coords:
            continue
        lat, lng = coords
        total = dados["pessoas"] + dados["liderancas"]
        pontos.append({
            "municipio": municipio,
            "lat": lat,
            "lng": lng,
            "pessoas": dados["pessoas"],
            "liderancas": dados["liderancas"],
            "total": total,
        })

    pontos.sort(key=lambda x: x["total"], reverse=True)

    return jsonify({
        "pontos": pontos,
        "centro": {"lat": -9.0238, "lng": -70.8120, "zoom": 7},
    })
