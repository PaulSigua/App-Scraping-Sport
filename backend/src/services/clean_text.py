import re
import unicodedata
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
import nltk
from nltk.corpus import stopwords

nltk.download("stopwords")
DetectorFactory.seed = 0

class CleanText:
    def __init__(self):
        self.stopwords_es = set(stopwords.words("spanish"))

    def limpiar_texto(self, texto, eliminar_numeros=True, quitar_stopwords=False):
        if not texto:
            return ""
        texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8", "ignore")
        texto = texto.lower()
        texto = re.sub(r"http\S+|www\S+|https\S+", "", texto)
        texto = re.sub(r"@\w+|#\w+", "", texto)
        texto = re.sub(r"[^\w\s]", "", texto)
        if eliminar_numeros:
            texto = re.sub(r"\d+", "", texto)
        texto = re.sub(r"\s+", " ", texto).strip()
        if quitar_stopwords:
            texto = " ".join([p for p in texto.split() if p not in self.stopwords_es])
        return texto

    def es_espanol(self, texto):
        try:
            return detect(texto) == "es"
        except LangDetectException:
            return False
