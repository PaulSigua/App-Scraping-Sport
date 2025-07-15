from fastapi import APIRouter, HTTPException
from services.scraping.scraping_x import ScraperX
from services.scraping.scraping_tiktok import ScraperTikTok
from services.scraping.scraping_youtube import ScraperYouTube
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import os

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
PATH_ = os.getenv("Data_win")

router = APIRouter(
    prefix="/scraping",
    tags=["scraping"]
)

class ScrapingXRequest(BaseModel):
    palabra_clave: str
    max_posts: int
    
class ScrapingTikTokRequest(BaseModel):
    palabra_clave: str
    max_videos: int

class ScrapingYouTubeRequest(BaseModel):
    max_videos: int
    palabra_clave: str  


@router.post("/x")
def scraping_x(data: ScrapingXRequest):
    scraper = ScraperX(palabra_clave=data.palabra_clave, max_posts=data.max_posts)
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
def scraping_tiktok(data: ScrapingTikTokRequest):
    scraper = ScraperTikTok(palabra_clave=data.palabra_clave, max_videos=data.max_videos)
    scraper.buscar_videos()
    scraper.extraer_comentarios()
    json_path = scraper.guardar_json()
    return {
        "status": "ok",
        "total_comentarios": len(scraper.comentarios_data),
        "archivo_json": json_path
    }

@router.post("/youtube")
def scraping_youtube(data: ScrapingYouTubeRequest):
    try:
        scraper = ScraperYouTube(palabra_clave=data.palabra_clave, max_videos=data.max_videos)
        scraper.buscar_videos()
        resultado = scraper.guardar_json()

        return {
            "status": "ok",
            "comentarios_totales": resultado["total_raw"],
            "comentarios_limpios": resultado["total_limpio"],
            "archivo_raw": resultado["archivo_raw"],
            "archivo_limpio": resultado["archivo_limpio"]
        }
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la solicitud: {str(e)}")

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
    data = leer_json(f"{PATH_}/tweets_raw.json")
    clean_data = leer_json(f"{PATH_}/tweets_clean.json")

    # Crear set de claves válidas desde clean: (usuario, tweet_text)
    clean_keys = set((tweet["comment_user"], tweet["tweet_id"]) for tweet in clean_data)

    comentarios = []
    for tweet in data:
        tweet_text = tweet["tweet_url"]
        for c in tweet.get("comments", []):
            clave = (c["usuario"], tweet_text)
            if clave in clean_keys:
                comentarios.append({
                    "usuario": c["usuario"],
                    "comentario": c["texto"],
                    "plataforma": "x"
                })

    return JSONResponse(content=comentarios)



@router.get("/comentarios/tiktok")
def get_comentarios_tiktok():
    # Leer ambos archivos JSON
    raw_data = leer_json(f"{PATH_}/comentarios_tiktok_raw.json")
    clean_data = leer_json(f"{PATH_}/comentarios_tiktok_clean.json")

    clean_keys = set((comentario["usuario"], comentario["video_url"]) for comentario in clean_data)

    comentarios_validados = []
    for comentario in raw_data:
        clave = (comentario["usuario"], comentario["video_url"])
        if clave in clean_keys:
            comentarios_validados.append({
                "usuario": comentario["usuario"],
                "comentario": comentario["comentario"],
                "plataforma": "tiktok"
            })

    return JSONResponse(content=comentarios_validados)



@router.get("/comentarios/youtube")
def get_comentarios_youtube():
    data = leer_json(f"{PATH_}/youtube_raw.json")
    clean_data = leer_json(f"{PATH_}/youtube_clean.json")

    # Crear set de claves válidas desde clean: (video_url, usuario)
    clean_keys = set((c["video_url"], c["usuario"]) for c in clean_data)

    comentarios = []
    for c in data:
        clave = (c["video_url"], c["usuario"])  # ahora sí coinciden
        if clave in clean_keys:
            comentarios.append({
                "usuario": c["usuario"],
                "comentario": c["comentario"],  # Comentario original del raw
                "plataforma": "youtube"
            })

    return JSONResponse(content=comentarios)


