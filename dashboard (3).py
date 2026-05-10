from flask import Blueprint, jsonify
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
        "liderancas": liderancas
    })