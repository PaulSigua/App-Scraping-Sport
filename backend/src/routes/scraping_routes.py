from fastapi import APIRouter, HTTPException

from services.scraping.scraping_x import ScraperX
from services.scraping.scraping_tiktok import ScraperTikTok
from services.scraping.scraping_youtube import ScraperYouTube
from services.scraping.scraping_facebook import ScraperFacebook

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

class ScrapingFacebookRequest(BaseModel):
    palabra_clave: str
    max_posts: int

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


@router.post("/facebook")
def scraping_facebook(data: ScrapingFacebookRequest):
    try:
        scraper = ScraperFacebook(palabra_clave=data.palabra_clave, max_posts=data.max_posts)
        scraper.extraer_comentarios()
        resultado = scraper.guardar_json()
        return {
            "status": "ok",
            "comentarios_totales": resultado["total_raw"],
            "comentarios_limpios": resultado["total_limpio"],
            "archivo_raw": resultado["archivo_raw"],
            "archivo_limpio": resultado["archivo_limpio"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar Facebook: {str(e)}")

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

    def ejecutar_facebook():
        try:
            scraper = ScraperFacebook(palabra_clave=data.palabra_clave, max_posts=data.max_posts_x)
            scraper.extraer_comentarios()
            res = scraper.guardar_json()
            return ("facebook", {
                "status": "ok",
                "comentarios_totales": res["total_raw"],
                "comentarios_limpios": res["total_limpio"],
                "archivo_raw": res["archivo_raw"],
                "archivo_limpio": res["archivo_limpio"]
            })
        except Exception as e:
            return ("facebook", {"status": "error", "error": str(e)})


    # Ejecutamos los 3 scrapers en paralelo
    with ThreadPoolExecutor(max_workers=4) as executor:
        tareas = [
            executor.submit(ejecutar_x),
            executor.submit(ejecutar_tiktok),
            executor.submit(ejecutar_youtube),
            executor.submit(ejecutar_facebook)
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
    

def cargar_clasificados_dataset(plataforma: str) -> dict:
    dataset = leer_json(os.path.join(PATH_, "dataset.json"))
    if plataforma == "facebook":
        return {
            c["usuario"]: c
            for c in dataset
            if c["plataforma"] == "facebook"
        }
    else:
        return {
            (c["usuario"], c["video_url"]): c
            for c in dataset
            if c["plataforma"] == plataforma
        }


@router.get("/comentarios/facebook")
def get_comentarios_facebook():
    raw_data = leer_json(f"{PATH_}/comentarios_facebook_raw.json")
    clasificados = cargar_clasificados_dataset("facebook")

    comentarios = []
    for publicacion in raw_data:
        titulo = publicacion.get("TituloPublicacion", "")
        for comentario in publicacion.get("Comentarios", []):
            usuario = comentario["Usuario"]
            clasif = clasificados.get(usuario)
            if clasif:
                comentarios.append({
                    "usuario": usuario,
                    "comentario": comentario["Comentario"],
                    "video_url": titulo,
                    "plataforma": "facebook",
                    "clasificacion": clasif.get("clasificacion", "otro")
                })

    return JSONResponse(content=comentarios)




@router.get("/comentarios/x")
def get_comentarios_x():
    raw_data = leer_json(f"{PATH_}/tweets_raw.json")
    clasificados = cargar_clasificados_dataset("x")

    comentarios = []
    for tweet in raw_data:
        tweet_url = tweet.get("tweet_url", "")
        for c in tweet.get("comments", []):
            clave = (c["usuario"], tweet_url)
            clasif = clasificados.get(clave)
            if clasif:
                comentarios.append({
                    "usuario": c["usuario"],
                    "comentario": c["texto"],
                    "video_url": tweet_url,
                    "plataforma": "x",
                    "clasificacion": clasif.get("clasificacion", "otro")
                })

    return JSONResponse(content=comentarios)





@router.get("/comentarios/tiktok")
def get_comentarios_tiktok():
    raw_data = leer_json(f"{PATH_}/comentarios_tiktok_raw.json")
    clasificados = cargar_clasificados_dataset("tiktok")

    comentarios = []
    for comentario in raw_data:
        clave = (comentario["usuario"], comentario["video_url"])
        clasif = clasificados.get(clave)
        if clasif:
            comentarios.append({
                "usuario": comentario["usuario"],
                "comentario": comentario["comentario"],
                "video_url": comentario["video_url"],
                "plataforma": "tiktok",
                "clasificacion": clasif.get("clasificacion", "otro")
            })

    return JSONResponse(content=comentarios)


@router.get("/comentarios/youtube")
def get_comentarios_youtube():
    raw_data = leer_json(f"{PATH_}/youtube_raw.json")
    clasificados = cargar_clasificados_dataset("youtube")

    comentarios = []
    for c in raw_data:
        clave = (c["usuario"], c["video_url"])
        clasif = clasificados.get(clave)
        if clasif:
            comentarios.append({
                "usuario": c["usuario"],
                "comentario": c["comentario"],
                "video_url": c["video_url"],
                "plataforma": "youtube",
                "clasificacion": clasif.get("clasificacion", "otro")
            })

    return JSONResponse(content=comentarios)



# Clasificacion de comentariosfrom fastapi import APIRouter
@router.get("/clasificar/todo")
def clasificar_todo():
    dataset = []

    plataformas = [
        {
            "nombre": "tiktok",
            "path_clean": os.path.join(PATH_, "comentarios_tiktok_clean.json"),
        },
        {
            "nombre": "x",
            "path_clean": os.path.join(PATH_, "tweets_clean.json"),
        },
        {
            "nombre": "youtube",
            "path_clean": os.path.join(PATH_, "youtube_clean.json"),
        },
        {
            "nombre": "facebook",
            "path_clean": os.path.join(PATH_, "comentarios_facebook_clean.json"),
        }
    ]

    for plataforma in plataformas:
        clasificados = clasificar_archivo(
            plataforma["path_clean"],
            plataforma["nombre"]
        )

        dataset.extend(clasificados)

    # Guardar todo el dataset unificado
    dataset_path = os.path.join(PATH_, "dataset.json")
    with open(dataset_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    return JSONResponse(content={
        "mensaje": "Clasificación completada correctamente.",
        "comentarios_totales": len(dataset),
        "archivo": "dataset.json"
    })



@router.get("/comentarios/obtenerjson")
def get_dataset():
    dataset = leer_json(os.path.join(PATH_, "dataset.json"))

    # Cargar datos crudos por plataforma
    raw_tiktok = leer_json(os.path.join(PATH_, "comentarios_tiktok_raw.json"))
    raw_x = leer_json(os.path.join(PATH_, "tweets_raw.json"))
    raw_youtube = leer_json(os.path.join(PATH_, "youtube_raw.json"))
    raw_facebook = leer_json(os.path.join(PATH_, "comentarios_facebook_raw.json"))

    # Diccionarios para acceso rápido
    dic_tiktok = {(c["usuario"], c["video_url"]): c["comentario"] for c in raw_tiktok}
    dic_youtube = {(c["usuario"], c["video_url"]): c["comentario"] for c in raw_youtube}
    dic_x = {
        (c["usuario"], tweet["tweet_url"]): c["texto"]
        for tweet in raw_x
        for c in tweet.get("comments", [])
    }
    dic_facebook = {
        c["Usuario"]: c["Comentario"]
        for publicacion in raw_facebook
        for c in publicacion.get("Comentarios", [])
    }

    resultado = []
    for comentario in dataset:
        plataforma = comentario["plataforma"]
        usuario = comentario["usuario"]
        video_url = comentario.get("video_url", "")

        if plataforma == "facebook":
            texto_crudo = dic_facebook.get(usuario)
        elif plataforma == "tiktok":
            texto_crudo = dic_tiktok.get((usuario, video_url))
        elif plataforma == "youtube":
            texto_crudo = dic_youtube.get((usuario, video_url))
        elif plataforma == "x":
            texto_crudo = dic_x.get((usuario, video_url))
        else:
            texto_crudo = None

        if texto_crudo:
            resultado.append({
                "usuario": usuario,
                "comentario": texto_crudo,
                "video_url": video_url,
                "plataforma": plataforma,
                "clasificacion": comentario.get("clasificacion", "otro"),
                "probabilidad_toxicidad": comentario.get("probabilidad_toxicidad", 0.0),
                "nivel_toxicidad": comentario.get("nivel_toxicidad", "bajo"),
                "palabras_clave": comentario.get("palabras_clave", [])
            })

    return JSONResponse(content=resultado)