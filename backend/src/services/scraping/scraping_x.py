import time
import os
import csv
import json
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from services.clean_text import LimpiezaComentarios

load_dotenv()
EMAIL = os.getenv("TWITTER_EMAIL")
PASSWORD = os.getenv("TWITTER_PASSWORD")
USERNAME = os.getenv("TWITTER_USERNAME")


def open_twitter_login(driver):
    driver.get("https://x.com/i/flow/login")
    time.sleep(3)
    driver.find_element(By.NAME, "text").send_keys(EMAIL, Keys.RETURN)
    time.sleep(3)
    driver.find_element(By.NAME, "text").send_keys(USERNAME, Keys.RETURN)
    time.sleep(3)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD, Keys.RETURN)
    time.sleep(5)
    print("Sesión iniciada")


def go_to_explore(driver):
    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable(
            (By.XPATH, '//a[@href="/explore" and @role="link"]'))
    ).click()
    print("Sección 'Explorar' lista")


def search_keyword(driver, keyword):
    search_input = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.XPATH, '//input[@data-testid="SearchBox_Search_Input"]'))
    )
    search_input.clear()
    search_input.send_keys(keyword, Keys.RETURN)
    print(f"🔍 Búsqueda de: {keyword}")
    time.sleep(5)


def get_tweet_links(driver, max_count, extra_scrolls=4):
    for i in range(extra_scrolls):
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        print(f"⬇ Scroll adicional en búsqueda ({i+1}/{extra_scrolls})")
        time.sleep(2.5)

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.XPATH, '//article[@role="article"]'))
    )

    articles = driver.find_elements(By.XPATH, '//article[@role="article"]')
    tweet_links = []

    for article in articles:
        try:
            link_elem = article.find_element(
                By.XPATH, './/a[contains(@href, "/status/")]')
            tweet_url = link_elem.get_attribute("href")
            if tweet_url and tweet_url not in tweet_links:
                tweet_links.append(tweet_url)
            if len(tweet_links) >= max_count:
                break
        except:
            continue

    print(f"🔗 Enlaces a tweets encontrados: {len(tweet_links)}")
    return tweet_links


def open_tweet_and_extract(driver, tweet_url, scrolls=4, wait_scroll=3):
    try:
        driver.get(tweet_url)
        print(f"Abriendo tweet: {tweet_url}")
        time.sleep(3)

        for i in range(scrolls):
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            print(f"Scroll {i+1}/{scrolls}")
            time.sleep(wait_scroll)

        # Texto del tweet y comentarios
        all_texts = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, '//div[@data-testid="tweetText"]'))
        )
        tweet_text = all_texts[0].text.strip()

        # Obtener todos los artículos que contienen tweets y respuestas
        tweet_articles = driver.find_elements(
            By.XPATH, '//article[@role="article"]')

        comentarios = []
        # ignoramos el primer tweet original
        for article in tweet_articles[1:]:
            try:
                user_elem = article.find_element(
                    By.XPATH, './/div[@data-testid="User-Name"]//a')
                usuario = user_elem.get_attribute("href").split("/")[-1]
                comentario_texto = article.find_element(
                    By.XPATH, './/div[@data-testid="tweetText"]').text.strip()
                if comentario_texto:
                    comentarios.append({
                        "usuario": usuario,
                        "texto": comentario_texto
                    })
            except:
                continue

        # Usuario del tweet original
        username_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@data-testid="User-Name"]//a'))
        )
        username = username_elem.get_attribute("href").split("/")[-1]

        # Fecha del tweet
        time_elem = driver.find_element(By.XPATH, '//time')
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


def save_data_to_files(tweet_data_list, json_raw_path="tweets_raw.json", json_clean_path="tweets_clean.json"):
    # Guardar JSON con datos brutos
    with open(json_raw_path, "w", encoding="utf-8") as f:
        json.dump(tweet_data_list, f, ensure_ascii=False, indent=2)
    print(f"Datos brutos guardados en: {json_raw_path}")

    # Procesar con LimpiezaComentarios mejorada
    limpiador = LimpiezaComentarios()
    clean_data = []

    for tweet in tweet_data_list:
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
    print(f"Comentarios limpios guardados en: {json_clean_path}")
