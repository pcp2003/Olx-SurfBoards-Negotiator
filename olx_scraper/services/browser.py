from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
from config.settings import BROWSER_OPTIONS, TIMEOUTS, CREDENTIALS
from utils.logger import logger
import time

class BrowserManager:
    def __init__(self):
        self.driver = None
        self.wait = None

    def iniciar(self):
        """Inicia o navegador com as configurações especificadas"""
        try:
            logger.info("Configurando opções do navegador...")
            options = webdriver.ChromeOptions()
            if BROWSER_OPTIONS["disable_popup_blocking"]:
                options.add_argument("--disable-popup-blocking")
            if BROWSER_OPTIONS["headless"]:
                options.add_argument("--headless")
            
            logger.info("Iniciando navegador Chrome...")
            self.driver = uc.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, TIMEOUTS["element_wait"])
            logger.info("Navegador iniciado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao iniciar o navegador: {e}")
            return False

    def aceitar_cookies(self):
        """Aceita os cookies do site"""
        logger.info("Tentando aceitar cookies...")
        for attempt in range(TIMEOUTS["max_retries"]):
            try:
                logger.info(f"Tentativa {attempt + 1} de aceitar cookies...")
                # Tenta diferentes seletores para o botão de cookies
                cookie_selectors = [
                    (By.ID, "onetrust-accept-btn-handler"),
                    (By.CSS_SELECTOR, "[data-testid='cookie-banner-accept']"),
                    (By.XPATH, "//button[contains(text(), 'Aceitar')]"),
                    (By.XPATH, "//button[contains(text(), 'Aceitar todos')]")
                ]
                
                for selector in cookie_selectors:
                    try:
                        cookie_button = self.wait.until(
                            EC.element_to_be_clickable(selector)
                        )
                        cookie_button.click()
                        logger.info("Cookies aceitos com sucesso")
                        return True
                    except:
                        continue
                
                logger.warning(f"Tentativa {attempt + 1} de aceitar cookies falhou: Nenhum botão encontrado")
                if attempt < TIMEOUTS["max_retries"] - 1:
                    time.sleep(TIMEOUTS["retry_delay"])
            except Exception as e:
                logger.warning(f"Tentativa {attempt + 1} de aceitar cookies falhou: {e}")
                if attempt < TIMEOUTS["max_retries"] - 1:
                    time.sleep(TIMEOUTS["retry_delay"])
        logger.error("Todas as tentativas de aceitar cookies falharam")
        return False

    def login(self):
        """Realiza o login no site"""
        logger.info("Iniciando processo de login...")
        for attempt in range(TIMEOUTS["max_retries"]):
            try:
                logger.info(f"Tentativa {attempt + 1} de login...")
                
                # Clicar no botão de login
                logger.info("Procurando botão de login...")
                login_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="mainContent"]/div/div[2]/section/div/div/button'))
                )
                login_button.click()

                # Preencher campos de login
                logger.info("Preenchendo campos de login...")
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
            except Exception as e:
                logger.warning(f"Tentativa {attempt + 1} de login falhou: {e}")
                if attempt < TIMEOUTS["max_retries"] - 1:
                    time.sleep(TIMEOUTS["retry_delay"])
        logger.error("Todas as tentativas de login falharam")
        return False

    def finalizar(self):
        """Finaliza a execução e limpa recursos"""
        if self.driver:
            try:
                logger.info("Fechando navegador...")
                self.driver.quit()
                logger.info("Navegador fechado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao fechar o navegador: {e}") 