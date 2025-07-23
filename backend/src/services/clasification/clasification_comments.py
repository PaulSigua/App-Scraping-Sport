import os
import openai
import json
import re
from typing import List, Dict

openai.api_key = os.getenv("OPENAI_API_KEY")

import os
import json
import re
from typing import Dict
from openai import OpenAI

# Crear cliente (nuevo estilo del SDK)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def clasificar_comentario_completo(texto: str) -> Dict:
    prompt = f"""
Eres un sistema experto en detección de toxicidad en comentarios deportivos.

Analiza el siguiente comentario y responde únicamente en formato JSON con la siguiente estructura:

{{
  "clasificacion": "acoso | racismo | insulto | spam | sarcasmo | neutral",
  "probabilidad_toxicidad": número entre 0 y 1 (por ejemplo: 0.78),
  "nivel_toxicidad": "alto | medio | bajo",
  "palabras_clave": ["palabra1", "palabra2", ...]
}}

Comentario: "{texto}"

Recuerda: No incluyas explicaciones, solo el JSON.
"""

    response = client.chat.completions.create(
        model="o4-mini",  # Puedes usar gpt-3.5-turbo si no tienes acceso a 4o
        messages=[
            {"role": "system", "content": "Eres un asistente de moderación de comentarios deportivos."},
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content.strip()

    # Asegurar que la respuesta es JSON válida
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print(f"Error de parsing en respuesta: {content}")
        return {
            "clasificacion": "otro",
            "probabilidad_toxicidad": 0.0,
            "nivel_toxicidad": "bajo",
            "palabras_clave": []
        }


def clasificar_archivo(path_clean: str, plataforma: str):
    with open(path_clean, "r", encoding="utf-8") as f:
        data = json.load(f)

    resultado = []
    for c in data:
        comentario = c.get("comentario")
        if not comentario:
            continue

        analisis = clasificar_comentario_completo(comentario)

        resultado.append({
            "usuario": c.get("usuario", ""),
            "comentario": comentario,
            "video_url": c.get("video_url") or c.get("tweet_id", ""),
            "plataforma": plataforma,
            "clasificacion": analisis.get("clasificacion", "otro"),
            "probabilidad_toxicidad": analisis.get("probabilidad_toxicidad", 0.0),
            "nivel_toxicidad": analisis.get("nivel_toxicidad", "bajo"),
            "palabras_clave": analisis.get("palabras_clave", [])
        })

    return resultado

