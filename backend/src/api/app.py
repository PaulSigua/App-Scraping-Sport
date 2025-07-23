import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from routes import scraping_routes
import uvicorn

app = FastAPI(
    title="API Scraping Toxic Social Media"
)


# CORS middleware to allow requests from the frontend

origins = [
    "http://localhost:4200",
    # "*"
]

# 1) CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = "/api/v1"

app.include_router(scraping_routes.router, prefix=api_prefix)

@app.get('/', description="Default endpoint")
def default_enpoint():
    try:
        info = [
            {
                "status": "ok",
                "API": "Levantada"
            }
        ]
        return info
    except HTTPException as e:
        return { "error": {e}}

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=9999)