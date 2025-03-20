from fastapi import FastAPI, HTTPException, Depends
import sqlite3
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import uvicorn

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("api.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()
app = FastAPI()

# Definição de modelos Pydantic para validação de dados
class MensagemRequest(BaseModel):
    mensagem: str

class Mensagem(BaseModel):
    id: int
    conversa_id: int
    tipo: str  # "enviada" ou "recebida"
    mensagem: str
    respondida: bool

class Conversa(BaseModel):
    id: int
    email: str
    anuncio_id: str
    mensagens: List[Mensagem]

# Função para conectar ao banco de dados
def get_db():
    try:
        conn = sqlite3.connect("mensagens.db")
        conn.row_factory = sqlite3.Row  # Permite acessar resultados por nome de coluna
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {e}")
        raise

# Criar tabelas no banco de dados
def criar_tabelas():
    """Cria as tabelas no banco de dados"""
    try:
        logger.info("Iniciando criação/verificação das tabelas...")
        with get_db() as conn:
            # Verifica se o banco existe
            if not os.path.exists("mensagens.db"):
                logger.info("Banco de dados não encontrado, criando novo...")
            
            # Cria tabela de conversas
            logger.info("Criando/verificando tabela de conversas...")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    anuncio_id TEXT NOT NULL,
                    UNIQUE(email, anuncio_id)
                )
            """)
            
            # Cria tabela de mensagens
            logger.info("Criando/verificando tabela de mensagens...")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mensagens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversa_id INTEGER NOT NULL,
                    tipo TEXT CHECK(tipo IN ('enviada', 'recebida')) NOT NULL,
                    mensagem TEXT NOT NULL,
                    respondida BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (conversa_id) REFERENCES conversas (id)
                )
            """)
            
            conn.commit()
            logger.info("Tabelas criadas/verificadas com sucesso")
            
            # Verifica se as tabelas foram criadas
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            logger.info(f"Tabelas existentes no banco: {[table[0] for table in tables]}")
            
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        raise

# Criar tabelas ao iniciar a API
criar_tabelas()

@app.get("/conversas/pendentes/{email}")
def buscar_conversas_pendentes(email: str):
    """Retorna conversas com mensagens recebidas não respondidas"""
    try:
        with get_db() as conn:
            conversas = conn.execute(
                """
                SELECT c.id, c.email, c.anuncio_id, m.id, m.tipo, m.mensagem, m.respondida
                FROM conversas c
                JOIN mensagens m ON c.id = m.conversa_id
                WHERE c.email = ?
                AND m.tipo = 'recebida'
                AND m.respondida = FALSE
                ORDER BY c.id, m.id
                """,
                (email,),
            ).fetchall()

            resultado = {}
            for conv in conversas:
                if conv["id"] not in resultado:
                    resultado[conv["id"]] = {
                        "id": conv["id"],
                        "email": conv["email"],
                        "anuncio_id": conv["anuncio_id"],
                        "mensagens": [],
                    }
                resultado[conv["id"]]["mensagens"].append(
                    {
                        "id": conv["id"],
                        "conversa_id": conv["id"],
                        "tipo": conv["tipo"],
                        "mensagem": conv["mensagem"],
                        "respondida": bool(conv["respondida"]),
                    }
                )

            logger.info(f"Buscadas {len(resultado)} conversas pendentes na DB")
            return {"conversas_pendentes": list(resultado.values())}
    except Exception as e:
        logger.error(f"Erro ao buscar conversas pendentes na DB: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar conversas")

