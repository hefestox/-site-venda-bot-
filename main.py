import os
import bcrypt
from flask import Flask, jsonify, render_template, redirect, request
from flask_cors import CORS
from db import get_conn, release_conn

app = Flask(__name__, template_folder='templates')
CORS(app)

def init_db():
    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id        SERIAL PRIMARY KEY,
                email     TEXT UNIQUE,
                senha     TEXT,
                role      TEXT,
                municipio TEXT
            );
            CREATE TABLE IF NOT EXISTS pessoas (
                id               SERIAL PRIMARY KEY,
                nome             TEXT NOT NULL,
                endereco         TEXT,
                telefone         TEXT,
                municipio        TEXT NOT NULL,
                data_nascimento  DATE,
                lideranca        TEXT DEFAULT 'Nenhuma',
                bairro           TEXT,
                zona_eleitoral   TEXT,
                secao_eleitoral  TEXT,
                partido          TEXT,
                status           TEXT DEFAULT 'Indefinido',
                votos_declarados INTEGER DEFAULT 0
            );
            """)
            # Migrações para bancos existentes
            for col, tipo in [
                ('bairro','TEXT'),('zona_eleitoral','TEXT'),
                ('secao_eleitoral','TEXT'),('partido','TEXT'),
                ('status',"TEXT DEFAULT 'Indefinido'"),
                ('votos_declarados','INTEGER DEFAULT 0'),
                ('municipio_usuario','TEXT'),
            ]:
                try:
                    cur.execute(f"ALTER TABLE pessoas ADD COLUMN IF NOT EXISTS {col.split()[0]} {tipo}")
                except: pass
            try:
                cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS municipio TEXT")
            except: pass
        c.commit()
        print("✅ Banco inicializado!")
    except Exception as e:
        c.rollback(); print("❌ Erro:", e); raise e
    finally:
        release_conn(c)

init_db()

from auth import auth_routes
from dashboard import dashboard_routes
app.register_blueprint(auth_routes, url_prefix="/auth")
app.register_blueprint(dashboard_routes, url_prefix="/dashboard")

@app.route("/", methods=["GET"])
def home(): return redirect("/app")

@app.route("/app", methods=["GET"])
def frontend(): return render_template("index.html")

@app.route("/ping", methods=["GET"])
def ping(): return jsonify({"status": "ok"})

@app.route("/reset-db", methods=["POST"])
def reset_db():
    secret   = os.getenv("RESET_SECRET","")
    provided = request.headers.get("X-Reset-Secret","")
    if not secret or provided != secret:
        return jsonify({"error": "Não autorizado"}), 403
    c = get_conn()
    try:
        with c.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS pessoas CASCADE")
            cur.execute("DROP TABLE IF EXISTS usuarios CASCADE")
            cur.execute("""
            CREATE TABLE usuarios (id SERIAL PRIMARY KEY, email TEXT UNIQUE, senha TEXT, role TEXT, municipio TEXT);
            CREATE TABLE pessoas (
                id SERIAL PRIMARY KEY, nome TEXT NOT NULL, endereco TEXT, telefone TEXT,
                municipio TEXT NOT NULL, data_nascimento DATE, lideranca TEXT DEFAULT 'Nenhuma',
                bairro TEXT, zona_eleitoral TEXT, secao_eleitoral TEXT, partido TEXT,
                status TEXT DEFAULT 'Indefinido', votos_declarados INTEGER DEFAULT 0
            );
            """)
            hashed = bcrypt.hashpw("admin991714827".encode(), bcrypt.gensalt()).decode()
            cur.execute("INSERT INTO usuarios (email,senha,role) VALUES (%s,%s,%s)",("admin@campanhaacre.com",hashed,"admin"))
        c.commit()
    except Exception as e:
        c.rollback(); return jsonify({"error":str(e)}), 500
    finally:
        release_conn(c)
    return jsonify({"message":"Resetado","login":"admin@campanhaacre.com","senha":"admin991714827"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT",3000))
    app.run(host="0.0.0.0", port=port)
