import time, os, csv
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from services.driver import get_chrome_driver
from services.clean_text import CleanText

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
        EC.element_to_be_clickable((By.XPATH, '//a[@href="/explore" and @role="link"]'))
    ).click()
    print("Sección 'Explorar' lista")

def search_keyword(driver, keyword):
    search_input = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, '//input[@data-testid="SearchBox_Search_Input"]'))
    )
    search_input.clear()
    search_input.send_keys(keyword, Keys.RETURN)
    print(f"Búsqueda de: {keyword}")
    time.sleep(5)

def get_tweet_articles(driver, max_count):
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//article[@role="article"]')))
    articles = driver.find_elements(By.XPATH, '//article[@role="article"]')
    return articles[:max_count]

def get_tweet_links(driver, max_count, extra_scrolls=10):
    # Realizar scrolls para cargar más tweets
    for i in range(extra_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print(f"⬇ Scroll adicional en búsqueda ({i+1}/{extra_scrolls})")
        time.sleep(2.5)

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, '//article[@role="article"]'))
    )

    articles = driver.find_elements(By.XPATH, '//article[@role="article"]')
    tweet_links = []

    for article in articles:
        try:
            link_elem = article.find_element(By.XPATH, './/a[contains(@href, "/status/")]')
            tweet_url = link_elem.get_attribute("href")
            if tweet_url and tweet_url not in tweet_links:
                tweet_links.append(tweet_url)
            if len(tweet_links) >= max_count:
                break
        except:
            continue

    print(f"Enlaces a tweets encontrados: {len(tweet_links)}")
    return tweet_links


def open_tweet_and_extract(driver, tweet_url, scrolls=10, wait_scroll=3):
    try:
        driver.get(tweet_url)
        print(f"Abriendo tweet: {tweet_url}")
        time.sleep(3)

        # Scroll en comentarios
        for i in range(scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print(f"Scroll {i+1}/{scrolls}")
            time.sleep(wait_scroll)

        # Extraer texto y comentarios
        all_texts = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[@data-testid="tweetText"]'))
        )
        tweet_text = all_texts[0].text.strip()
        comments = [t.text.strip() for t in all_texts[1:] if t.text.strip()]
        print(f"Tweet: {tweet_text[:50]}... | Comentarios: {len(comments)}")

        return tweet_text, comments

    except Exception as e:
        print(f"⚠ Error al procesar tweet: {e}")
        return None, []


def save_all_to_csv(data, output_file="comments_output_v2.csv"):
    limpiador = CleanText()

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["tweet_id", "comment"])
        for tweet_text, comments in data:
            for comment in comments:
                limpio = limpiador.limpiar_texto(comment, eliminar_numeros=True, quitar_stopwords=True)
                if len(limpio.split()) >= 3 and limpiador.es_espanol(limpio):
                    writer.writerow([tweet_text, limpio])
    print(f"Archivo guardado: {output_file}")

def main(max_posts, scrolls_per_post):
    driver = get_chrome_driver()
    all_data = []
    try:
        open_twitter_login(driver)
        go_to_explore(driver)
        search_keyword(driver, "mundial de clubes")
        time.sleep(5)

        tweet_links = get_tweet_links(driver, max_posts, extra_scrolls=10)

        for idx, link in enumerate(tweet_links):
            print(f"\nProcesando tweet {idx + 1}/{max_posts}")
            tweet_text, comments = open_tweet_and_extract(driver, link, scrolls_per_post)
            if tweet_text:
                all_data.append((tweet_text, comments))

    finally:
        driver.quit()
        save_all_to_csv(all_data)