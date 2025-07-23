import json
import re
import unicodedata
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
import spacy
import nltk
from nltk.corpus import stopwords

nltk.download("stopwords")
DetectorFactory.seed = 0
nlp = spacy.load("es_core_news_sm")

class LimpiezaComentarios:
    def __init__(self):
        self.stopwords_es = set(stopwords.words("spanish"))

    def es_espanol(self, texto):
        try:
            return detect(texto) == "es"
        except LangDetectException:
            return False

    def limpiar_texto(self, texto, eliminar_numeros=True, quitar_stopwords=True, aplicar_lema=True):
        texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8", "ignore")
        texto = texto.lower()
        texto = re.sub(r"http\S+|www\S+|https\S+", "", texto)
        texto = re.sub(r"@\w+|#\w+", "", texto)
        texto = re.sub(r"[^\w\s]", "", texto)
        if eliminar_numeros:
            texto = re.sub(r"\d+", "", texto)
        texto = re.sub(r"\s+", " ", texto).strip()

        tokens = texto.split()

        if quitar_stopwords:
            tokens = [p for p in tokens if p not in self.stopwords_es]

        if aplicar_lema:
            doc = nlp(" ".join(tokens))
            tokens = [token.lemma_ for token in doc]

        return " ".join(tokens)
