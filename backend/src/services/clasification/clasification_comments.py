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

def clasificar_comentario_simple(texto: str) -> str:
    prompt = f"""
    Clasifica el siguiente comentario en una sola categoría: Acoso, Racismo, Insulto u Otro.
    Responde únicamente con el nombre de la categoría más adecuada, sin explicaciones ni puntuaciones.

    Comentario: "{texto}"
    """

    response = client.chat.completions.create(
        model="o4-mini",
        messages=[
            {"role": "system", "content": "Eres un clasificador de comentarios deportivos tóxicos."},
            {"role": "user", "content": prompt}
        ],
    )

    texto_respuesta = response.choices[0].message.content.strip().lower()

    # Validación
    categorias_validas = {"acoso", "racismo", "insulto", "otro"}
    if texto_respuesta in categorias_validas:
        return texto_respuesta
    else:
        return "otro"



def clasificar_archivo(path_clean: str, plataforma: str, output_path: str):
    with open(path_clean, "r", encoding="utf-8") as f:
        data = json.load(f)

    resultado = []
    for c in data:
        comentario = c.get("comentario")
        if not comentario:
            continue
        clasificacion = clasificar_comentario_simple(comentario)
        resultado.append({
            "usuario": c.get("usuario"),
            "comentario": comentario,
            "video_url": c.get("video_url") or c.get("tweet_id") or c.get("video_url", "no-url"),
            "plataforma": plataforma,
            "clasificacion": clasificacion
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    return resultado