@app.post("/enviar-mensagem/{email}/{anuncio_id}")
def enviar_mensagem(email: str, anuncio_id: str, mensagem_data: MensagemRequest):
    """Registra uma mensagem enviada e marca todas as mensagens recebidas anteriores como respondidas"""
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO conversas (email, anuncio_id) VALUES (?, ?)",
                (email, anuncio_id),
            )
            conversa = conn.execute(
                "SELECT id FROM conversas WHERE email = ? AND anuncio_id = ?",
                (email, anuncio_id),
            ).fetchone()

            if not conversa:
                raise HTTPException(status_code=400, detail="Erro ao criar conversa")

            conn.execute(
                """
                UPDATE mensagens
                SET respondida = TRUE
                WHERE conversa_id = ?
                AND tipo = 'recebida'
                """,
                (conversa["id"],),
            )

            conn.execute(
                """
                INSERT INTO mensagens (conversa_id, tipo, mensagem, respondida)
                VALUES (?, 'enviada', ?, FALSE)
                """,
                (conversa["id"], mensagem_data.mensagem),
            )

            conn.commit()
            return {"status": "Mensagem enviada e mensagens anteriores marcadas como respondidas"}
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem na DB: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao enviar mensagem")

@app.post("/receber-mensagem/{email}/{anuncio_id}")
def receber_mensagem(email: str, anuncio_id: str, mensagem_data: MensagemRequest, tipo: str):
    """Registra uma mensagem recebida ou enviada"""
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO conversas (email, anuncio_id) VALUES (?, ?)",
                (email, anuncio_id),
            )
            conversa = conn.execute(
                "SELECT id FROM conversas WHERE email = ? AND anuncio_id = ?",
                (email, anuncio_id),
            ).fetchone()

            if not conversa:
                raise HTTPException(status_code=400, detail="Erro ao criar conversa")

            # Se a mensagem for recebida, marca todas as enviadas como respondidas
            if tipo == 'recebida':
                conn.execute(
                    """
                    UPDATE mensagens
                    SET respondida = TRUE
                    WHERE conversa_id = ?
                    AND tipo = 'enviada'
                    """,
                    (conversa["id"],),
                )
            # Se a mensagem for enviada, marca todas as recebidas como respondidas
            elif tipo == 'enviada':
                conn.execute(
                    """
                    UPDATE mensagens
                    SET respondida = TRUE
                    WHERE conversa_id = ?
                    AND tipo = 'recebida'
                    """,
                    (conversa["id"],),
                )

            conn.execute(
                """
                INSERT INTO mensagens (conversa_id, tipo, mensagem, respondida)
                VALUES (?, ?, ?, FALSE)
                """,
                (conversa["id"], tipo, mensagem_data.mensagem),
            )

            conn.commit()
            return {"status": f"Mensagem {tipo} registrada com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao receber mensagem na DB: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao receber mensagem")

@app.get("/mensagem-existe/{email}/{anuncio_id}")
def verificar_mensagem_existe(email: str, anuncio_id: str, mensagem: str, tipo: str):
    """Verifica se uma mensagem já existe na DB para um anúncio específico"""
    try:
        with get_db() as conn:
            # Busca a conversa
            conversa = conn.execute("SELECT id FROM conversas WHERE email = ? AND anuncio_id = ?", 
                                  (email, anuncio_id)).fetchone()
            
            if not conversa:
                logger.info(f"Conversa não encontrada para anuncio_id: {anuncio_id}")
                return {"existe": False}
            
            # Verifica se a mensagem já existe
            mensagem_existe = conn.execute("""
                SELECT COUNT(*) FROM mensagens 
                WHERE conversa_id = ? 
                AND mensagem = ?
                AND tipo = ?
            """, (conversa["id"], mensagem, tipo)).fetchone()[0] > 0
            
            logger.info(f"Verificação de mensagem para anuncio_id {anuncio_id}: {'existe' if mensagem_existe else 'não existe'}")
            return {"existe": mensagem_existe}
    except Exception as e:
        logger.error(f"Erro ao verificar mensagem na DB: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao verificar mensagem: {str(e)}")

if __name__ == "__main__":
    logger.info("Iniciando servidor FastAPI")
    uvicorn.run(app, host="localhost", port=8000)
