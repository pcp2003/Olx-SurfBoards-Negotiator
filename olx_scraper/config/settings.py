import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações do OLX
OLX_EMAIL = os.getenv("OLX_EMAIL", "")
OLX_PASSWORD = os.getenv("OLX_PASSWORD", "")
OLX_URL = "https://www.olx.pt"

# Configurações da API
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_TIMEOUT = 30  # segundos

# Configurações do navegador
HEADLESS = os.getenv("HEADLESS", "True").lower() == "true"
BROWSER_WAIT_TIME = 10  # segundos

# Configurações de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.path.join("data", "logs", "olx_scraper.log")

# Configurações de cache
CACHE_FILE = os.path.join("data", "cache", "links_cache.json")

# Configurações de tempo
CYCLE_WAIT_TIME = 300  # segundos (5 minutos)
PAGE_LOAD_WAIT_TIME = 5  # segundos

BROWSER_OPTIONS = {
    "disable_popup_blocking": True,
    "headless": False
}

TIMEOUTS = {
    "element_wait": 10,
    "max_retries": 3,
    "retry_delay": 2
}

CREDENTIALS = {
    "username": "joseAlmeida90811@gmail.com",
    "password": "JoseAlmeida90811"
}

URLS = {
    "favorites": "https://www.olx.pt/favoritos/",
    "api": "http://localhost:8000",
    "Langflow_URL": "http://localhost:7860/predict/"
}

LOGGING = {
    "level": "INFO",
    "format": "%(asctime)s - %(levelname)s - %(message)s",
    "file": os.path.join("data", "logs", "olx_scraper.log")
} 