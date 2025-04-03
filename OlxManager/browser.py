import logging
import time
import requests
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc
from typing import Optional

from config import BROWSER_OPTIONS, TIMEOUTS, CREDENTIALS, URLS

logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self, api_manager):
        self.driver = None
        self.wait = None
        self.api = api_manager

    def iniciar_navegador(self):
        """Inicia o navegador com as configurações especificadas"""
        try:
            logger.info("Configurando opções do navegador...")
            
            # Configuração do ChromeDriver com undetected-chromedriver
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-save-password-bubble')
            options.add_argument('--disable-single-click-autofill')
            options.add_argument('--disable-translate')
            options.add_argument('--disable-web-security')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--start-maximized')
            
            self.driver = uc.Chrome(
                options=options,
                version_main=134,
                use_subprocess=True,
                suppress_welcome=True,
                log_level=3
            )
            
            # Configuração do timeout
            self.driver.set_page_load_timeout(TIMEOUTS["page_load"])
            self.wait = WebDriverWait(self.driver, TIMEOUTS["element_wait"])
            
            # Configurações adicionais do driver
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
            })
            
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
                (By.CSS_SELECTOR, 'a.css-1tqlkj0'),  # Novo seletor para links de anúncios
                (By.CSS_SELECTOR, '[data-testid="observed-page-link"]'),
                (By.CSS_SELECTOR, '[data-testid="favorites-item"]'),
                (By.CSS_SELECTOR, "a[href*='/favoritos/']"),
                (By.CLASS_NAME, "css-qo0cxu")
            ]
            
            favoritos = None
            for seletor in seletores:
                try:
                    logger.info(f"Tentando encontrar favoritos com seletor: {seletor}")
                    # Aguarda até que pelo menos um elemento seja encontrado
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
                # Salva o HTML da página para debug
                try:
                    with open("debug_page.html", "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    logger.info("HTML da página salvo em debug_page.html")
                except:
                    pass
                return []
            
            novos_links = set()
            for favorito in favoritos:
                try:
                    # Tenta obter o link de diferentes maneiras
                    link = favorito.get_attribute("href")
                    if not link:
                        # Se não encontrar href direto, tenta encontrar um elemento <a> dentro
                        link_element = favorito.find_element(By.TAG_NAME, "a")
                        if link_element:
                            link = link_element.get_attribute("href")
                    
                    if not link:
                        logger.warning("Link não encontrado em um favorito")
                        continue
                    
                    # Converte link relativo para absoluto se necessário
                    if link.startswith('/'):
                        link = f"https://www.olx.pt{link}"
                    
                    # Remove parâmetros desnecessários do link
                    if 'reason=observed_ad' in link:
                        link = link.split('?')[0]
                        
                    # Adiciona parâmetros necessários ao link
                    if "?" in link:
                        link = link.replace("?", "?chat=1&isPreviewActive=0&")
                    else:
                        link = f"{link}?chat=1&isPreviewActive=0"
                    
                    novos_links.add(link)
                    logger.info(f"Novo link encontrado: {link}")
                except Exception as e:
                    logger.error(f"Erro ao processar um favorito: {str(e)}")
                    continue

            logger.info(f"{len(novos_links)} links encontrados")
            if novos_links:
                logger.info("Links encontrados:")
                for link in novos_links:
                    logger.info(f"- {link}")
            return list(novos_links)
        
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
                logger.info("Fechando navegador...")
                self.driver.quit()
                logger.info("Navegador fechado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao fechar o navegador: {e}")

    def reabrir_anuncio(self, anuncio_id: str) -> bool:
        """Reabre a aba de um anúncio específico se ela não estiver disponível"""
        try:
            # Verifica se a aba já está aberta
            abas = self.driver.window_handles
            for aba in abas[1:]:  # Pula a primeira aba (favoritos)
                self.driver.switch_to.window(aba)
                if anuncio_id in self.driver.current_url:
                    logger.info(f"Anúncio {anuncio_id} já está aberto em uma aba")
                    return True
            
            # Se não estiver aberto, tenta reabrir
            logger.info(f"Tentando reabrir anúncio {anuncio_id}...")
            url = f"https://www.olx.com.br/item/{anuncio_id}"
            self.driver.execute_script(f"window.open('{url}', '_blank');")
            time.sleep(2)
            
            # Muda para a nova aba
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # Espera a página carregar
            self.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info(f"Anúncio {anuncio_id} reaberto com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao reabrir anúncio {anuncio_id}: {e}")
            return False

    def enviar_mensagem_olx(self, anuncio_id: str, mensagem: str) -> bool:
        """Envia a mensagem de resposta no OLX"""
        max_tentativas = 3
        for tentativa in range(max_tentativas):
            try:
                # Encontrar a aba correta do anúncio
                abas = self.driver.window_handles
                encontrou_aba = False
                
                for aba in abas[1:]:  # Pula a primeira aba (favoritos)
                    self.driver.switch_to.window(aba)
                    if anuncio_id in self.driver.current_url:
                        logger.info(f"Anúncio {anuncio_id} encontrado na aba")
                        encontrou_aba = True
                        break
                
                # Se não encontrou a aba, tenta reabrir
                if not encontrou_aba:
                    logger.info(f"Anúncio {anuncio_id} não encontrado nas abas abertas, tentando reabrir...")
                    if not self.reabrir_anuncio(anuncio_id):
                        logger.error(f"Não foi possível reabrir o anúncio {anuncio_id}")
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
                    
                    # Extrair informações do anúncio e vendedor
                    try:
                        # ID do anúncio
                        elemento_id = self.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="ad-details-id"]'))
                        )
                        anuncio_id = elemento_id.text.replace("ID: ", "").strip()
                        
                        # Nome do vendedor
                        nome_vendedor = self.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="username"]'))
                        ).text.strip()
                        
                        # Título do anúncio
                        titulo_anuncio = self.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="ad-details-title"]'))
                        ).text.strip()
                        
                        # Preço do anúncio
                        preco_anuncio = self.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="ad-details-price"]'))
                        ).text.strip()
                        
                        logger.info(f"Informações extraídas - ID: {anuncio_id}, Vendedor: {nome_vendedor}, Título: {titulo_anuncio}, Preço: {preco_anuncio}")
                        
                        # Criar a conversa primeiro
                        criar_response = requests.post(
                            f"{URLS['api']}/criar-conversa",
                            params={
                                "email": CREDENTIALS["username"],
                                "anuncio_id": anuncio_id
                            },
                            timeout=10
                        )
                        
                        if criar_response.status_code != 200:
                            logger.error(f"Erro ao criar conversa: {criar_response.text}")
                            continue
                        
                        # Enviar informações para a API
                        self.api.enviar_info_anuncio_para_api(
                            anuncio_id=anuncio_id,
                            nome_vendedor=nome_vendedor,
                            titulo_anuncio=titulo_anuncio,
                            preco_anuncio=preco_anuncio
                        )
                        
                    except Exception as e:
                        logger.error(f"Erro ao extrair informações do anúncio: {e}")
                        continue

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
                            if not self.api.verificar_mensagem_existe(anuncio_id, texto, tipo):
                                if self.api.enviar_mensagem_para_api(anuncio_id, texto, tipo):
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

    def obter_searched_info(self, anuncio_id: str) -> Optional[str]:
        """Obtém informações detalhadas do anúncio"""
        try:
            # Guarda a aba principal
            aba_principal = self.driver.current_window_handle
            
            # Procura a aba do anúncio
            for handle in self.driver.window_handles:
                self.driver.switch_to.window(handle)
                if anuncio_id in self.driver.current_url:
                    break
            
            # Aguarda carregamento da página
            self.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Coleta informações do anúncio
            info = []
            
            # Título do anúncio
            try:
                titulo = self.driver.find_element(By.CSS_SELECTOR, "h1.css-1soizd2").text
                info.append(f"Título: {titulo}")
            except:
                logger.warning("Não foi possível obter o título do anúncio")
            
            # Preço
            try:
                preco = self.driver.find_element(By.CSS_SELECTOR, "h3.css-46itwz").text
                info.append(f"Preço: {preco}")
            except:
                logger.warning("Não foi possível obter o preço do anúncio")
            
            # Descrição
            try:
                descricao = self.driver.find_element(By.CSS_SELECTOR, "div.css-g5mtbi").text
                info.append(f"Descrição: {descricao}")
            except:
                logger.warning("Não foi possível obter a descrição do anúncio")
            
            # Características
            try:
                caracteristicas = self.driver.find_elements(By.CSS_SELECTOR, "div.css-1wws9er")
                if caracteristicas:
                    info.append("Características:")
                    for carac in caracteristicas:
                        info.append(f"- {carac.text}")
            except:
                logger.warning("Não foi possível obter as características do anúncio")
            
            # Localização
            try:
                localizacao = self.driver.find_element(By.CSS_SELECTOR, "p.css-1wws9er").text
                info.append(f"Localização: {localizacao}")
            except:
                logger.warning("Não foi possível obter a localização do anúncio")
            
            # Data de publicação
            try:
                data_pub = self.driver.find_element(By.CSS_SELECTOR, "span.css-19yf5ek").text
                info.append(f"Data de publicação: {data_pub}")
            except:
                logger.warning("Não foi possível obter a data de publicação")
            
            # Volta para a aba principal
            self.driver.switch_to.window(aba_principal)
            
            if info:
                return "\n".join(info)
            else:
                logger.warning("Nenhuma informação foi coletada do anúncio")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao obter informações do anúncio: {e}")
            return None 