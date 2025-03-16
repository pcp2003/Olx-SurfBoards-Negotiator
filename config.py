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
    "base_url": "https://www.olx.pt"
}

# Configurações de logging
LOGGING = {
    "level": "INFO",
    "format": "%(asctime)s - %(levelname)s - %(message)s",
    "file": "olx_scraper.log"
} 