import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import logging
import json
from datetime import datetime
from config import BROWSER_OPTIONS, TIMEOUTS, CREDENTIALS, URLS, LOGGING
import os

# Configuração do logging
logging.basicConfig(
    level=getattr(logging, LOGGING["level"]),
    format=LOGGING["format"],
    handlers=[
        logging.FileHandler(LOGGING["file"]),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OlxScraper:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.links_cache = set()
        self.load_cache()

    def load_cache(self):
        """Carrega o cache de links já processados"""
        try:
            if os.path.exists('links_cache.json'):
                with open('links_cache.json', 'r') as f:
                    self.links_cache = set(json.load(f))
                logger.info(f"Cache carregado com {len(self.links_cache)} links")
        except Exception as e:
            logger.error(f"Erro ao carregar cache: {e}")

    def save_cache(self):
        """Salva o cache de links processados"""
        try:
            with open('links_cache.json', 'w') as f:
                json.dump(list(self.links_cache), f)
            logger.info("Cache salvo com sucesso")
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")

    def iniciar_navegador(self):
        """Inicia o navegador com as configurações especificadas"""
        try:
            options = webdriver.ChromeOptions()
            if BROWSER_OPTIONS["disable_popup_blocking"]:
                options.add_argument("--disable-popup-blocking")
            if BROWSER_OPTIONS["headless"]:
                options.add_argument("--headless")
            
            self.driver = uc.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, TIMEOUTS["element_wait"])
            logger.info("Navegador iniciado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao iniciar o navegador: {e}")
            return False

    def aceitar_cookies(self):
        """Aceita os cookies do site"""
        for attempt in range(TIMEOUTS["max_retries"]):
            try:
                cookie_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))
                )
                cookie_button.click()
                logger.info("Cookies aceitos com sucesso")
                return True
            except TimeoutException:
                logger.warning(f"Tentativa {attempt + 1} de aceitar cookies falhou")
                time.sleep(TIMEOUTS["retry_delay"])
            except Exception as e:
                logger.error(f"Erro ao aceitar cookies: {e}")
                return False
        return False

    def login(self):
        """Realiza o login no site"""
        for attempt in range(TIMEOUTS["max_retries"]):
            try:
                login_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="mainContent"]/div/div[2]/section/div/div/button'))
                )
                login_button.click()

                username_field = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="username"]'))
                )
                password_field = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="password"]'))
                )

                username_field.send_keys(CREDENTIALS["username"])
                time.sleep(1)
                password_field.send_keys(CREDENTIALS["password"])
                password_field.send_keys(Keys.RETURN)
                
                logger.info("Login realizado com sucesso")
                return True
            except TimeoutException:
                logger.warning(f"Tentativa {attempt + 1} de login falhou")
                time.sleep(TIMEOUTS["retry_delay"])
            except Exception as e:
                logger.error(f"Erro no login: {e}")
                return False
        return False

    def acessar_favoritos(self):
        """Acessa a página de favoritos e coleta os links"""
        try:
            self.wait.until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="mainContent"]/div/div[2]/section/div[2]/div'))
            )
            favoritos = self.wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "css-qo0cxu"))
            )

            novos_links = set()
            for favorito in favoritos:
                try:
                    link = favorito.get_attribute("href")
                    if link and link not in self.links_cache:
                        link_modificado = link.replace("?", "?chat=1&isPreviewActive=0&")
                        novos_links.add(link_modificado)
                        self.links_cache.add(link)
                except Exception as e:
                    logger.error(f"Erro ao processar um favorito: {e}")

            logger.info(f"{len(novos_links)} novos links encontrados")
            return list(novos_links)
        except Exception as e:
            logger.error(f"Erro ao acessar favoritos: {e}")
            return []

    def abrir_anuncios_em_abas(self, links):
        """Abre os anúncios em novas abas"""
        for link in links:
            try:
                logger.info(f"Abrindo: {link}")
                self.driver.execute_script(f"window.open('{link}', '_blank');")
                time.sleep(TIMEOUTS["retry_delay"])
            except Exception as e:
                logger.error(f"Erro ao abrir o link: {e}")

    def finalizar(self):
        """Finaliza a execução e limpa recursos"""
        if self.driver:
            try:
                self.save_cache()
                self.driver.quit()
                logger.info("Navegador fechado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao fechar o navegador: {e}")

    def executar(self):
        """Executa o processo completo"""
        if not self.iniciar_navegador():
            return False

        try:
            self.driver.get(URLS["favorites"])
            
            if not self.aceitar_cookies():
                return False
                
            if not self.login():
                return False

            links = self.acessar_favoritos()
            if links:
                self.abrir_anuncios_em_abas(links)
            
            return True
        except Exception as e:
            logger.error(f"Erro durante a execução: {e}")
            return False
        finally:
            self.finalizar()

def main():
    scraper = OlxScraper()
    if not scraper.executar():
        logger.error("Falha na execução do scraper")

if __name__ == "__main__":
    main()
