from fastapi import FastAPI, HTTPException
import sqlite3
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()
app = FastAPI()
OLX_EMAIL = os.getenv("OLX_USERNAME")

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

def get_db():
    """Retorna uma conexão com o banco de dados"""
    try:
        return sqlite3.connect("mensagens.db")
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {e}")
        raise

def criar_tabelas():
    """Cria as tabelas no banco de dados"""
    try:
        with get_db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    anuncio_id TEXT NOT NULL,
                    UNIQUE(email, anuncio_id)
                )
            """)
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
            logger.info("Tabelas criadas/verificadas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        raise

criar_tabelas()

@app.get("/conversas/pendentes")
def buscar_conversas_pendentes():
    """Retorna conversas com mensagens recebidas não respondidas"""
    try:
        with get_db() as conn:
            # Busca conversas com mensagens recebidas não respondidas
            conversas = conn.execute("""
                SELECT c.id, c.email, c.anuncio_id, m.id, m.tipo, m.mensagem, m.respondida
                FROM conversas c
                JOIN mensagens m ON c.id = m.conversa_id
                WHERE c.email = ? 
                AND m.tipo = 'recebida' 
                AND m.respondida = FALSE
                ORDER BY c.id, m.id
            """, (OLX_EMAIL,)).fetchall()

            # Agrupa mensagens por conversa
            resultado = {}
            for conv in conversas:
                if conv[0] not in resultado:
                    resultado[conv[0]] = {
                        "id": conv[0],
                        "email": conv[1],
                        "anuncio_id": conv[2],
                        "mensagens": []
                    }
                resultado[conv[0]]["mensagens"].append({
                    "id": conv[3],
                    "conversa_id": conv[0],
                    "tipo": conv[4],
                    "mensagem": conv[5],
                    "respondida": bool(conv[6])
                })

            logger.info(f"Buscadas {len(resultado)} conversas pendentes na DB")
            return {"conversas_pendentes": list(resultado.values())}
    except Exception as e:
        logger.error(f"Erro ao buscar conversas pendentes na DB: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar conversas")

@app.post("/enviar-mensagem/")
def enviar_mensagem(anuncio_id: str, mensagem: str):
    """Registra uma mensagem enviada e marca todas as mensagens recebidas anteriores como respondidas"""
    try:
        with get_db() as conn:
            # Cria ou obtém conversa
            conn.execute("INSERT OR IGNORE INTO conversas (email, anuncio_id) VALUES (?, ?)", 
                        (OLX_EMAIL, anuncio_id))
            conversa = conn.execute("SELECT id FROM conversas WHERE email = ? AND anuncio_id = ?", 
                                  (OLX_EMAIL, anuncio_id)).fetchone()
            
            if not conversa:
                logger.error(f"Erro ao criar conversa para anuncio_id: {anuncio_id} na DB")
                raise HTTPException(status_code=400, detail="Erro ao criar conversa")
            
            # Marca todas as mensagens recebidas anteriores como respondidas
            conn.execute("""
                UPDATE mensagens 
                SET respondida = TRUE
                WHERE conversa_id = ? 
                AND tipo = 'recebida'
            """, (conversa[0],))
            
            # Insere nova mensagem enviada
            conn.execute("""
                INSERT INTO mensagens (conversa_id, tipo, mensagem, respondida) 
                VALUES (?, 'enviada', ?, FALSE)
            """, (conversa[0], mensagem))
            
            conn.commit()  # Adiciona commit explícito
            
            logger.info(f"Mensagem enviada com sucesso na DB para anuncio_id: {anuncio_id}")
            return {"status": "Mensagem enviada e mensagens anteriores marcadas como respondidas"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem na DB: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao enviar mensagem: {str(e)}")

@app.post("/receber-mensagem/{anuncio_id}")
def receber_mensagem(anuncio_id: str, mensagem: str):
    """Registra uma mensagem recebida e marca todas as mensagens enviadas como respondidas"""
    try:
        with get_db() as conn:
            # Cria ou obtém conversa
            conn.execute("INSERT OR IGNORE INTO conversas (email, anuncio_id) VALUES (?, ?)", 
                        (OLX_EMAIL, anuncio_id))
            conversa = conn.execute("SELECT id FROM conversas WHERE email = ? AND anuncio_id = ?", 
                                  (OLX_EMAIL, anuncio_id)).fetchone()
            
            if not conversa:
                logger.error(f"Erro ao criar conversa para anuncio_id: {anuncio_id} na DB")
                raise HTTPException(status_code=400, detail="Erro ao criar conversa")
            
            # Marca todas as mensagens enviadas como respondidas
            conn.execute("""
                UPDATE mensagens 
                SET respondida = TRUE
                WHERE conversa_id = ? 
                AND tipo = 'enviada'
            """, (conversa[0],))
            
            # Insere nova mensagem recebida
            conn.execute("""
                INSERT INTO mensagens (conversa_id, tipo, mensagem, respondida) 
                VALUES (?, 'recebida', ?, FALSE)
            """, (conversa[0], mensagem))
            
            logger.info(f"Mensagem recebida com sucesso na DB para anuncio_id: {anuncio_id}")
            return {"status": "Mensagem recebida e mensagens enviadas marcadas como respondidas"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao receber mensagem na DB: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao receber mensagem")

@app.delete("/conversa/{anuncio_id}")
def remover_conversa(anuncio_id: str):
    """Remove uma conversa e suas mensagens"""
    try:
        with get_db() as conn:
            conversa = conn.execute("SELECT id FROM conversas WHERE email = ? AND anuncio_id = ?", 
                                  (OLX_EMAIL, anuncio_id)).fetchone()
            
            if not conversa:
                logger.error(f"Conversa não encontrada na DB para remoção: {anuncio_id}")
                raise HTTPException(status_code=404, detail="Conversa não encontrada")
            
            conn.execute("DELETE FROM mensagens WHERE conversa_id = ?", (conversa[0],))
            conn.execute("DELETE FROM conversas WHERE id = ?", (conversa[0],))
            
            logger.info(f"Conversa removida com sucesso na DB: {anuncio_id}")
            return {"status": "Conversa removida com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover conversa na DB: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao remover conversa")

@app.get("/mensagem-existe/{anuncio_id}")
def verificar_mensagem_existe(anuncio_id: str, mensagem: str):
    """Verifica se uma mensagem já existe na DB para um anúncio específico"""
    try:
        with get_db() as conn:
            # Busca a conversa
            conversa = conn.execute("SELECT id FROM conversas WHERE email = ? AND anuncio_id = ?", 
                                  (OLX_EMAIL, anuncio_id)).fetchone()
            
            if not conversa:
                logger.info(f"Conversa não encontrada para anuncio_id: {anuncio_id}")
                return {"existe": False}
            
            # Verifica se a mensagem já existe
            mensagem_existe = conn.execute("""
                SELECT COUNT(*) FROM mensagens 
                WHERE conversa_id = ? 
                AND mensagem = ?
                AND tipo = 'recebida'
            """, (conversa[0], mensagem)).fetchone()[0] > 0
            
            logger.info(f"Verificação de mensagem para anuncio_id {anuncio_id}: {'existe' if mensagem_existe else 'não existe'}")
            return {"existe": mensagem_existe}
    except Exception as e:
        logger.error(f"Erro ao verificar mensagem na DB: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao verificar mensagem")

if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando servidor FastAPI")
    uvicorn.run(app, host="localhost", port=8000)
