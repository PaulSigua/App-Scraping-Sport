# scraper_facebook.py
from datetime import datetime
import os
import re
import time
import json
import traceback
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager
from services.clean_text import LimpiezaComentarios

class ScraperFacebook:
    PATH_ = os.getenv("Data_win")

    def __init__(self, palabra_clave: str, max_posts: int):
        load_dotenv()
        self.email = os.getenv("FACEBOOK_EMAIL")
        self.password = os.getenv("FACEBOOK_PASSWORD")
        self.palabra_clave = palabra_clave
        self.max_posts = max_posts
        self.driver = None
        self.resultado = []

    def iniciar_driver(self):
        options = Options()
        options.add_argument("--disable-notifications")
        # options.add_argument("--headless")  # Descomenta si no quieres UI
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def login(self):
        self.driver.get("https://www.facebook.com/login")
        time.sleep(2)
        self.driver.find_element(By.ID, "email").send_keys(self.email)
        self.driver.find_element(By.ID, "pass").send_keys(self.password + Keys.RETURN)
        time.sleep(5)

    def buscar_palabra_clave(self):
        search_input = self.driver.find_element(By.XPATH, '//input[@aria-label="Buscar en Facebook"]')
        search_input.send_keys(self.palabra_clave)
        search_input.send_keys(Keys.RETURN)
        time.sleep(5)
        try:
            publicaciones_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//a[contains(@href, "/search/posts/") and .//span[text()="Publicaciones"]]'))
            )
            publicaciones_btn.click()
            time.sleep(3)
        except:
            pass

    def expandir_publicacion(self):
        for b in self.driver.find_elements(By.XPATH, '//div[@role="button" and text()="Ver más"]'):
            try:
                self.driver.execute_script("arguments[0].click();", b)
                time.sleep(0.5)
            except:
                continue

    def obtener_nombre_cuenta(self):
        try:
            return self.driver.find_element(By.XPATH, '//div[@role="dialog"]//strong/span').text.strip()
        except:
            return "Desconocido"

    def obtener_titulo_publicacion(self):
        posibles = [
            '//div[@data-ad-preview="message"]',
            '//div[@role="dialog"]//div[@dir="auto" and not(@aria-hidden)]'
        ]
        for xpath in posibles:
            try:
                t = self.driver.find_element(By.XPATH, xpath).text.strip()
                if t:
                    return t
            except:
                continue
        return ""

    def expandir_comentarios(self, objetivo):
        prev = 0
        for _ in range(20):
            comentarios = self.driver.find_elements(By.XPATH, '//div[contains(@aria-label, "Comentario de")]')
            actual = len(comentarios)
            if actual >= objetivo or actual == prev:
                break
            prev = actual
            for b in self.driver.find_elements(By.XPATH, '//div[@role="button" and (contains(text(), "Ver más comentarios") or contains(text(), "Ver más respuestas"))]'):
                try:
                    self.driver.execute_script("arguments[0].click();", b)
                except:
                    pass
            time.sleep(1)

    def obtener_comentarios(self):
        resultado = []
        contenedores = self.driver.find_elements(By.XPATH, '//div[contains(@aria-label, "Comentario de")]')
        for c in contenedores:
            try:
                aria = c.get_attribute("aria-label")
                autor = re.search(r"Comentario de (.+?)(?: hace|$)", aria)
                autor = autor.group(1).strip() if autor else "Desconocido"
                texto = c.find_element(By.XPATH, './/div[@dir="auto" and contains(@style,"text-align: start")]').text.strip()
                resultado.append((autor, texto))
            except:
                continue
        return resultado

    def extraer_comentarios(self):
        self.iniciar_driver()
        self.login()
        self.buscar_palabra_clave()

        publicaciones_json = []
        procesadas = 0

        while procesadas < self.max_posts:
            botones = self.driver.find_elements(By.XPATH, '//span[text()="Comentar"]/ancestor::div[@role="button"]')
            if procesadas >= len(botones):
                break
            try:
                self.driver.execute_script("arguments[0].click();", botones[procesadas])
                time.sleep(3)

                try:
                    filtro = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, '//span[contains(text(), "Más pertinentes")]'))
                    )
                    filtro.click()
                    WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "Todos los comentarios")]'))
                    ).click()
                    time.sleep(2)
                except:
                    pass

                try:
                    total = self.driver.find_element(By.XPATH, '//span[contains(text(), "comentario")]').text
                    numero = [int(s) for s in total.split() if s.isdigit()]
                    objetivo = numero[0] if numero else 0
                except:
                    objetivo = 0

                if objetivo == 0:
                    procesadas += 1
                    continue

                self.expandir_publicacion()
                nombre = self.obtener_nombre_cuenta()
                titulo = self.obtener_titulo_publicacion()
                self.expandir_comentarios(objetivo)
                comentarios = self.obtener_comentarios()

                publicaciones_json.append({
                    "CuentaPublicacion": nombre,
                    "TituloPublicacion": titulo,
                    "Comentarios": [{"Usuario": u, "Comentario": c} for u, c in comentarios]
                })

                self.driver.find_element(By.XPATH, '//div[@aria-label="Cerrar" or @aria-label="Cerrar publicación"]').click()
                procesadas += 1
                time.sleep(2)

            except Exception as e:
                print(f"Error: {e}")
                procesadas += 1

        self.resultado = publicaciones_json
        self.driver.quit()

    def guardar_json(self, 
                 json_raw_path=f"{PATH_}/comentarios_facebook_raw.json", 
                 json_clean_path=f"{PATH_}/comentarios_facebook_clean.json"):

        # Guardar estructura cruda (por publicación)
        with open(json_raw_path, "w", encoding="utf-8") as f:
            json.dump(self.resultado, f, ensure_ascii=False, indent=2)
        print(f" Comentarios crudos guardados en: {json_raw_path}")

        # Limpiar y convertir a estructura plana
        limpiador = LimpiezaComentarios()
        clean_data = []

        for publicacion in self.resultado:
            titulo = publicacion.get("TituloPublicacion", "")
            for comentario in publicacion.get("Comentarios", []):
                texto = comentario["Comentario"]
                if not limpiador.es_espanol(texto):
                    continue
                limpio = limpiador.limpiar_texto(
                    texto,
                    eliminar_numeros=True,
                    quitar_stopwords=True,
                    aplicar_lema=True
                )
                if len(limpio.split()) >= 3:
                    clean_data.append({
                        "post_titulo": titulo,
                        "usuario": comentario["Usuario"],
                        "comentario": limpio
                    })

        # Guardar comentarios limpios
        with open(json_clean_path, "w", encoding="utf-8") as f:
            json.dump(clean_data, f, ensure_ascii=False, indent=2)
        print(f" Comentarios limpios guardados en: {json_clean_path}")

        self.driver.quit()

        return {
            "archivo_raw": json_raw_path,
            "archivo_limpio": json_clean_path,
            "total_raw": sum(len(p["Comentarios"]) for p in self.resultado),
            "total_limpio": len(clean_data)
        }
