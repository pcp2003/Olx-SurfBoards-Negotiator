from services.browser import BrowserManager
from services.api import APIService
from services.olx import OLXService
from utils.logger import logger
from config.settings import API_URL
import time

def main():
    try:
        # Inicializa os serviços
        logger.info("Inicializando serviços...")
        browser_manager = BrowserManager()
        api_service = APIService(API_URL)
        olx_service = OLXService(browser_manager, api_service)
        
        # Inicia o navegador
        logger.info("Iniciando navegador...")
        browser_manager.iniciar()
        
        # Acessa a página de favoritos primeiro
        logger.info("Acessando página de favoritos...")
        browser_manager.driver.get("https://www.olx.pt/favoritos/")
        time.sleep(5)
        
        # Aceita os cookies
        logger.info("Aceitando cookies...")
        browser_manager.aceitar_cookies()
        
        # Faz login no OLX
        logger.info("Fazendo login no OLX...")
        browser_manager.login()
        
        while True:
            try:
                # Coleta links dos anúncios
                logger.info("Coletando links dos anúncios...")
                links = olx_service.append_links()
                
                if not links:
                    logger.info("Nenhum link encontrado. Aguardando próximo ciclo...")
                    time.sleep(300)  # Aguarda 5 minutos
                    continue
                
                # Abre os anúncios em novas abas
                logger.info(f"Abrindo {len(links)} anúncios em novas abas...")
                olx_service.abrir_anuncios_em_abas(links)
                
                # Extrai mensagens dos vendedores
                logger.info("Extraindo mensagens dos vendedores...")
                olx_service.extrair_mensagens_vendedor()
                
                # Salva o cache de links
                logger.info("Salvando cache de links...")
                olx_service.save_cache()
                
                # Fecha todas as abas exceto a primeira
                logger.info("Fechando abas...")
                abas = browser_manager.driver.window_handles
                for aba in abas[1:]:
                    browser_manager.driver.switch_to.window(aba)
                    browser_manager.driver.close()
                browser_manager.driver.switch_to.window(abas[0])
                
                # Aguarda antes do próximo ciclo
                logger.info("Aguardando próximo ciclo...")
                time.sleep(300)  # Aguarda 5 minutos
                
            except Exception as e:
                logger.error(f"Erro durante o ciclo principal: {e}")
                time.sleep(300)  # Aguarda 5 minutos mesmo em caso de erro
                continue
                
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
    finally:
        # Finaliza o navegador
        logger.info("Finalizando navegador...")
        browser_manager.finalizar()

if __name__ == "__main__":
    main() 