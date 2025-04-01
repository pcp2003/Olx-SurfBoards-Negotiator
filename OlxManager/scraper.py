import logging
from datetime import datetime
from typing import Optional
import uuid
import requests
import time
import os

from .browser import BrowserManager
from .cache import CacheManager
from .api import APIManager
from .langflow import LangflowManager
from .metrics import MetricsManager
from config import CREDENTIALS, URLS, LOGGING

# Configuração do logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOGGING["level"]),
    format=LOGGING["format"],
    handlers=[
        logging.FileHandler(os.path.join('logs', LOGGING["file"]), encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class OlxScraper:
    def __init__(self):
        logger.info("Inicializando OlxScraper...")
        self.api = APIManager(URLS["api"])
        self.browser = BrowserManager(self.api)
        self.cache = CacheManager()
        self.langflow = LangflowManager()
        self.metrics = MetricsManager()
        logger.info("Métricas inicializadas")

    def executar(self):
        """Executa o scraper completo"""
        try:
            logger.info("Iniciando execução do scraper...")
            
            if not self.browser.iniciar_navegador():
                logger.error("Falha ao iniciar o navegador")
                return False

            logger.info("Acessando página de favoritos...")
            self.browser.driver.get(URLS["favorites"])

            if not self.browser.aceitar_cookies():
                logger.error("Falha ao aceitar cookies")
                return False
                
            if not self.browser.login():
                logger.error("Falha no login")
                return False

            # Coleta links e abre abas
            logger.info("Coletando links dos anúncios...")
            links = self.browser.append_links()
            if not links:
                logger.warning("Nenhum link encontrado para processar")
                return True

            logger.info(f"Abrindo {len(links)} anúncios em abas...")
            self.browser.abrir_anuncios_em_abas(links)
            
            # Inicia ciclo de respostas
            logger.info("Iniciando ciclo de respostas...")
            self.ciclo_de_respostas()

            return True
        except Exception as e:
            logger.error(f"Erro durante a execução: {e}")
            self.metrics.atualizar('erros')
            return False
        finally:
            logger.info("Finalizando execução...")
            self.browser.finalizar()
            # Log final das métricas
            self.metrics.log()

    def ciclo_de_respostas(self):
        """Loop para buscar mensagens pendentes e gerar respostas automáticas"""
        self.metrics.atualizar('inicio_execucao', datetime.now())
        
        while True:
            try:
                # Verificar novas mensagens
                logger.info("Verificando novas mensagens...")
                self.browser.extrair_mensagens_vendedor()

                logger.info("Verificando conversas pendentes...")
                conversas_pendentes = self.api.buscar_respostas_pendentes()

                if conversas_pendentes:
                    for conversa in conversas_pendentes:
                        for msg in conversa['mensagens']:
                            if msg['tipo'] == 'recebida' and not msg['respondida']:
                                logger.info(f"Gerando resposta para: {msg['mensagem']}")
                                
                                resposta = self.langflow.obter_resposta(msg['mensagem'], conversa['anuncio_id'])
                                
                                if resposta:
                                    logger.info(f"Resposta enviada: {resposta}")
                                else:
                                    logger.warning(f"Falha ao gerar resposta")
                                    self.metrics.atualizar('erros')
                
                # Atualizar métricas
                self.metrics.atualizar('ultima_verificacao', datetime.now())
                self.metrics.atualizar('tempo_total_execucao', 
                    (self.metrics.metricas['ultima_verificacao'] - self.metrics.metricas['inicio_execucao']).total_seconds())
                
                # Log das métricas a cada ciclo
                self.metrics.log()
                
                # Aguardar próximo ciclo
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Erro no ciclo de respostas: {e}")
                self.metrics.atualizar('erros')
                time.sleep(60)  # Espera mais tempo em caso de erro

def main():
    try:
        logger.info("Iniciando aplicação...")
        scraper = OlxScraper()
        if not scraper.executar():
            logger.error("Falha na execução do scraper")
    except KeyboardInterrupt:
        logger.info("Scraper interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
    finally:
        logger.info("Encerrando aplicação...")

if __name__ == "__main__":
    main() 