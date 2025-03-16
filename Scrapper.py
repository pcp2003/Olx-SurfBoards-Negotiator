import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
import time


# Função para iniciar o navegador
def iniciar_navegador():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-popup-blocking")  # Desativa o bloqueio de pop-ups
        driver = uc.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"Erro ao iniciar o navegador: {e}")
        return None


# Função para aceitar cookies
def aceitar_cookies(driver, wait):
    try:
        cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]')))
        cookie_button.click()
        print("Cookies aceitos.")
    except Exception as e:
        print(f"Não foi possível aceitar os cookies: {e}")

# Função para fazer login
def login(driver, wait):
    try:
        loginAccount_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainContent"]/div/div[2]/section/div/div/button')))
        loginAccount_button.click()

        username_field = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="username"]')))
        password_field = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="password"]')))

        username_field.send_keys("pedropacheco2709@gmail.com")
        time.sleep(1)
        password_field.send_keys("Manga27090")
        password_field.send_keys(Keys.RETURN)
        print("Login realizado.")
    except Exception as e:
        print(f"Erro no login: {e}")

# Função para acessar a página de favoritos e coletar os links
def acessar_favoritos(driver, wait):
    try:
        wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="mainContent"]/div/div[2]/section/div[2]/div')))
        favoritos = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "css-qo0cxu")))

        links = set()  # Usando um set para evitar duplicatas

        for favorito in favoritos:
            try:
                link = favorito.get_attribute("href")
                if link and link not in links:
                    links.add(link.replace("?", "?chat=1&isPreviewActive=0&"))

            except Exception as e:
                print(f"Erro ao processar um favorito: {e}")

        print(f"{len(links)} links únicos encontrados.")
        return list(links)  # Convertendo de volta para lista

    except Exception as e:
        print(f"Erro ao acessar favoritos: {e}")
        return []

# Função para abrir os anúncios em abas (sem duplicar)
def abrir_anuncios_em_abas(driver, links):
    for link in links:
        try:
            print(f"Abrindo: {link}")
            driver.execute_script(f"window.open('{link}', '_blank');")
            time.sleep(1)  # Pequeno delay para evitar bloqueios

        except Exception as e:
            print(f"Erro ao abrir o link: {e}")

# Função para finalizar a execução
def finalizar(driver):
    if driver:
        try:
            driver.quit()
            print("Navegador fechado.")
        except Exception as e:
            print(f"Erro ao fechar o navegador: {e}")

# Função principal
def main():
    driver = iniciar_navegador()
    if driver:
        wait = WebDriverWait(driver, 10)

        driver.get("https://www.olx.pt/favoritos/")

        aceitar_cookies(driver, wait)
        login(driver, wait)

        # Coleta os links dos favoritos (sem duplicar)
        links = acessar_favoritos(driver, wait)

        # Abre os anúncios em abas
        abrir_anuncios_em_abas(driver, links)

        # Finaliza o navegador
        finalizar(driver)

if __name__ == "__main__":
    main()
