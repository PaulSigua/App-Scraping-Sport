from fastapi import APIRouter, HTTPException
from services.scraping.scraping_x import ScraperX
from services.scraping.scraping_tiktok import ScraperTikTok
from services.scraping.scraping_youtube import ScraperYouTube
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.clasification.clasification_comments import clasificar_archivo
import json
import os
from concurrent.futures import ThreadPoolExecutor

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

class ScrapingTodoRequest(BaseModel):
    palabra_clave: str
    max_posts_x: int
    max_videos_tiktok: int
    max_videos_youtube: int


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

@router.post("/todo")
def scraping_todo(data: ScrapingTodoRequest):
    resultados = {}

    def ejecutar_x():
        try:
            scraper = ScraperX(palabra_clave=data.palabra_clave, max_posts=data.max_posts_x)
            scraper.open_twitter_login()
            scraper.buscar_tweets()
            res = scraper.guardar_json()
            return ("x", {
                "status": "ok",
                "tweets_procesados": res["total_raw"],
                "tweets_filtrados": res["total_limpio"],
                "archivo_raw": res["archivo_raw"],
                "archivo_limpio": res["archivo_limpio"]
            })
        except Exception as e:
            return ("x", {"status": "error", "error": str(e)})

    def ejecutar_tiktok():
        try:
            scraper = ScraperTikTok(palabra_clave=data.palabra_clave, max_videos=data.max_videos_tiktok)
            scraper.buscar_videos()
            scraper.extraer_comentarios()
            path = scraper.guardar_json()
            return ("tiktok", {
                "status": "ok",
                "total_comentarios": len(scraper.comentarios_data),
                "archivo_json": path
            })
        except Exception as e:
            return ("tiktok", {"status": "error", "error": str(e)})

    def ejecutar_youtube():
        try:
            scraper = ScraperYouTube(palabra_clave=data.palabra_clave, max_videos=data.max_videos_youtube)
            scraper.buscar_videos()
            res = scraper.guardar_json()
            return ("youtube", {
                "status": "ok",
                "comentarios_totales": res["total_raw"],
                "comentarios_limpios": res["total_limpio"],
                "archivo_raw": res["archivo_raw"],
                "archivo_limpio": res["archivo_limpio"]
            })
        except Exception as e:
            return ("youtube", {"status": "error", "error": str(e)})

    # Ejecutamos los 3 scrapers en paralelo
    with ThreadPoolExecutor(max_workers=3) as executor:
        tareas = [
            executor.submit(ejecutar_x),
            executor.submit(ejecutar_tiktok),
            executor.submit(ejecutar_youtube)
        ]

        for future in tareas:
            plataforma, resultado = future.result()
            resultados[plataforma] = resultado

    return JSONResponse(content=resultados)

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
    data_clasificados = leer_json(f"{PATH_}/tweets_class.json")

    # Crear set de claves válidas desde clean: (usuario, tweet_id)
    clean_keys = set((tweet["usuario"], tweet["tweet_id"]) for tweet in clean_data)

    # Clasificados dict: (usuario, video_url) → "insulto", "otro", etc.
    clasificados_dict = {
        (c["usuario"], c["video_url"]): c["clasificacion"]
        for c in data_clasificados
    }

    comentarios = []
    for tweet in data:
        tweet_url = tweet["tweet_url"]
        for c in tweet.get("comments", []):
            clave = (c["usuario"], tweet_url)
            if clave in clean_keys:
                comentarios.append({
                    "usuario": c["usuario"],
                    "comentario": c["texto"],
                    "plataforma": "x",
                    "clasificacion": clasificados_dict.get(clave, "sin clasificar")
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

# Clasificacion de comentariosfrom fastapi import APIRouter
@router.get("/clasificar/todo")
def clasificar_todo():
    resultados = []

    plataformas = [
        {
            "nombre": "tiktok",
            "path_clean": os.path.join(PATH_, "comentarios_tiktok_clean.json"),
            "output_path": os.path.join(PATH_, "comentarios_tiktok_class.json")
        },
        {
            "nombre": "x",
            "path_clean": os.path.join(PATH_, "tweets_clean.json"),
            "output_path": os.path.join(PATH_, "tweets_class.json")
        },
        {
            "nombre": "youtube",
            "path_clean": os.path.join(PATH_, "youtube_clean.json"),
            "output_path": os.path.join(PATH_, "youtube_class.json")
        }
    ]

    for plataforma in plataformas:
        clasificados = clasificar_archivo(
            plataforma["path_clean"],
            plataforma["nombre"],
            plataforma["output_path"]
        )
        resultados.append({
            "plataforma": plataforma["nombre"],
            "comentarios": clasificados
        })

    return JSONResponse(content=resultados)