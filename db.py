import os
import psycopg2
import psycopg2.pool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("DATABASE_URL não encontrada nas variáveis de ambiente")

try:
    _pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        dsn=DATABASE_URL,
        sslmode="require"
    )
    print("✅ Pool de conexões criado com sucesso!")
except Exception as e:
    print("❌ Erro ao conectar no PostgreSQL:")
    print(e)
    raise e


def get_conn():
    """Pega uma conexão do pool."""
    return _pool.getconn()


def release_conn(c):
    """Devolve a conexão ao pool."""
    _pool.putconn(c)
