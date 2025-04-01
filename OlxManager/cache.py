import json
import os
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self.links_cache = set()
        self.load_cache()

    def load_cache(self):
        """Carrega o cache de links já processados"""
        try:
            if os.path.exists('links_cache.json'):
                logger.info("Carregando cache de links...")
                with open('links_cache.json', 'r') as f:
                    self.links_cache = set(json.load(f))
                logger.info(f"Cache carregado com {len(self.links_cache)} links")
            else:
                logger.info("Nenhum cache de links encontrado")
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar cache de links: {e}")
            self.links_cache = set()
        except Exception as e:
            logger.error(f"Erro ao carregar cache: {e}")
            self.links_cache = set()

    def save_cache(self):
        """Salva o cache de links processados"""
        try:
            logger.info("Salvando cache de links...")
            with open('links_cache.json', 'w') as f:
                json.dump(list(self.links_cache), f)
            logger.info(f"Cache salvo com sucesso ({len(self.links_cache)} links)")
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")

    def add_link(self, link: str):
        """Adiciona um link ao cache"""
        self.links_cache.add(link)
        self.save_cache()

    def has_link(self, link: str) -> bool:
        """Verifica se um link existe no cache"""
        return link in self.links_cache 