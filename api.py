from fastapi import FastAPI
import sqlite3
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Criar instância da API
app = FastAPI()

# 🔹 Modelo Pydantic para receber dados de mensagens
class MensagemInput(BaseModel):
    anuncio_id: str
    vendedor: str
    mensagem: str

def criar_tabela():
    """Cria a tabela de mensagens se ela não existir"""
    conn = sqlite3.connect("mensagens.db")
    cursor = conn.cursor()
    
    # Criar tabela com email como parte da chave primária
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            anuncio_id TEXT NOT NULL,
            vendedor TEXT NOT NULL,
            mensagem_enviada TEXT,
            mensagem_recebida TEXT,
            UNIQUE(email, anuncio_id)
        )
    """)
    
    conn.commit()
    conn.close()

# Criar tabela ao iniciar a aplicação
criar_tabela()

# 🔹 Endpoint 1: Buscar mensagens não respondidas
@app.get("/mensagens/pendentes")
def buscar_mensagens_pendentes():
    email = os.getenv("OLX_USERNAME")
    conn = sqlite3.connect("mensagens.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mensagens WHERE email = ? AND mensagem_recebida IS NULL", (email,))
    mensagens = cursor.fetchall()
    conn.close()
    
    # Converter resultados em JSON
    mensagens_json = [
        {
            "id": msg[0],
            "email": msg[1],
            "anuncio_id": msg[2],
            "vendedor": msg[3],
            "mensagem_enviada": msg[4]
        }
        for msg in mensagens
    ]
    return {"mensagens_pendentes": mensagens_json}

# 🔹 Endpoint 2: Registrar mensagem enviada ao vendedor
@app.post("/enviar-mensagem/")
def enviar_mensagem(mensagem: MensagemInput):
    email = os.getenv("OLX_USERNAME")
    conn = sqlite3.connect("mensagens.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO mensagens (email, anuncio_id, vendedor, mensagem_enviada)
            VALUES (?, ?, ?, ?)
        """, (email, mensagem.anuncio_id, mensagem.vendedor, mensagem.mensagem))
        conn.commit()
        return {"status": "Mensagem enviada registrada com sucesso!"}
    except sqlite3.IntegrityError:
        return {"status": "Mensagem já existe para este anúncio!"}
    finally:
        conn.close()

# 🔹 Endpoint 3: Atualizar mensagem recebida do vendedor
@app.put("/atualizar-mensagem/{anuncio_id}")
def atualizar_mensagem(anuncio_id: str, mensagem_recebida: str):
    email = os.getenv("OLX_USERNAME")
    conn = sqlite3.connect("mensagens.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE mensagens 
        SET mensagem_recebida = ? 
        WHERE email = ? AND anuncio_id = ?
    """, (mensagem_recebida, email, anuncio_id))
    conn.commit()
    conn.close()
    return {"status": "Mensagem recebida atualizada!"}

# 🔹 Endpoint 4: Remover mensagem
@app.delete("/mensagem/{anuncio_id}")
def remover_mensagem(anuncio_id: str):
    email = os.getenv("OLX_USERNAME")
    conn = sqlite3.connect("mensagens.db")
    cursor = conn.cursor()
    
    # Verifica se a mensagem existe antes de tentar remover
    cursor.execute("SELECT id FROM mensagens WHERE email = ? AND anuncio_id = ?", (email, anuncio_id))
    mensagem = cursor.fetchone()
    
    if not mensagem:
        conn.close()
        return {"status": "Mensagem não encontrada!"}
    
    # Remove a mensagem
    cursor.execute("DELETE FROM mensagens WHERE email = ? AND anuncio_id = ?", (email, anuncio_id))
    conn.commit()
    conn.close()
    
    return {"status": "Mensagem removida com sucesso!"}

# 🔹 Executar a API
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
