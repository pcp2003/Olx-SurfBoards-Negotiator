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
import requests


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
        self.api_url = URLS["api"]  # URL da API FastAPI do arquivo de configuração

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

    def append_links(self):
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
                    link = favorito.get_attribute("href").replace("?", "?chat=1&isPreviewActive=0&")
                    if link and link not in self.links_cache:
                        novos_links.add(link)
                        self.links_cache.add(link)
                except Exception as e:
                    logger.error(f"Erro ao processar um favorito: {e}")

            logger.info(f"{len(novos_links)} novos links encontrados")
            return self.links_cache
        
        except Exception as e:
            logger.error(f"Erro ao acessar favoritos: {e}")
            return []

    def abrir_anuncios_em_abas(self, links):
        """Abre os anúncios em novas abas e espera o carregamento"""
        # Guarda a aba principal
        aba_principal = self.driver.current_window_handle
        
        for link in links:
            try:
                logger.info(f"Abrindo: {link}")
                
                # Abre nova aba
                self.driver.execute_script(f"window.open('{link}', '_blank');")
                time.sleep(2)  # Espera a aba abrir
                
                # Muda para a nova aba
                self.driver.switch_to.window(self.driver.window_handles[-1])
                
                # Espera a página carregar
                self.wait.until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Volta para a aba principal
                self.driver.switch_to.window(aba_principal)
                
            except Exception as e:
                logger.error(f"Erro ao abrir o link: {e}")
                try:
                    self.driver.switch_to.window(aba_principal)
                except:
                    pass

    def finalizar(self):
        """Finaliza a execução e limpa recursos"""
        if self.driver:
            try:
                self.save_cache()
                self.driver.quit()
                logger.info("Navegador fechado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao fechar o navegador: {e}")


    # Novas alterações

    

    def verificar_mensagem_existe(self, anuncio_id, mensagem, tipo):
        """ Verifica se uma mensagem já existe na DB antes de enviá-la para a API """
        try:
            response = requests.get(
                f"{self.api_url}/mensagem-existe",
                params={
                    "email": CREDENTIALS["username"],
                    "anuncio_id": anuncio_id,
                    "mensagem": mensagem,
                    "tipo": tipo
                }
            )
            if response.status_code == 200:
                return response.json().get("existe", False)
            logger.error(f"Erro ao verificar mensagem na API: {response.text}")
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar mensagem na API: {e}")
            return False

    def enviar_mensagem_para_api(self, anuncio_id, mensagem, tipo):
        """ Envia uma mensagem extraída pelo scraper para a API FastAPI """
        try:
            payload = {
                "mensagem": mensagem
            }
            response = requests.post(
                f"{self.api_url}/receber-mensagem",
                json=payload,
                params={
                    "email": CREDENTIALS["username"],
                    "anuncio_id": anuncio_id,
                    "tipo": tipo
                }
            )
            if response.status_code == 200:
                logger.info(f"Mensagem {tipo} registrada na API: {mensagem}")
            else:
                logger.error(f"Erro ao registrar mensagem na API: {response.text}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erro ao registrar mensagem na API: {e}")
            return False

    def buscar_respostas_pendentes(self):
        """ Busca conversas com mensagens recebidas não respondidas na API """
        try:
            response = requests.get(
                f"{self.api_url}/conversas/pendentes",
                params={"email": CREDENTIALS["username"]}
            )
            if response.status_code == 200:
                return response.json().get("conversas_pendentes", [])
            logger.error(f"Erro ao buscar conversas pendentes: {response.text}")
            return []
        except Exception as e:
            logger.error(f"Erro ao buscar conversas pendentes: {e}")
            return []

    def enviar_mensagem_olx(self, anuncio_id, mensagem):
        """ Envia a mensagem de resposta no OLX """
        try:
            # Encontrar a aba correta do anúncio
            abas = self.driver.window_handles
            for aba in abas[1:]:  # Pula a primeira aba (favoritos)
                self.driver.switch_to.window(aba)
                if anuncio_id in self.driver.current_url:
                    break
            else:
                logger.error(f"Anúncio {anuncio_id} não encontrado nas abas abertas")
                return False

            # Encontrar e preencher campo de mensagem
            campo_mensagem = self.wait.until(
                EC.presence_of_element_located((By.NAME, "message.text"))  # Usando NAME correto
            )

            # Enviar a mensagem
            campo_mensagem.clear()
            campo_mensagem.send_keys(mensagem)
            campo_mensagem.send_keys(Keys.RETURN)
            
            logger.info(f" Mensagem enviada no OLX: {mensagem}")
            return True

        except Exception as e:
            logger.error(f"Erro ao enviar mensagem no OLX: {e}")
            return False


    def extrair_mensagens_vendedor(self):
        """ Extrai mensagens de vendedores e envia para a API """
        try:
            abas = self.driver.window_handles
            for aba in abas[1:]:  # Pula a primeira aba (favoritos)
                try:
                    self.driver.switch_to.window(aba)
                    time.sleep(2)  # Pequena pausa para garantir carregamento
                    
                    anuncio_id = self.driver.current_url.split("/")[-1].split("?")[0]
                    logger.info(f"Analisando Anúncio ID: {anuncio_id}")

                    # Esperar até que o elemento das mensagens esteja presente
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="messages-list-container"]')))

                    # Buscar todas as mensagens (recebidas e enviadas)
                    mensagens_recebidas = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="received-message"] [data-testid="message"] span')
                    mensagens_enviadas = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="sent-message"] [data-testid="message"] span')
                    
                    if not mensagens_recebidas and not mensagens_enviadas:
                        logger.info(f"Nenhuma mensagem encontrada para o anúncio {anuncio_id}")
                        continue

                    # Criar lista de todas as mensagens com seus tipos
                    todas_mensagens = []
                    
                    # Adicionar mensagens recebidas
                    for msg in mensagens_recebidas:
                        try:
                            texto = msg.text.strip()
                            if texto:
                                todas_mensagens.append({
                                    'texto': texto,
                                    'tipo': 'recebida',
                                    'elemento': msg
                                })
                        except Exception as e:
                            logger.error(f"Erro ao processar mensagem recebida: {e}")

                    # Adicionar mensagens enviadas
                    for msg in mensagens_enviadas:
                        try:
                            texto = msg.text.strip()
                            if texto:
                                todas_mensagens.append({
                                    'texto': texto,
                                    'tipo': 'enviada',
                                    'elemento': msg
                                })
                        except Exception as e:
                            logger.error(f"Erro ao processar mensagem enviada: {e}")

                    # Ordenar mensagens por posição no DOM (ordem de recebimento)
                    todas_mensagens.sort(key=lambda x: self.driver.execute_script(
                        "return arguments[0].getBoundingClientRect().top;", 
                        x['elemento']
                    ))

                    # Enviar todas as mensagens para a API
                    for msg in todas_mensagens:
                        try:
                            texto = msg['texto']
                            tipo = msg['tipo']
                            
                            # Verificar se a mensagem já existe antes de enviar
                            if not self.verificar_mensagem_existe(anuncio_id, texto, tipo):
                                self.enviar_mensagem_para_api(anuncio_id, texto, tipo)
                            else:
                                logger.info(f"Mensagem já registrada na API: {texto}")
                        except Exception as e:
                            logger.error(f"Erro ao processar mensagem: {e}")

                except Exception as e:
                    logger.error(f"Erro ao processar aba: {e}")
                    continue
                    
            try:
                self.driver.switch_to.window(abas[0])
            except:
                pass
            
        except Exception as e:
            logger.error(f"Erro ao buscar mensagens novas: {e}")


    def ciclo_de_respostas(self):
        """ Loop infinito para buscar mensagens e mostrar as pendentes """
        while True:
            logger.info("🔄 Verificando conversas pendentes...")
            conversas_pendentes = self.buscar_respostas_pendentes()

            if conversas_pendentes:
                print("\n" + "="*50)
                print("📬 CONVERSAS PENDENTES:")
                print("="*50)
                
                for conversa in conversas_pendentes:
                    print(f"\n📝 Anúncio ID: {conversa['anuncio_id']}")
                    for msg in conversa['mensagens']:
                        if msg['tipo'] == 'recebida' and not msg['respondida']:
                            print(f"💬 Mensagem: {msg['mensagem']}")
                    print("-"*30)
                
                print("\n" + "="*50)
                print("🤖 ÁREA PREPARADA PARA INTEGRAÇÃO COM LANGFLOW")
                print("="*50 + "\n")
                
                # TODO: Aqui será integrado o Langflow para gerar respostas
                # Exemplo de como será:
                # for conversa in conversas_pendentes:
                #     for msg in conversa['mensagens']:
                #         if msg['tipo'] == 'recebida' and not msg['respondida']:
                #             resposta = langflow.gerar_resposta(msg['mensagem'])
                #             self.enviar_mensagem_olx(conversa['anuncio_id'], resposta)
            else:
                logger.info("⏳ Nenhuma conversa pendente.")

            # Verifica novas mensagens dos vendedores a cada 5 minutos
            logger.info("🔄 Verificando novas mensagens dos vendedores...")
            self.extrair_mensagens_vendedor()
            
            # Aguarda 5 minutos antes da próxima verificação
            logger.info("⏳ Aguardando 5 minutos para próxima verificação...")
            time.sleep(300)  # 5 minutos = 300 segundos


    def executar(self):
        """ Executa o scraper completo """
        if not self.iniciar_navegador():
            return False

        try:
            self.driver.get(URLS["favorites"])

            if not self.aceitar_cookies():
                return False
                
            if not self.login():
                return False

            # Coleta links e abre abas
            links = self.append_links()
            if not links:
                logger.warning("Nenhum link encontrado para processar")
                return True

            self.abrir_anuncios_em_abas(links)
            
            # Processa mensagens
            self.extrair_mensagens_vendedor()
            
            # Inicia ciclo de respostas
            self.ciclo_de_respostas()

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
