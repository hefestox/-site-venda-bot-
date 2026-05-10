from flask import Flask, jsonify, render_template
from flask_cors import CORS
from db import conn
import bcrypt as _bcrypt

app = Flask(__name__, template_folder='templates')
CORS(app)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to Site Venda Bot API", "status": "running"})


@app.route("/app", methods=["GET"])
def frontend():
    return render_template("index.html")


# Criar tabelas

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

# Insert default admin user if not exists
with conn.cursor() as cur:
    cur.execute("SELECT id FROM usuarios WHERE email = %s", ("admin@campanha.com",))
    if not cur.fetchone():
        _hashed = _bcrypt.hashpw("admin123".encode(), _bcrypt.gensalt()).decode()
        cur.execute(
            "INSERT INTO usuarios (email, senha, role) VALUES (%s, %s, %s)",
            ("admin@campanha.com", _hashed, "admin")
        )
        conn.commit()

# Rotas
from auth import auth_routes
from dashboard import dashboard_routes

app.register_blueprint(auth_routes, url_prefix="/auth")
app.register_blueprint(dashboard_routes, url_prefix="/dashboard")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
