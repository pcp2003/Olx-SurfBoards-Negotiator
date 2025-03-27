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
        logger.info("Inicializando OlxScraper...")
        self.driver = None
        self.wait = None
        self.links_cache = set()
        self.load_cache()
        self.api_url = URLS["api"]  # URL da API FastAPI do arquivo de configuração
        logger.info(f"API URL configurada: {self.api_url}")
        
        # Adicionando métricas
        self.metricas = {
            'mensagens_processadas': 0,
            'respostas_enviadas': 0,
            'erros': 0,
            'inicio_execucao': None,
            'ultima_verificacao': None,
            'tempo_total_execucao': 0
        }
        logger.info("Métricas inicializadas")

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

    def iniciar_navegador(self):
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
                cookie_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))
                )
                cookie_button.click()
                logger.info("Cookies aceitos com sucesso")
                return True
            except TimeoutException:
                logger.warning(f"Tentativa {attempt + 1} de aceitar cookies falhou")
                if attempt < TIMEOUTS["max_retries"] - 1:
                    time.sleep(TIMEOUTS["retry_delay"])
            except Exception as e:
                logger.error(f"Erro ao aceitar cookies: {e}")
                return False
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
            except TimeoutException:
                logger.warning(f"Tentativa {attempt + 1} de login falhou")
                if attempt < TIMEOUTS["max_retries"] - 1:
                    time.sleep(TIMEOUTS["retry_delay"])
            except Exception as e:
                logger.error(f"Erro no login: {e}")
                return False
        logger.error("Todas as tentativas de login falharam")
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
        logger.info(f"Abrindo {len(links)} anúncios em novas abas...")
        
        for link in links:
            try:
                logger.info(f"Abrindo: {link}")
                
                # Abre nova aba
                self.driver.execute_script(f"window.open('{link}', '_blank');")
                time.sleep(2)  # Espera a aba abrir
                
                # Muda para a nova aba
                self.driver.switch_to.window(self.driver.window_handles[-1])
                
                # Espera a página carregar
                logger.info("Aguardando carregamento da página...")
                self.wait.until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Volta para a aba principal
                self.driver.switch_to.window(aba_principal)
                logger.info("Aba aberta com sucesso")
                
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
                logger.info("Salvando cache de links...")
                self.save_cache()
                
                logger.info("Fechando navegador...")
                self.driver.quit()
                logger.info("Navegador fechado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao fechar o navegador: {e}")


    # Novas alterações

    

    def atualizar_metricas(self, tipo: str, valor: Any = 1) -> None:
        """Atualiza as métricas do scraper"""
        try:
            if tipo in self.metricas:
                if isinstance(self.metricas[tipo], (int, float)):
                    self.metricas[tipo] += valor
                    logger.debug(f"Métrica '{tipo}' atualizada para {self.metricas[tipo]}")
                else:
                    self.metricas[tipo] = valor
                    logger.debug(f"Métrica '{tipo}' definida para {valor}")
            else:
                logger.warning(f"Tipo de métrica desconhecido: {tipo}")
        except Exception as e:
            logger.error(f"Erro ao atualizar métricas: {e}")

    def log_metricas(self) -> None:
        """Registra as métricas atuais"""
        try:
            logger.info("=== Métricas do Scraper ===")
            for key, value in self.metricas.items():
                if isinstance(value, datetime):
                    logger.info(f"  {key}: {value.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    logger.info(f"  {key}: {value}")
            logger.info("==========================")
        except Exception as e:
            logger.error(f"Erro ao registrar métricas: {e}")

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
                elif response.status_code == 404:
                    logger.warning("Endpoint de verificação de mensagem não encontrado")
                    return False
                else:
                    logger.error(f"Erro ao verificar mensagem na API: {response.text}")
                    if tentativa < max_tentativas - 1:
                        time.sleep(2)
            except requests.exceptions.Timeout:
                logger.error(f"Timeout ao verificar mensagem (tentativa {tentativa + 1})")
                if tentativa < max_tentativas - 1:
                    time.sleep(2)
            except requests.exceptions.ConnectionError:
                logger.error(f"Erro de conexão ao verificar mensagem (tentativa {tentativa + 1})")
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
                elif response.status_code == 404:
                    logger.warning("Endpoint de envio de mensagem não encontrado")
                    return False
                else:
                    logger.error(f"Erro ao registrar mensagem na API: {response.text}")
                    if tentativa < max_tentativas - 1:
                        time.sleep(2)
            except requests.exceptions.Timeout:
                logger.error(f"Timeout ao enviar mensagem (tentativa {tentativa + 1})")
                if tentativa < max_tentativas - 1:
                    time.sleep(2)
            except requests.exceptions.ConnectionError:
                logger.error(f"Erro de conexão ao enviar mensagem (tentativa {tentativa + 1})")
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
                params={"email": CREDENTIALS["username"]},
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("conversas_pendentes", [])
            elif response.status_code == 404:
                logger.warning("Endpoint de conversas pendentes não encontrado")
                return []
            else:
                logger.error(f"Erro ao buscar conversas pendentes: {response.text}")
                return []
        except requests.exceptions.Timeout:
            logger.error("Timeout ao buscar conversas pendentes")
            return []
        except requests.exceptions.ConnectionError:
            logger.error("Erro de conexão ao buscar conversas pendentes")
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
                        logger.info(f"Anúncio {anuncio_id} encontrado na aba")
                        break
                else:
                    logger.error(f"Anúncio {anuncio_id} não encontrado nas abas abertas")
                    if tentativa < max_tentativas - 1:
                        time.sleep(2)
                    continue

                # Encontrar e preencher campo de mensagem
                logger.info("Procurando campo de mensagem...")
                campo_mensagem = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "message.text"))
                )

                # Limpar campo e enviar mensagem
                logger.info("Enviando mensagem...")
                campo_mensagem.clear()
                campo_mensagem.send_keys(mensagem)
                campo_mensagem.send_keys(Keys.RETURN)
                
                # Verificar se a mensagem foi enviada
                time.sleep(2)  # Pequena pausa para garantir o envio
                logger.info(f"Mensagem enviada com sucesso: {mensagem}")
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
                    logger.info("Aguardando carregamento das mensagens...")
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="messages-list-container"]')))

                    # Buscar todas as mensagens (recebidas e enviadas)
                    logger.info("Buscando mensagens recebidas e enviadas...")
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
                                logger.debug(f"Mensagem recebida encontrada: {texto}")
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
                                logger.debug(f"Mensagem enviada encontrada: {texto}")
                        except Exception as e:
                            logger.error(f"Erro ao processar mensagem enviada: {e}")

                    # Ordenar mensagens por posição no DOM (ordem de recebimento)
                    todas_mensagens.sort(key=lambda x: self.driver.execute_script(
                        "return arguments[0].getBoundingClientRect().top;", 
                        x['elemento']
                    ))

                    # Enviar todas as mensagens para a API
                    logger.info(f"Processando {len(todas_mensagens)} mensagens para o anúncio {anuncio_id}")
                    for msg in todas_mensagens:
                        try:
                            texto = msg['texto']
                            tipo = msg['tipo']
                            
                            # Verificar se a mensagem já existe antes de enviar
                            if not self.verificar_mensagem_existe(anuncio_id, texto, tipo):
                                if self.enviar_mensagem_para_api(anuncio_id, texto, tipo):
                                    logger.info(f"Mensagem {tipo} registrada com sucesso: {texto}")
                                else:
                                    logger.error(f"Falha ao registrar mensagem {tipo}: {texto}")
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
                                    if self.enviar_mensagem_olx(conversa['anuncio_id'], resposta):
                                        logger.info(f"Resposta enviada: {resposta}")
                                        self.atualizar_metricas('respostas_enviadas')
                                    else:
                                        logger.error(f"Falha ao enviar resposta no OLX")
                                        self.atualizar_metricas('erros')
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
            logger.info("Iniciando execução do scraper...")
            
            if not self.iniciar_navegador():
                logger.error("Falha ao iniciar o navegador")
                return False

            logger.info("Acessando página de favoritos...")
            self.driver.get(URLS["favorites"])

            if not self.aceitar_cookies():
                logger.error("Falha ao aceitar cookies")
                return False
                
            if not self.login():
                logger.error("Falha no login")
                return False

            # Coleta links e abre abas
            logger.info("Coletando links dos anúncios...")
            links = self.append_links()
            if not links:
                logger.warning("Nenhum link encontrado para processar")
                return True

            logger.info(f"Abrindo {len(links)} anúncios em abas...")
            self.abrir_anuncios_em_abas(links)
            
            # Processa mensagens
            logger.info("Processando mensagens existentes...")
            self.extrair_mensagens_vendedor()
            
            # Inicia ciclo de respostas
            logger.info("Iniciando ciclo de respostas...")
            self.ciclo_de_respostas()

            return True
        except Exception as e:
            logger.error(f"Erro durante a execução: {e}")
            self.atualizar_metricas('erros')
            return False
        finally:
            logger.info("Finalizando execução...")
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
            
            # Payload atualizado baseado na nova estrutura do fluxo
            payload = {
                "output_type": "chat",
                "input_type": "chat",
                "tweaks": {
                    "ChatOutput-trXWe": {
                        "background_color": "",
                        "chat_icon": "",
                        "clean_data": True,
                        "data_template": "{text}",
                        "input_value": "",
                        "sender": "Machine",
                        "sender_name": "AI",
                        "session_id": current_session_id,
                        "should_store_message": True,
                        "text_color": ""
                    },
                    "GetEnvVar-fD5AB": {
                        "env_dir": "",
                        "env_var_name": "",
                        "tools_metadata": [
                            {
                                "name": "GetEnvVar-process_inputs",
                                "description": "process_inputs() - Get env var from a specified directory",
                                "tags": ["GetEnvVar-process_inputs"]
                            }
                        ]
                    },
                    "CustomComponent-ZQxeP": {
                        "acao": "",
                        "anuncio_id": "",
                        "conversa_id": "",
                        "email": "",
                        "mensagem": "",
                        "respondida": "",
                        "tipo": "",
                        "tools_metadata": [
                            {
                                "name": "FastAPIClient-process_inputs",
                                "description": "process_inputs() - Componente para acessar APIs do FastAPI e interagir com a DB",
                                "tags": ["FastAPIClient-process_inputs"]
                            }
                        ]
                    },
                    "CustomComponent-iJBo4": {
                        "input": "",
                        "tools_metadata": [
                            {
                                "name": "ActionSelector-process_inputs",
                                "description": "process_inputs() - Componente para selecionar a ação a ser executada baseado no contexto da conversa",
                                "tags": ["ActionSelector-process_inputs"]
                            }
                        ]
                    },
                    "Agent-tIIK7": {
                        "add_current_date_tool": True,
                        "agent_description": "A helpful assistant with access to the following tools:",
                        "agent_llm": "OpenAI",
                        "api_key": "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",
                        "handle_parsing_errors": True,
                        "input_value": mensagem,
                        "json_mode": False,
                        "max_iterations": 15,
                        "max_retries": 5,
                        "max_tokens": None,
                        "model_kwargs": {},
                        "model_name": "gpt-4o-mini",
                        "n_messages": 100,
                        "openai_api_base": "",
                        "order": "Ascending",
                        "seed": 1,
                        "sender": "Machine and User",
                        "sender_name": "",
                        "session_id": current_session_id,
                        "system_prompt": "# Instruções para o AIAgent - Gerenciador de Negociações OLX\n\n## Visão Geral\nVocê é um agente especializado em gerenciar negociações de pranchas de surf no OLX. Você tem acesso a três ferramentas principais que devem ser utilizadas em conjunto para gerenciar as conversas e mensagens.\n\n## Ferramentas Disponíveis\n\n### 1. GetEnvVar\n- **Propósito**: Obter credenciais e configurações do arquivo .env\n- **Uso Inicial**: \n  - Primeiro, você DEVE usar esta ferramenta para obter o email do usuário\n  - Diretório: `C:\\Users\\pedro\\programas\\Olx-SurfBoards-Negotiator`\n  - Variável: `OLX_USERNAME`\n  - Este email será usado em todas as chamadas do FastAPIClient\n\n### 2. ActionSelector\n- **Propósito**: Determinar qual ação deve ser executada baseado no contexto\n- **Ações Possíveis**:\n  - `buscar_mensagens`: Buscar histórico de mensagens\n  - `enviar_mensagem`: Enviar uma nova mensagem\n- **Uso**:\n  - Use esta ferramenta antes de qualquer interação com o FastAPIClient\n  - Forneça o contexto da conversa ou instrução clara\n  - A ferramenta retornará a ação apropriada baseada em palavras-chave:\n    - Para buscar: \"buscar\", \"procurar\", \"encontrar\", \"listar\", \"ver\", \"mostrar\"\n    - Para enviar: \"enviar\", \"mandar\", \"responder\", \"resposta\", \"mensagem\"\n\n### 3. FastAPIClient\n- **Propósito**: Executar ações na API\n- **Parâmetros**:\n  - `acao`: Ação a ser executada (vem do ActionSelector)\n  - `email`: Email do usuário (vem do GetEnvVar)\n  - `anuncio_id`: ID do anúncio (quando necessário)\n  - `mensagem`: Texto da mensagem (quando necessário)\n  - `tipo`: Tipo da mensagem (\"recebida\" ou \"enviada\")\n  - `conversa_id`: ID da conversa (opcional, para filtrar mensagens)\n  - `respondida`: Status de resposta (opcional, para filtrar mensagens)\n- **Fluxo de Uso**:\n  1. Obter email do GetEnvVar\n  2. Usar ActionSelector para determinar a ação\n  3. Executar a ação via FastAPIClient\n\n## Fluxo de Trabalho\n\n1. **Inicialização**:\n   - Use GetEnvVar para obter o OLX_USERNAME\n   - Guarde este email para uso posterior\n\n2. **Ciclo de Trabalho**:\n   - Use ActionSelector para determinar a próxima ação\n   - Execute a ação via FastAPIClient\n   - Processe a resposta\n   - Repita o ciclo\n\n3. **Regras de Validação**:\n   - Sempre verifique se o email foi obtido antes de usar o FastAPIClient\n   - Use o ActionSelector antes de cada chamada ao FastAPIClient\n   - Verifique as respostas da API para garantir sucesso das operações\n\n## Exemplos de Uso\n\n1. **Buscar Mensagens**:\n   ```python\n   # 1. Obter email\n   email = GetEnvVar(env_var_name=\"OLX_USERNAME\", env_dir=\"C:\\\\Users\\\\pedro\\\\programas\\\\Olx-SurfBoards-Negotiator\")\n   \n   # 2. Determinar ação\n   acao = ActionSelector(input=\"buscar mensagens não respondidas\")\n   \n   # 3. Executar ação\n   resultado = FastAPIClient(\n       acao=\"buscar_mensagens\",\n       email=email,\n       respondida=\"false\"\n   )\n   ```\n\n2. **Enviar Mensagem**:\n   ```python\n   # 1. Determinar ação\n   acao = ActionSelector(input=\"enviar mensagem para o anúncio 123\")\n   \n   # 2. Executar ação\n   resultado = FastAPIClient(\n       acao=\"enviar_mensagem\",\n       email=email,\n       anuncio_id=\"123\",\n       mensagem=\"Olá, gostaria de saber mais sobre a prancha\"\n   )\n   ```\n\n## Tratamento de Erros\n- Se o GetEnvVar falhar, não prossiga com outras operações\n- Se o ActionSelector retornar uma ação inválida, use \"buscar_mensagens\" como fallback\n- Se o FastAPIClient retornar erro, tente novamente ou mude a ação\n\n## Prioridades\n1. Manter o email do usuário sempre atualizado\n2. Usar o ActionSelector para cada decisão\n3. Verificar respostas da API antes de prosseguir"
                    }
                }
            }
            
            max_tentativas = 3
            tempo_espera_base = 5  # Tempo base de espera em segundos
            
            for tentativa in range(max_tentativas):
                try:
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
                    elif response.status_code == 429:  # Rate limit
                        tempo_espera = tempo_espera_base * (2 ** tentativa)  # Backoff exponencial
                        logger.warning(f"Rate limit atingido. Aguardando {tempo_espera} segundos antes da próxima tentativa...")
                        time.sleep(tempo_espera)
                        continue
                    else:
                        logger.error(f"Erro na requisição ao Langflow (status {response.status_code}): {response.text}")
                        if tentativa < max_tentativas - 1:
                            time.sleep(tempo_espera_base)
                        continue
                        
                except requests.exceptions.Timeout:
                    logger.error(f"Timeout na tentativa {tentativa + 1}")
                    if tentativa < max_tentativas - 1:
                        time.sleep(tempo_espera_base)
                except requests.exceptions.ConnectionError:
                    logger.error(f"Erro de conexão na tentativa {tentativa + 1}")
                    if tentativa < max_tentativas - 1:
                        time.sleep(tempo_espera_base)
                except Exception as e:
                    logger.error(f"Erro inesperado na tentativa {tentativa + 1}: {e}")
                    if tentativa < max_tentativas - 1:
                        time.sleep(tempo_espera_base)
            
            return None
                
        except Exception as e:
            logger.error(f"Erro inesperado ao obter resposta do Langflow: {e}")
            return None






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
