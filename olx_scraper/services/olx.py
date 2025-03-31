from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from utils.logger import logger
from models.anuncio import Anuncio, Mensagem
import time
import json
import os

class OLXService:
    def __init__(self, browser_manager, api_service):
        self.browser = browser_manager
        self.api = api_service
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

    def append_links(self):
        """Acessa a página de favoritos e coleta os links"""
        try:
            # Aguarda a página carregar completamente
            logger.info("Aguardando carregamento da página de favoritos...")
            time.sleep(5)
            
            # Tenta diferentes seletores para encontrar os favoritos
            seletores = [
                (By.CSS_SELECTOR, 'a.css-1tqlkj0'),
                (By.CSS_SELECTOR, '[data-testid="observed-page-link"]'),
                (By.CSS_SELECTOR, '[data-testid="favorites-item"]'),
                (By.CSS_SELECTOR, "a[href*='/favoritos/']"),
                (By.CLASS_NAME, "css-qo0cxu")
            ]
            
            favoritos = None
            for seletor in seletores:
                try:
                    logger.info(f"Tentando encontrar favoritos com seletor: {seletor}")
                    favoritos = self.browser.wait.until(
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
                self._save_debug_page()
                return []
            
            novos_links = set()
            for favorito in favoritos:
                try:
                    link = favorito.get_attribute("href")
                    if not link:
                        link_element = favorito.find_element(By.TAG_NAME, "a")
                        if link_element:
                            link = link_element.get_attribute("href")
                    
                    if not link:
                        logger.warning("Link não encontrado em um favorito")
                        continue
                    
                    if link.startswith('/'):
                        link = f"https://www.olx.pt{link}"
                    
                    if 'reason=observed_ad' in link:
                        link = link.split('?')[0]
                        
                    if "?" in link:
                        link = link.replace("?", "?chat=1&isPreviewActive=0&")
                    else:
                        link = f"{link}?chat=1&isPreviewActive=0"
                    
                    if link not in self.links_cache:
                        novos_links.add(link)
                        self.links_cache.add(link)
                        logger.info(f"Novo link encontrado: {link}")
                    else:
                        logger.debug(f"Link já existe no cache: {link}")
                        novos_links.add(link)
                except Exception as e:
                    logger.error(f"Erro ao processar um favorito: {str(e)}")
                    continue

            logger.info(f"{len(novos_links)} links encontrados (novos e em cache)")
            return list(novos_links)
        
        except Exception as e:
            logger.error(f"Erro ao acessar favoritos: {str(e)}")
            self._save_debug_page()
            return []

    def abrir_anuncios_em_abas(self, links):
        """Abre os anúncios em novas abas e espera o carregamento"""
        aba_principal = self.browser.driver.current_window_handle
        logger.info(f"Abrindo {len(links)} anúncios em novas abas...")
        
        for link in links:
            try:
                logger.info(f"Abrindo: {link}")
                
                self.browser.driver.execute_script(f"window.open('{link}', '_blank');")
                time.sleep(2)
                
                self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])
                
                logger.info("Aguardando carregamento da página...")
                self.browser.wait.until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                self.browser.driver.switch_to.window(aba_principal)
                logger.info("Aba aberta com sucesso")
                
            except Exception as e:
                logger.error(f"Erro ao abrir o link: {e}")
                try:
                    self.browser.driver.switch_to.window(aba_principal)
                except:
                    pass

    def extrair_mensagens_vendedor(self):
        """Extrai mensagens de vendedores e envia para a API"""
        try:
            abas = self.browser.driver.window_handles
            for aba in abas[1:]:  # Pula a primeira aba (favoritos)
                try:
                    self.browser.driver.switch_to.window(aba)
                    time.sleep(2)
                    
                    # Extrair informações do anúncio
                    try:
                        elemento_id = self.browser.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="ad-details-id"]'))
                        )
                        anuncio_id = elemento_id.text.replace("ID: ", "").strip()
                        
                        nome_vendedor = self.browser.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="username"]'))
                        ).text.strip()
                        
                        titulo_anuncio = self.browser.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="ad-details-title"]'))
                        ).text.strip()
                        
                        preco_anuncio = self.browser.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="ad-details-price"]'))
                        ).text.strip()
                        
                        logger.info(f"Informações extraídas - ID: {anuncio_id}, Vendedor: {nome_vendedor}, Título: {titulo_anuncio}, Preço: {preco_anuncio}")
                        
                        # Criar a conversa primeiro
                        if not self.api.criar_conversa(anuncio_id):
                            continue
                        
                        # Atualizar informações do anúncio
                        info_anuncio = {
                            "nome_vendedor": nome_vendedor,
                            "titulo_anuncio": titulo_anuncio,
                            "preco_anuncio": preco_anuncio
                        }
                        if not self.api.atualizar_info_anuncio(anuncio_id, info_anuncio):
                            continue
                        
                    except Exception as e:
                        logger.error(f"Erro ao extrair informações do anúncio: {e}")
                        continue

                    # Processar mensagens
                    self._processar_mensagens(anuncio_id)

                except Exception as e:
                    logger.error(f"Erro ao processar aba: {e}")
                    continue
                    
            try:
                self.browser.driver.switch_to.window(abas[0])
            except:
                pass
            
        except Exception as e:
            logger.error(f"Erro ao buscar mensagens novas: {e}")

    def _processar_mensagens(self, anuncio_id: str):
        """Processa as mensagens de um anúncio"""
        try:
            logger.info("Aguardando carregamento das mensagens...")
            self.browser.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="messages-list-container"]')))

            logger.info("Buscando mensagens recebidas e enviadas...")
            mensagens_recebidas = self.browser.driver.find_elements(By.CSS_SELECTOR, '[data-testid="received-message"] [data-testid="message"] span')
            mensagens_enviadas = self.browser.driver.find_elements(By.CSS_SELECTOR, '[data-testid="sent-message"] [data-testid="message"] span')
            
            if not mensagens_recebidas and not mensagens_enviadas:
                logger.info(f"Nenhuma mensagem encontrada para o anúncio {anuncio_id}")
                return

            todas_mensagens = []
            
            # Processar mensagens recebidas
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

            # Processar mensagens enviadas
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

            # Ordenar mensagens por posição no DOM
            todas_mensagens.sort(key=lambda x: self.browser.driver.execute_script(
                "return arguments[0].getBoundingClientRect().top;", 
                x['elemento']
            ))

            # Enviar mensagens para a API
            logger.info(f"Processando {len(todas_mensagens)} mensagens para o anúncio {anuncio_id}")
            for msg in todas_mensagens:
                try:
                    texto = msg['texto']
                    tipo = msg['tipo']
                    
                    if not self.api.verificar_mensagem_existe(anuncio_id, texto, tipo):
                        if self.api.enviar_mensagem(anuncio_id, texto, tipo):
                            logger.info(f"Mensagem {tipo} registrada com sucesso: {texto}")
                        else:
                            logger.error(f"Falha ao registrar mensagem {tipo}: {texto}")
                    else:
                        logger.info(f"Mensagem já registrada na API: {texto}")
                except Exception as e:
                    logger.error(f"Erro ao processar mensagem: {e}")

        except Exception as e:
            logger.error(f"Erro ao processar mensagens: {e}")

    def _save_debug_page(self):
        """Salva o HTML da página para debug"""
        try:
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(self.browser.driver.page_source)
            logger.info("HTML da página salvo em debug_page.html")
        except Exception as e:
            logger.error(f"Erro ao salvar página de debug: {e}") 