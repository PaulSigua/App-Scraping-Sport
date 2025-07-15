import time
import os
import csv
import json
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from services.driver import get_chrome_driver
from services.clean_text import LimpiezaComentarios

load_dotenv()
EMAIL = os.getenv("TWITTER_EMAIL")
PASSWORD = os.getenv("TWITTER_PASSWORD")
USERNAME = os.getenv("TWITTER_USERNAME")


class ScraperX:
    def __init__(self, palabra_clave=None, max_posts=None, scrolls=5):
        self.palabra_clave = palabra_clave
        self.max_posts = max_posts
        self.scrolls = scrolls
        self.driver = get_chrome_driver()
        self.tweets_data = []

    def open_twitter_login(self):
        self.driver.get("https://x.com/i/flow/login")
        time.sleep(3)

        try:
            # Paso 1: ingresar email
            correo_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
            correo_input.send_keys(EMAIL, Keys.RETURN)
            time.sleep(2)

            # # Paso 2: bucle para manejar redirección a input de usuario (que también usa name="text")
            # for _ in range(8):
            #     try:
            #         print("Verificando si hay que ingresar nombre de usuario...")
            #         username_input = WebDriverWait(self.driver, 3).until(
            #             EC.presence_of_element_located((By.NAME, "text"))
            #         )
            #         if username_input.is_displayed():
            #             username_input.clear()
            #             username_input.send_keys(USERNAME, Keys.RETURN)
            #             print("Nombre de usuario ingresado")
            #             time.sleep(2)
            #             break
            #     except:
            #         print("Esperando el campo de username...")
            #         time.sleep(1)

            # Paso 3: ahora sí esperar el campo de contraseña
            time.sleep(3)   
            print("Verificando si hay que ingresar nombre de usuario...")
            username_input = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
            username_input.send_keys(USERNAME, Keys.RETURN)
            time.sleep(3)
            print("Esperando campo de contraseña...")
            password_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_input.send_keys(PASSWORD, Keys.RETURN)
            print("Contraseña ingresada")

            time.sleep(5)
            print("Sesión iniciada correctamente")

        except Exception as e:
            print(f"Error al iniciar sesión en Twitter: {e}")
            self.driver.save_screenshot("error_login_x.png")
            raise

    def buscar_tweets(self):
        WebDriverWait(self.driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, '//a[@href="/explore" and @role="link"]'))
        ).click()
        print("🔎 Sección 'Explorar' abierta")

        search_input = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//input[@data-testid="SearchBox_Search_Input"]'))
        )
        search_input.clear()
        search_input.send_keys(self.palabra_clave, Keys.RETURN)
        print(f"🔍 Búsqueda de: {self.palabra_clave}")
        time.sleep(5)

        tweet_links = self.get_tweet_links()
        for idx, tweet_url in enumerate(tweet_links):
            print(f"📄 Procesando tweet {idx+1}/{self.max_posts}")
            tweet_data = self.open_tweet_and_extract(tweet_url)
            if tweet_data:
                self.tweets_data.append(tweet_data)

    def get_tweet_links(self):
        for i in range(4):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print(f"⬇ Scroll adicional ({i+1}/4)")
            time.sleep(2.5)

        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//article[@role="article"]'))
        )
        articles = self.driver.find_elements(By.XPATH, '//article[@role="article"]')
        tweet_links = []

        for article in articles:
            try:
                link_elem = article.find_element(By.XPATH, './/a[contains(@href, "/status/")]')
                tweet_url = link_elem.get_attribute("href")
                if tweet_url and tweet_url not in tweet_links:
                    tweet_links.append(tweet_url)
                if len(tweet_links) >= self.max_posts:
                    break
            except:
                continue

        print(f"🔗 Enlaces a tweets encontrados: {len(tweet_links)}")
        return tweet_links

    def open_tweet_and_extract(self, tweet_url):
        try:
            self.driver.get(tweet_url)
            print(f"🔍 Abriendo tweet: {tweet_url}")
            time.sleep(3)

            for i in range(self.scrolls):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                print(f"⬇ Scroll en tweet ({i+1}/{self.scrolls})")
                time.sleep(3)

            all_texts = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '//div[@data-testid="tweetText"]'))
            )
            tweet_text = all_texts[0].text.strip()

            tweet_articles = self.driver.find_elements(By.XPATH, '//article[@role="article"]')
            comentarios = []
            for article in tweet_articles[1:]:
                try:
                    user_elem = article.find_element(By.XPATH, './/div[@data-testid="User-Name"]//a')
                    usuario = user_elem.get_attribute("href").split("/")[-1]
                    comentario_texto = article.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text.strip()
                    if comentario_texto:
                        comentarios.append({
                            "usuario": usuario,
                            "texto": comentario_texto
                        })
                except:
                    continue

            username_elem = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@data-testid="User-Name"]//a'))
            )
            username = username_elem.get_attribute("href").split("/")[-1]

            time_elem = self.driver.find_element(By.XPATH, '//time')
            fecha = time_elem.get_attribute("datetime")

            return {
                "tweet_url": tweet_url,
                "username": username,
                "tweet_text": tweet_text,
                "fecha": fecha,
                "comments": comentarios
            }

        except Exception as e:
            print(f"⚠ Error al procesar tweet: {e}")
            return None

    def guardar_json(self, 
                     json_raw_path="src/data/tweets_raw.json", 
                     json_clean_path="src/data/tweets_clean.json"):
        with open(json_raw_path, "w", encoding="utf-8") as f:
            json.dump(self.tweets_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Datos crudos guardados en: {json_raw_path}")

        limpiador = LimpiezaComentarios()
        clean_data = []

        for tweet in self.tweets_data:
            for comment in tweet["comments"]:
                if not limpiador.es_espanol(comment["texto"]):
                    continue
                limpio = limpiador.limpiar_texto(
                    comment["texto"],
                    eliminar_numeros=True,
                    quitar_stopwords=True,
                    aplicar_lema=True
                )
                if len(limpio.split()) >= 3:
                    clean_data.append({
                        "tweet_id": tweet["tweet_text"],
                        "comment_user": comment["usuario"],
                        "comment_text": limpio
                    })

        with open(json_clean_path, "w", encoding="utf-8") as f:
            json.dump(clean_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Comentarios limpios guardados en: {json_clean_path}")

        self.driver.quit()

        return {
            "archivo_raw": json_raw_path,
            "archivo_limpio": json_clean_path,
            "total_raw": len(self.tweets_data),
            "total_limpio": len(clean_data)
        }