from fastapi import FastAPI
from .routes import router
from .database import criar_tabelas
import uvicorn
import logging

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

# Cria a aplicação FastAPI
app = FastAPI()

# Inclui as rotas
app.include_router(router)

def iniciar_servidor():
    """Inicia o servidor FastAPI e cria as tabelas"""
    # Cria as tabelas ao iniciar
    criar_tabelas()
    logger.info("Iniciando servidor FastAPI")
    uvicorn.run(app, host="localhost", port=8000) 