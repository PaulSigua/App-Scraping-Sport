from fastapi import FastAPI, HTTPException
import uvicorn
from routes import scraping_routes

app = FastAPI(
    title="API Scraping Toxic Social Media"
)

api_prefix = "/api/v1"

app.include_router(scraping_routes.router, prefix=api_prefix)

@app.get('/', description="Default endpoint")
def default_enpoint():
    info = [
        {
            "status": "ok"
        }
    ]
    return info

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=9999)