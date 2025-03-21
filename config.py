import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Configurações do navegador
BROWSER_OPTIONS = {
    "disable_popup_blocking": True,
    "headless": False  # Mude para True para executar sem interface gráfica
}

# Configurações de tempo
TIMEOUTS = {
    "page_load": 30,
    "element_wait": 10,
    "retry_delay": 2,
    "max_retries": 3
}

# Configurações de login
CREDENTIALS = {
    "username": os.getenv("OLX_USERNAME", ""),
    "password": os.getenv("OLX_PASSWORD", "")
}

# URLs
URLS = {
    "favorites": "https://www.olx.pt/favoritos/",
    "base_url": "https://www.olx.pt",
    "api": "http://localhost:8000",  # URL da API FastAPI
    "Langflow_URL" : "http://127.0.0.1:7860/api/v1/run/a0075945-5b70-43d4-9a82-ab84ddc6be27"
}

# Configurações de logging
LOGGING = {
    "level": "INFO",
    "format": "%(asctime)s - %(levelname)s - %(message)s",
    "file": "olx_scraper.log"
} 