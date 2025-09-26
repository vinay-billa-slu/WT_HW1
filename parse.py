import json
from bs4 import BeautifulSoup

# Load the HTML file
with open("listing.html", "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "html.parser")

# Extract business info
business_info = {
    "name": soup.select_one(".y-css-olzveb").get_text(strip=True) if soup.select_one(".y-css-olzveb") else "",
    "category": soup.select_one(".y-css-1cafv3i").get_text(strip=True) if soup.select_one(".y-css-1cafv3i") else "",
    "city_region": soup.select_one(".y-css-69058c").get_text(strip=True) if soup.select_one(".y-css-69058c") else "",
    "about_business": soup.select_one(".y-css-1mwo47a").get_text(strip=True) if soup.select_one(".y-css-1mwo47a") else "",
    "vibes": [span.get_text(strip=True) for span in soup.select("span.y-css-1541nhh")],
    "overall_rating": soup.select_one(".y-css-1ms5w5p").get_text(strip=True) if soup.select_one(".y-css-1ms5w5p") else "",
    "total_reviews": soup.select_one(".y-css-1x1e1r2").get_text(strip=True) if soup.select_one(".y-css-1x1e1r2") else ""
}

vibe_spans = soup.select("span.y-css-1541nhh")
vibes = [span.get_text(strip=True) for span in vibe_spans]

# Find all review items
review_items = soup.select("ul.list__09f24__ynIEd li.y-css-1sqelp2")
reviews = []

for item in review_items:
    reviewer = item.select_one("a.y-css-1x1e1r2")
    
    # Skip if no reviewer
    if not reviewer or not reviewer.get_text(strip=True):
        continue
    
    star = item.select_one("div.y-css-dnttlc")
    date = item.select_one("span.y-css-1vi7y4e")
    text = item.select_one("span.raw__09f24__T4Ezm")
    
    # Extract numeric value from "5 star rating"
    star_value = ""
    if star and star.has_attr("aria-label"):
        star_value = star["aria-label"].split()[0]  # first word
    
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

# Save to JSON
with open("parsed.json", "w", encoding="utf-8") as f:
    json.dump(reviews, f, ensure_ascii=False, indent=4)

print(f"Saved {len(reviews)} reviews to parsed.json")
