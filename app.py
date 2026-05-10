from flask import Flask, jsonify, render_template, redirect
from flask_cors import CORS
from db import conn
import bcrypt

app = Flask(__name__, template_folder='templates')
CORS(app)

@app.route("/", methods=["GET"])
def home():
    return redirect("/app")


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

# Rotas
from auth import auth_routes
from dashboard import dashboard_routes

app.register_blueprint(auth_routes, url_prefix="/auth")
app.register_blueprint(dashboard_routes, url_prefix="/dashboard")


@app.route("/reset-db", methods=["POST"])
def reset_db():
    """Reset database - drop and recreate all tables with default admin"""
    with conn.cursor() as cur:
        # Drop existing tables
        cur.execute("DROP TABLE IF EXISTS liderancas CASCADE")
        cur.execute("DROP TABLE IF EXISTS pessoas CASCADE")
        cur.execute("DROP TABLE IF EXISTS usuarios CASCADE")

        # Recreate tables
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

        # Insert default admin user
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        cur.execute(
            "INSERT INTO usuarios (email, senha, role) VALUES (%s, %s, %s)",
            ("admin@campanha.com", hashed, "admin")
        )
        conn.commit()

    return jsonify({"message": "Database reset successfully", "admin_email": "admin@campanha.com", "admin_password": "admin123"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)