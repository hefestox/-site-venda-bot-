from flask import Flask, jsonify, render_template, redirect
from flask_cors import CORS
from db import conn
import bcrypt
import os

app = Flask(__name__, template_folder='templates')
CORS(app)

# ================= HOME =================
@app.route("/", methods=["GET"])
def home():
    return redirect("/app")

# ================= FRONTEND =================
@app.route("/app", methods=["GET"])
def frontend():
    return render_template("index.html")

# ================= INIT DB =================
with conn.cursor() as cur:
    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        email TEXT,
        senha TEXT,
        role TEXT
    );

    CREATE TABLE IF NOT EXISTS pessoas (
        id SERIAL PRIMARY KEY,
        nome TEXT,
        municipio TEXT
    );

    CREATE TABLE IF NOT EXISTS liderancas (
        id SERIAL PRIMARY KEY,
        nome TEXT,
        municipio TEXT
    );
    """)

# ================= IMPORT ROTAS =================
from auth import auth_routes
from dashboard import dashboard_routes

app.register_blueprint(auth_routes, url_prefix="/auth")
app.register_blueprint(dashboard_routes, url_prefix="/dashboard")

# ================= RESET DB =================
@app.route("/reset-db", methods=["POST"])
def reset_db():
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS liderancas CASCADE")
        cur.execute("DROP TABLE IF EXISTS pessoas CASCADE")
        cur.execute("DROP TABLE IF EXISTS usuarios CASCADE")

        cur.execute("""
        CREATE TABLE usuarios (
            id SERIAL PRIMARY KEY,
            email TEXT,
            senha TEXT,
            role TEXT
        );

        CREATE TABLE pessoas (
            id SERIAL PRIMARY KEY,
            nome TEXT,
            municipio TEXT
        );

        CREATE TABLE liderancas (
            id SERIAL PRIMARY KEY,
            nome TEXT,
            municipio TEXT
        );
        """)

        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()

        cur.execute(
            "INSERT INTO usuarios (email, senha, role) VALUES (%s, %s, %s)",
            ("admin@campanha.com", hashed, "admin")
        )

        conn.commit()

    return jsonify({
        "message": "Database resetado",
        "login": "admin@campanha.com",
        "senha": "admin123"
    })

# ================= TESTE =================
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok"})

# ================= START =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
