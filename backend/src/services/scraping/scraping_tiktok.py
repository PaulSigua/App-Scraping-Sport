import time, json, re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from services.driver import get_chrome_driver
from services.clean_text import LimpiezaComentarios

class ScraperTikTok:
    def __init__(self, palabra_clave=None, max_videos=None):
        self.palabra_clave = palabra_clave
        self.max_videos = max_videos
        self.comentarios_data = []
        self.urls = []
        self.driver = get_chrome_driver()

    def buscar_videos(self):
        self.driver.get("https://www.tiktok.com/")
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-e2e="nav-search"]'))
        )

        btn_lupa = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-e2e="nav-search"]'))
        )
        btn_lupa.click()
        time.sleep(2)

        inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[data-e2e="search-user-input"]')
        input_search = next((i for i in inputs if i.is_displayed() and i.is_enabled()), None)
        if not input_search:
            self.driver.quit()
            raise Exception("No se encontró el input de búsqueda.")

        input_search.click()
        input_search.clear()
        input_search.send_keys(self.palabra_clave)
        input_search.send_keys(Keys.ENTER)
        time.sleep(4)

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//a[contains(@href, "/video/")]'))
        )

        videos = self.driver.find_elements(By.XPATH, '//a[contains(@href, "/video/")]')
        for v in videos:
            href = v.get_attribute("href")
            if href and href not in self.urls:
                self.urls.append(href)
            if len(self.urls) >= self.max_videos:
                break

    def extraer_comentarios(self):
        for url in self.urls:
            print(f"🔗 Extrayendo de: {url}")
            self.driver.get(url)
            time.sleep(3)

            # Intentar pausar el video
            try:
                pausa_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.css-q1bwae-DivPlayIconContainer'))
                )
                pausa_btn.click()
                print("⏸ Video pausado")
                time.sleep(1)
            except Exception as e:
                print(f"⚠️ No se pudo pausar el video: {e}")

            last_count = 0
            same_count_retries = 0
            max_retries = 2
            max_scrolls = 10
            scrolls = 0

            while same_count_retries < max_retries and scrolls < max_scrolls:
                self.driver.execute_script("window.scrollBy(0, 700)")
                time.sleep(4)

                if "/video/" not in self.driver.current_url:
                    print("🔁 Saliste del video, recargando...")
                    self.driver.get(url)
                    time.sleep(10)
                    last_count = 0
                    same_count_retries = 0
                    continue

                items = self.driver.find_elements(By.CSS_SELECTOR, 'div[class*="DivCommentContentWrapper"]')
                current_count = len(items)
                print(f"💬 Comentarios visibles: {current_count}")

                if current_count == last_count:
                    same_count_retries += 1
                else:
                    same_count_retries = 0
                    last_count = current_count

                scrolls += 1

            print(f"✅ Scroll finalizado. Total detectados: {last_count}")

            try:
                WebDriverWait(self.driver, 12).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="DivCommentContentWrapper"]'))
                )
                items = self.driver.find_elements(By.CSS_SELECTOR, 'div[class*="DivCommentContentWrapper"]')
            except:
                print("⚠️ No se encontraron comentarios después del scroll.")
                continue

            for item in items:
                try:
                    usuario_elem = item.find_element(By.CSS_SELECTOR, 'a[href*="/@"]')
                    comentario_elem = item.find_element(By.CSS_SELECTOR, 'span[data-e2e^="comment-level"] p')
                    usuario = usuario_elem.text.strip()
                    comentario = comentario_elem.text.strip()
                    if re.search(r"\b\w+\b", comentario):
                        self.comentarios_data.append({
                            "video_url": url,
                            "usuario": usuario,
                            "comentario": comentario
                        })
                except:
                    continue

    def guardar_json(self, 
                     json_raw_path="src/data/comentarios_tiktok_raw.json", 
                     json_clean_path="src/data/comentarios_tiktok_clean.json"):
        # Guardar comentarios originales
        with open(json_raw_path, "w", encoding="utf-8") as f:
            json.dump(self.comentarios_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Comentarios crudos guardados en: {json_raw_path}")

        # Limpiar y guardar comentarios procesados
        limpiador = LimpiezaComentarios()
        clean_data = []

        for item in self.comentarios_data:
            if not limpiador.es_espanol(item["comentario"]):
                continue
            limpio = limpiador.limpiar_texto(
                item["comentario"],
                eliminar_numeros=True,
                quitar_stopwords=True,
                aplicar_lema=True
            )
            if len(limpio.split()) >= 3:
                clean_data.append({
                    "video_url": item["video_url"],
                    "usuario": item["usuario"],
                    "comentario": limpio
                })

        with open(json_clean_path, "w", encoding="utf-8") as f:
            json.dump(clean_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Comentarios limpios guardados en: {json_clean_path}")
        self.driver.quit()

        return {
            "archivo_raw": json_raw_path,
            "archivo_limpio": json_clean_path,
            "total_raw": len(self.comentarios_data),
            "total_limpio": len(clean_data)
        }