from fastapi import APIRouter, HTTPException
from services.scraping.scraping_x import (
    open_twitter_login,
    go_to_explore,
    search_keyword,
    get_tweet_links,
    open_tweet_and_extract,
    save_data_to_files
)
from services.scraping.scraping_tiktok import ScraperTikTok
from services.driver import get_chrome_driver
import time

router = APIRouter(
    prefix="/scraping",
    tags=["scraping"]
)

@router.post("/x")
def scraping_x(max_posts: int = 3, scrolls_per_post: int = 5, keywork: str = "mundial de clubes"):
    driver = get_chrome_driver()
    all_data = []

    try:
        open_twitter_login(driver)
        go_to_explore(driver)
        search_keyword(driver, keyword=keywork)
        time.sleep(5)

        tweet_links = get_tweet_links(driver, max_posts, extra_scrolls=10)

        for idx, link in enumerate(tweet_links):
            print(f"\n🔍 Procesando tweet {idx + 1}/{max_posts}")
            tweet_data = open_tweet_and_extract(driver, link, scrolls_per_post)
            if tweet_data:
                all_data.append(tweet_data)

    finally:
        driver.quit()
        save_data_to_files(all_data)

    return {
        "status": "ok",
        "tweets_procesados": len(all_data),
        "archivo_json": "tweets_raw.json",
        "archivo_csv": "tweets_clean.csv",
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
