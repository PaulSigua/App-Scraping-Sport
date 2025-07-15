import time, json, re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from services.driver import get_chrome_driver
from services.clean_text import LimpiezaComentarios
import os

PATH_ = os.getenv("Data_win")

class ScraperYouTube:
    def __init__(self, max_videos=None, palabra_clave=None, scrolls=10):
        self.palabra_clave = palabra_clave
        self.max_videos = max_videos
        self.scrolls = scrolls
        self.driver = get_chrome_driver()
        self.comentarios_data = []

    def buscar_videos(self):
        print(f"🔍 Buscando: {self.palabra_clave}")
        self.driver.get("https://www.youtube.com/")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "search_query"))
        )
        input_box = self.driver.find_element(By.NAME, "search_query")
        input_box.clear()
        input_box.send_keys(self.palabra_clave, Keys.ENTER)
        time.sleep(3)

        videos = self.driver.find_elements(By.XPATH, '//a[@id="video-title"]')
        video_urls = []
        for v in videos:
            href = v.get_attribute("href")
            if href and "watch?v=" in href:
                video_urls.append(href)
            if len(video_urls) >= self.max_videos:
                break

        for video_url in video_urls:
            self.extraer_comentarios(video_url)

    def extraer_comentarios(self, video_url):
        print(f"🎥 Extrayendo de: {video_url}")
        self.driver.get(video_url)
        time.sleep(4)
        
        # Scroll para cargar comentarios
        for i in range(self.scrolls):
            self.driver.execute_script("window.scrollBy(0, 700);")
            time.sleep(2)

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#comments'))
            )
        except:
            print("Comentarios deshabilitados.")
            return

        threads = self.driver.find_elements(By.CSS_SELECTOR, 'ytd-comment-thread-renderer')
        for thread in threads:
            try:
                text = thread.find_element(By.ID, "content-text").text.strip()
                user = thread.find_element(By.ID, "author-text").text.strip()
                if re.search(r"\b\w+\b", text):
                    self.comentarios_data.append({
                        "video_url": video_url,  
                        "usuario": user,
                        "comentario": text
                    })
            except:
                continue

    def guardar_json(self, json_raw_path=f"{PATH_}/youtube_raw.json", json_clean_path=f"{PATH_}/youtube_clean.json"):
        with open(json_raw_path, "w", encoding="utf-8") as f:
            json.dump(self.comentarios_data, f, ensure_ascii=False, indent=2)
        print(f"Comentarios crudos guardados en: {json_raw_path}")

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
        print(f"Comentarios limpios guardados en: {json_clean_path}")

        self.driver.quit()

        return {
            "archivo_raw": json_raw_path,
            "archivo_limpio": json_clean_path,
            "total_raw": len(self.comentarios_data),
            "total_limpio": len(clean_data)
        }
