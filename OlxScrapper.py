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
from typing import Dict, Any, Optional
import uuid


# Configuração do logging
logging.basicConfig(
    level=getattr(logging, LOGGING["level"]),
    format=LOGGING["format"],
    handlers=[
        logging.FileHandler(LOGGING["file"], encoding='utf-8'),
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
        # Adicionando métricas
        self.metricas = {
            'mensagens_processadas': 0,
            'respostas_enviadas': 0,
            'erros': 0,
            'inicio_execucao': None,
            'ultima_verificacao': None,
            'tempo_total_execucao': 0
        }

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
            # Aguarda a página carregar completamente
            logger.info("Aguardando carregamento da página de favoritos...")
            time.sleep(5)  # Pequena pausa para garantir carregamento
            
            # Tenta diferentes seletores para encontrar os favoritos
            seletores = [
                (By.CLASS_NAME, "css-qo0cxu"),
                (By.CSS_SELECTOR, "a[href*='/favoritos/']"),
                (By.CSS_SELECTOR, "[data-testid='favorites-item']")
            ]
            
            favoritos = None
            for seletor in seletores:
                try:
                    logger.info(f"Tentando encontrar favoritos com seletor: {seletor}")
                    favoritos = self.wait.until(
                        EC.presence_of_all_elements_located(seletor)
                    )
                    if favoritos:
                        logger.info(f"Favoritos encontrados com seletor: {seletor}")
                        break
                except Exception as e:
                    logger.debug(f"Seletor {seletor} não funcionou: {str(e)}")
                    continue
            
            if not favoritos:
                logger.error("Nenhum favorito encontrado")
                return []
            
            novos_links = set()
            for favorito in favoritos:
                try:
                    link = favorito.get_attribute("href")
                    if not link:
                        continue
                        
                    # Adiciona parâmetros necessários ao link
                    link = link.replace("?", "?chat=1&isPreviewActive=0&")
                    
                    if link and link not in self.links_cache:
                        novos_links.add(link)
                        self.links_cache.add(link)
                        logger.debug(f"Novo link encontrado: {link}")
                except Exception as e:
                    logger.error(f"Erro ao processar um favorito: {str(e)}")
                    continue

            logger.info(f"{len(novos_links)} novos links encontrados")
            return self.links_cache
        
        except Exception as e:
            logger.error(f"Erro ao acessar favoritos: {str(e)}")
            # Tenta salvar o HTML da página para debug
            try:
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                logger.info("HTML da página salvo em debug_page.html")
            except:
                pass
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

    

    def atualizar_metricas(self, tipo: str, valor: Any = 1) -> None:
        """Atualiza as métricas do scraper"""
        if tipo in self.metricas:
            if isinstance(self.metricas[tipo], (int, float)):
                self.metricas[tipo] += valor
            else:
                self.metricas[tipo] = valor

    def log_metricas(self) -> None:
        """Registra as métricas atuais"""
        logger.info("Métricas do Scraper:")
        for key, value in self.metricas.items():
            logger.info(f"  {key}: {value}")

    def verificar_mensagem_existe(self, anuncio_id: str, mensagem: str, tipo: str) -> bool:
        """Verifica se uma mensagem já existe na DB antes de enviá-la para a API"""
        max_tentativas = 3
        for tentativa in range(max_tentativas):
            try:
                response = requests.get(
                    f"{self.api_url}/mensagem-existe",
                    params={
                        "email": CREDENTIALS["username"],
                        "anuncio_id": anuncio_id,
                        "mensagem": mensagem,
                        "tipo": tipo
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    return response.json().get("existe", False)
                logger.error(f"Erro ao verificar mensagem na API: {response.text}")
                if tentativa < max_tentativas - 1:
                    time.sleep(2)
            except Exception as e:
                logger.error(f"Tentativa {tentativa + 1} falhou: {e}")
                if tentativa < max_tentativas - 1:
                    time.sleep(2)
        return False

    def enviar_mensagem_para_api(self, anuncio_id: str, mensagem: str, tipo: str) -> bool:
        """Envia uma mensagem extraída pelo scraper para a API FastAPI"""
        max_tentativas = 3
        for tentativa in range(max_tentativas):
            try:
                payload = {"mensagem": mensagem}
                response = requests.post(
                    f"{self.api_url}/receber-mensagem",
                    json=payload,
                    params={
                        "email": CREDENTIALS["username"],
                        "anuncio_id": anuncio_id,
                        "tipo": tipo
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    logger.info(f"Mensagem {tipo} registrada na API: {mensagem}")
                    self.atualizar_metricas('mensagens_processadas')
                    return True
                logger.error(f"Erro ao registrar mensagem na API: {response.text}")
                if tentativa < max_tentativas - 1:
                    time.sleep(2)
            except Exception as e:
                logger.error(f"Tentativa {tentativa + 1} falhou: {e}")
                if tentativa < max_tentativas - 1:
                    time.sleep(2)
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

    def enviar_mensagem_olx(self, anuncio_id: str, mensagem: str) -> bool:
        """Envia a mensagem de resposta no OLX"""
        max_tentativas = 3
        for tentativa in range(max_tentativas):
            try:
                # Encontrar a aba correta do anúncio
                abas = self.driver.window_handles
                for aba in abas[1:]:  # Pula a primeira aba (favoritos)
                    self.driver.switch_to.window(aba)
                    if anuncio_id in self.driver.current_url:
                        break
                else:
                    logger.error(f"Anúncio {anuncio_id} não encontrado nas abas abertas")
                    if tentativa < max_tentativas - 1:
                        time.sleep(2)
                    continue

                # Encontrar e preencher campo de mensagem
                campo_mensagem = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "message.text"))
                )

                # Limpar campo e enviar mensagem
                campo_mensagem.clear()
                campo_mensagem.send_keys(mensagem)
                campo_mensagem.send_keys(Keys.RETURN)
                
                # Verificar se a mensagem foi enviada
                time.sleep(2)  # Pequena pausa para garantir o envio
                logger.info(f" Mensagem enviada no OLX: {mensagem}")
                return True

            except TimeoutException:
                logger.error(f"Timeout ao tentar enviar mensagem (tentativa {tentativa + 1})")
                if tentativa < max_tentativas - 1:
                    time.sleep(2)
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem no OLX (tentativa {tentativa + 1}): {e}")
                if tentativa < max_tentativas - 1:
                    time.sleep(2)
        
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
        """Loop para buscar mensagens pendentes e gerar respostas automáticas"""
        self.metricas['inicio_execucao'] = datetime.now()
        
        while True:
            try:
                logger.info("Verificando conversas pendentes...")
                conversas_pendentes = self.buscar_respostas_pendentes()

                if conversas_pendentes:
                    for conversa in conversas_pendentes:
                        for msg in conversa['mensagens']:
                            if msg['tipo'] == 'recebida' and not msg['respondida']:
                                logger.info(f"Gerando resposta para: {msg['mensagem']}")
                                
                                resposta = self.obter_resposta_langflow(msg['mensagem'])
                                
                                if resposta:
                                    # if self.enviar_mensagem_olx(conversa['anuncio_id'], resposta):
                                        logger.info(f"Resposta enviada: {resposta}")
                                        self.atualizar_metricas('respostas_enviadas')
                                    # else:
                                        # logger.error(f"Falha ao enviar resposta no OLX")
                                        # self.atualizar_metricas('erros')
                                else:
                                    logger.warning(f"Falha ao gerar resposta")
                                    self.atualizar_metricas('erros')

                # Verificar novas mensagens
                logger.info("Verificando novas mensagens...")
                self.extrair_mensagens_vendedor()
                
                # Atualizar métricas
                self.metricas['ultima_verificacao'] = datetime.now()
                self.metricas['tempo_total_execucao'] = (self.metricas['ultima_verificacao'] - self.metricas['inicio_execucao']).total_seconds()
                
                # Log das métricas a cada ciclo
                self.log_metricas()
                
                # Aguardar próximo ciclo
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Erro no ciclo de respostas: {e}")
                self.atualizar_metricas('erros')
                time.sleep(60)  # Espera mais tempo em caso de erro


    def executar(self):
        """Executa o scraper completo"""
        try:
            if not self.iniciar_navegador():
                logger.error("Falha ao iniciar o navegador")
                return False

            self.driver.get(URLS["favorites"])

            if not self.aceitar_cookies():
                logger.error("Falha ao aceitar cookies")
                return False
                
            if not self.login():
                logger.error("Falha no login")
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
            self.atualizar_metricas('erros')
            return False
        finally:
            self.finalizar()
            # Log final das métricas
            self.log_metricas()


    def obter_resposta_langflow(self, mensagem: str, session_id: Optional[str] = None) -> Optional[str]:
        """
        Envia a mensagem para o Langflow e obtém a resposta.
        
        Args:
            mensagem (str): A mensagem a ser processada pelo Langflow
            session_id (str, optional): ID da sessão existente. Se None, gera um novo.
            
        Returns:
            Optional[str]: A resposta do Langflow ou None em caso de falha
        """
        if not mensagem or not isinstance(mensagem, str):
            logger.error("Mensagem inválida fornecida para o Langflow")
            return None
            
        try:
            langflow_url = URLS["Langflow_URL"].replace("/predict/", "/run/")
            logger.info(f"Obtendo resposta para a mensagem: {mensagem}")
            
            # Usa session_id existente ou gera um novo
            current_session_id = session_id if session_id else str(uuid.uuid4())
            
            # Payload corrigido baseado na estrutura do seu fluxo
            payload = {
                "input_value": mensagem,  # Seu fluxo espera input_value direto
                "output_type": "chat",
                "input_type": "chat",
                "tweaks": {
                    "ChatInput-g5RAZ": {  # Nome exato do seu componente de entrada
                        "session_id": session_id or str(uuid.uuid4()),
                        "sender": "User"
                    }
                }
            }
            
            response = requests.post(
                langflow_url, 
                json=payload,
                timeout=30,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )

            if response.status_code == 200:
                resposta_json = response.json()
                logger.debug(f"Resposta completa do Langflow: {resposta_json}")
                
                # Extração robusta da mensagem de resposta
                try:
                    # Caminho principal baseado na estrutura do JSON fornecido
                    if 'outputs' in resposta_json:
                        for output in resposta_json['outputs']:
                            if 'outputs' in output:
                                for sub_output in output['outputs']:
                                    if 'results' in sub_output:
                                        results = sub_output['results']
                                        if 'message' in results:
                                            message_data = results['message']
                                            if isinstance(message_data, dict):
                                                # Tenta obter o texto da resposta em vários caminhos possíveis
                                                if 'data' in message_data and 'text' in message_data['data']:
                                                    return message_data['data']['text']
                                                elif 'text' in message_data:
                                                    return message_data['text']
                                                elif 'message' in message_data:
                                                    return message_data['message']
                    
                    # Fallback para caminhos alternativos
                    if 'message' in resposta_json:
                        if isinstance(resposta_json['message'], dict):
                            if 'text' in resposta_json['message']:
                                return resposta_json['message']['text']
                            elif 'data' in resposta_json['message'] and 'text' in resposta_json['message']['data']:
                                return resposta_json['message']['data']['text']
                        elif isinstance(resposta_json['message'], str):
                            return resposta_json['message']
                    
                    # Último fallback: procura em toda a estrutura por um campo 'text'
                    if 'text' in resposta_json:
                        return resposta_json['text']
                    
                except (KeyError, TypeError) as e:
                    logger.warning(f"Erro ao extrair resposta: {e}")
                
                logger.warning("Nenhuma resposta válida encontrada no JSON retornado")
                return None
            else:
                logger.error(f"Erro na requisição ao Langflow (status {response.status_code}): {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão com o Langflow: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao obter resposta do Langflow: {e}")
            return None






def main():
    try:
        scraper = OlxScraper()
        if not scraper.executar():
            logger.error("Falha na execução do scraper")
    except KeyboardInterrupt:
        logger.info("Scraper interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")

if __name__ == "__main__":
    main()
