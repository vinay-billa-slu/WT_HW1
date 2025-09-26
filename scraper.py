import json
import argparse
import time
import random
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.yelp.com/biz/mia-bella-restaurant-cleveland"

def slow_scroll(page, selector):
    try:
        element = page.locator(selector)
        page.evaluate("""
            (element) => {
                element.scrollIntoView({behavior: 'smooth', block: 'center'});
            }
        """, element)
        page.wait_for_timeout(random.randint(1000, 3000))
    except:
        pass

def fetch_html(url, playwright, headless=True, retries=3):
    for attempt in range(1, retries + 1):
        try:
            browser = playwright.chromium.launch(headless=headless)
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/140.0.0.0 Safari/537.36"
            )
            page.goto(url, timeout=60000)
            slow_scroll(page, ".y-css-15jz5c7")  # scroll to reviews section
            page.wait_for_timeout(random.randint(2000, 4000))  # extra wait
            html = page.content()
            browser.close()
            return html
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            time.sleep(random.uniform(5, 10))
            if attempt == retries:
                print(f"Failed to fetch {url} after {retries} attempts.")
                return None

def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")

    # Business info
    business_info = {
        "name": soup.select_one(".y-css-olzveb").get_text(strip=True) if soup.select_one(".y-css-olzveb") else "",
        "category": soup.select_one(".y-css-1cafv3i").get_text(strip=True) if soup.select_one(".y-css-1cafv3i") else "",
        "city_region": soup.select_one(".y-css-69058c").get_text(strip=True) if soup.select_one(".y-css-69058c") else "",
        "about_business": soup.select_one(".y-css-1mwo47a").get_text(strip=True) if soup.select_one(".y-css-1mwo47a") else "",
        "vibes": [span.get_text(strip=True) for span in soup.select("span.y-css-1541nhh")],
        "overall_rating": soup.select_one(".y-css-1ms5w5p").get_text(strip=True) if soup.select_one(".y-css-1ms5w5p") else "",
        "total_reviews": soup.select_one(".y-css-1x1e1r2").get_text(strip=True) if soup.select_one(".y-css-1x1e1r2") else ""
    }

    reviews = []
    review_items = soup.select("ul.list__09f24__ynIEd li.y-css-1sqelp2")

    for item in review_items:
        reviewer = item.select_one("a.y-css-1x1e1r2")
        if not reviewer or not reviewer.get_text(strip=True):
            continue

        star = item.select_one("div.y-css-dnttlc")
        date = item.select_one("span.y-css-1vi7y4e")
        text = item.select_one("span.raw__09f24__T4Ezm")

        star_value = ""
        if star and star.has_attr("aria-label"):
            star_value = star["aria-label"].split()[0]

        review_data = {
            "reviewer_handle": reviewer.get_text(strip=True),
            "star_rating": star_value,
            "date": date.get_text(strip=True) if date else "",
            "review_text": text.get_text(strip=True) if text else "",
            "business_name": business_info["name"],
            "category": business_info["category"],
            "city_region": business_info["city_region"],
            "about_business": business_info["about_business"],
            "vibes": business_info["vibes"],
            "overall_rating": business_info["overall_rating"],
            "total_reviews": business_info["total_reviews"]
        }
        reviews.append(review_data)

    return business_info, reviews

def scrape(pages=3, delay_range=(3, 10), headless=True):
    all_reviews = []
    business_info = None

    with sync_playwright() as p:
        for i in range(pages):
            start = i * 10
            url = BASE_URL if i == 0 else f"{BASE_URL}?start={start}"
            print(f"Scraping page {i+1}: {url}")

            html = fetch_html(url, p, headless=headless)
            if not html:
                break

            biz_info, reviews = parse_page(html)
            if biz_info and not business_info:
                business_info = biz_info  # keep first page info

            if not reviews:
                print(f"No reviews found on page {i+1}. Stopping.")
                break

            all_reviews.extend(reviews)
            sleep_time = 60 + random.uniform(*delay_range)
            print(f"Sleeping {sleep_time:.2f}s before next page...")
            time.sleep(sleep_time)

    print(f"Scraped total {len(all_reviews)} reviews")
    return business_info, all_reviews

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Yelp Multi-Page Review Scraper (Playwright)")
    parser.add_argument("--pages", type=int, default=3, help="Number of pages to scrape (default: 3)")
    parser.add_argument("--output", type=str, default="data.json", help="Output file name")
    parser.add_argument("--headless", type=bool, default=True, help="Run browser in headless mode")
    args = parser.parse_args()

    business_info, reviews = scrape(pages=args.pages, headless=args.headless)

    # Save results to JSON
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=4)

    print(f"Saved {len(reviews)} reviews to {args.output}")
