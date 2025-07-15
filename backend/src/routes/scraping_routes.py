from fastapi import APIRouter, HTTPException
from services.scraping.scraping_x import ScraperX
from services.scraping.scraping_tiktok import ScraperTikTok
from services.scraping.scraping_youtube import ScraperYouTube
from fastapi.responses import JSONResponse
import json
import os

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
router = APIRouter(
    prefix="/scraping",
    tags=["scraping"]
)

@router.post("/x")
def scraping_x(max_posts: int = 3, palabra_clave: str = "mundial de clubes"):
    scraper = ScraperX(palabra_clave=palabra_clave, max_posts=max_posts)
    scraper.open_twitter_login()
    scraper.buscar_tweets()
    resultado = scraper.guardar_json()

    return {
        "status": "ok",
        "tweets_procesados": resultado["total_raw"],
        "tweets_filtrados": resultado["total_limpio"],
        "archivo_raw": resultado["archivo_raw"],
        "archivo_limpio": resultado["archivo_limpio"]
    }

@router.post("/tiktok")
def scraping_tiktok(max_videos: int = 5, palabra_clave: str = "mundial de clubes"):
    scraper = ScraperTikTok(palabra_clave=palabra_clave, max_videos=max_videos)
    scraper.buscar_videos()
    scraper.extraer_comentarios()
    json_path = scraper.guardar_json()
    return {
        "status": "ok",
        "total_comentarios": len(scraper.comentarios_data),
        "archivo_json": json_path
    }

@router.post("/youtube")
def scraping_youtube(max_videos: int = 5, palabra_clave: str = "mundial de clubes"):
    scraper = ScraperYouTube(palabra_clave=palabra_clave, max_videos=max_videos)
    scraper.buscar_videos()
    resultado = scraper.guardar_json()

    return {
        "status": "ok",
        "videos_procesados": max_videos,
        "comentarios_totales": resultado["total_raw"],
        "comentarios_limpios": resultado["total_limpio"],
        "archivo_raw": resultado["archivo_raw"],
        "archivo_limpio": resultado["archivo_limpio"]
    }

# Falta Facebook

##

## 


def leer_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        raise HTTPException(status_code=404, detail="Archivo no encontrado o inválido")


@router.get("/comentarios/x")
def get_comentarios_x():
    data = leer_json(f"{DATA_DIR}/tweets_raw.json")
    comentarios = []
    for tweet in data:
        for c in tweet.get("comments", []):
            comentarios.append({
                "usuario": c["usuario"],
                "comentario": c["texto"],
                "plataforma": "x"
            })
    return JSONResponse(content=comentarios)


@router.get("/comentarios/tiktok")
def get_comentarios_tiktok():
    data = leer_json(f"{DATA_DIR}/comentarios_tiktok_raw.json")
    comentarios = []
    for c in data:
        comentarios.append({
            "usuario": c["usuario"],
            "comentario": c["comentario"],
            "plataforma": "tiktok"
        })
    return JSONResponse(content=comentarios)


@router.get("/comentarios/youtube")
def get_comentarios_youtube():
    data = leer_json(f"{DATA_DIR}/youtube_raw.json")
    comentarios = []
    for c in data:
        comentarios.append({
            "usuario": c["usuario"],
            "comentario": c["comentario"],
            "plataforma": "youtube"
        })
    return JSONResponse(content=comentarios)
