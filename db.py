import os
import psycopg2
from dotenv import load_dotenv

# ================= LOAD ENV =================
load_dotenv()

# ================= DATABASE URL =================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL não encontrada nas variáveis de ambiente")

# ================= CONNECT =================
try:
    conn = psycopg2.connect(
        DATABASE_URL,
        sslmode="require"
    )

    conn.autocommit = True

    print("✅ Banco conectado com sucesso!")

except Exception as e:
    print("❌ Erro ao conectar no PostgreSQL:")
    print(e)
    raise e
