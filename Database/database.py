import sqlite3
import os
import logging
from datetime import datetime

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("DataBase/api.log"),
        logging.StreamHandler()
    ],
)
logger = logging.getLogger(__name__)

# Função para conectar ao banco de dados
def get_db():
    try:
        conn = sqlite3.connect("DataBase/mensagens.db")
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
            if not os.path.exists("DataBase/mensagens.db"):
                logger.info("Banco de dados não encontrado, criando novo...")
            
            # Cria tabela de conversas
            logger.info("Criando/verificando tabela de conversas...")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    anuncio_id TEXT NOT NULL,
                    nome_vendedor TEXT,
                    titulo_anuncio TEXT,
                    preco_anuncio TEXT,
                    searched_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(email, anuncio_id)
                )
            """)
            
            # Cria índices para conversas
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conversas_email ON conversas(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conversas_anuncio ON conversas(anuncio_id)")
            
            # Cria tabela de mensagens
            logger.info("Criando/verificando tabela de mensagens...")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mensagens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversa_id INTEGER NOT NULL,
                    tipo TEXT CHECK(tipo IN ('enviada', 'recebida')) NOT NULL,
                    mensagem TEXT NOT NULL,
                    respondida BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversa_id) REFERENCES conversas (id)
                )
            """)
            
            # Cria índices para mensagens
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mensagens_conversa ON mensagens(conversa_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mensagens_tipo ON mensagens(tipo)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mensagens_respondida ON mensagens(respondida)")
            
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