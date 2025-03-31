import logging
import os
from config.settings import LOG_LEVEL, LOG_FILE

# Cria o diretório de logs se não existir
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Configura o logger
logger = logging.getLogger("olx_scraper")
logger.setLevel(LOG_LEVEL)

# Cria o handler para arquivo
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setLevel(LOG_LEVEL)

# Cria o handler para console
console_handler = logging.StreamHandler()
console_handler.setLevel(LOG_LEVEL)

# Cria o formato do log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Adiciona os handlers ao logger
logger.addHandler(file_handler)
logger.addHandler(console_handler) 