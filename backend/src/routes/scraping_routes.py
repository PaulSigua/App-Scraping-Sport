from fastapi import APIRouter, HTTPException
from services.scraping.scraping_x import (
    get_chrome_driver,
    open_twitter_login,
    go_to_explore,
    search_keyword,
    get_tweet_links,
    open_tweet_and_extract,
    save_all_to_csv
)
import time

router = APIRouter(
    prefix="/scraping",
    tags=["scraping"]
)

@router.post("/x")
def scraping_x(max_posts, scrolls_per_post):
    driver = get_chrome_driver()
    all_data = []
    try:
        open_twitter_login(driver)
        go_to_explore(driver)
        search_keyword(driver, "mundial de clubes")
        time.sleep(5)

        tweet_links = get_tweet_links(driver, max_posts, extra_scrolls=10)

        for idx, link in enumerate(tweet_links):
            print(f"\nProcesando tweet {idx + 1}/{max_posts}")
            tweet_text, comments = open_tweet_and_extract(driver, link, scrolls_per_post)
            if tweet_text:
                all_data.append((tweet_text, comments))

    finally:
        driver.quit()
        save_all_to_csv(all_data)