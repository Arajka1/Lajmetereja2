# --------------------------------------------------
# Importet standarde të Python
# --------------------------------------------------
import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from urllib.parse import urljoin, urlparse
from modules.translator_utils import translate_title

# --------------------------------------------------
# Importet e palëve të treta
# --------------------------------------------------
import feedparser
import pytz
import requests
from bs4 import BeautifulSoup
from flask import Flask, redirect, request, jsonify

# --------------------------------------------------
# Importet e moduleve lokale/projektit
# --------------------------------------------------
from modules.cache_utils import get_cache, set_cache
from modules.time_utils import convert_to_local_time, struct_time_to_datetime
from flask_cors import CORS
# --------------------------------------------------
# Konfigurimi i logimit me rotacione
# --------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler("fetch_news.log", maxBytes=5000000, backupCount=3, encoding="utf-8"),
    ],
)
logging.info("Sistemi i logimit është inicializuar.")

original_title = "This is a sample title"
translated_title = translate_title(original_title)
print(translated_title)
# --------------------------------------------------
# Krijimi i instancës Flask
# --------------------------------------------------
app = Flask(__name__)
CORS(app)  # Lejon CORS për të gjitha endpoint-et

@app.route("/vizito_lajm")
def vizito_lajm():
    link = request.args.get("link")
    if not link or not urlparse(link).scheme:
        return "Lidhja është e pavlefshme!", 400
    return redirect(link)

@app.route('/latest_news', methods=['GET'])
def latest_news():
    # Shembull i strukturës së të dhënave
    news_data = [
        {"title": "Lajmi 1", "content": "Përmbajtja e lajmit 1"},
        {"title": "Lajmi 2", "content": "Përmbajtja e lajmit 2"}
    ]
    return jsonify(news_data)

# Burimet për lajmet lokale dhe ndërkombëtare
local_domains = [
    'https://telegrafi.com/feed',
    'https://kallxo.com/feed',
    'https://www.gazetaexpress.com/feed',
    'https://ekonomiaonline.com/feed',
    'https://lajmi.net/feed',
    'https://www.gazetablic.com/feed',
    'https://zeri.info/rss',
    'https://periskopi.com/feed',
    'https://www.botasot.info/rss',
    'https://veriu.info/feed',
    'https://jepize.com/feed',
    'https://www.vushtrriaonline.net/feed',
    'https://rajoni.org/feed',
    'https://drenicaonline.com/feed',
    'https://prishtinasot.com/feed',
    'https://prizrenisot.net/feed',
    'https://ferizajpress.com/feed',
]

international_domains = [
    "https://news.google.com/rss",
    "https://www.euronews.com/rss?format=mrss",
]


def generate_source_urls(domains):
    """
    Gjeneron URL-të e mundshme për burimet (RSS, feed, etj.).
    """
    return [
        {
            "name": urlparse(domain).netloc.replace("www.", ""),
            "main_url": domain,
            "rss_url": f"{domain}/rss",
            "feed_url": f"{domain}/feed",
        }
        for domain in domains
    ]

def extract_image(image_tag, base_url):
    """
    Nxjerr URL-në e imazhit nga tagu i imazhit.
    """
    if not image_tag:
        return None
    image_url = (
        image_tag.get("src")
        or image_tag.get("data-bg")
        or image_tag.get("data-src")
    )
    return urljoin(base_url, image_url) if image_url else None


def fetch_feed_with_timeout(feed_url, timeout=5):
    """
    Merr feed nga një URL me timeout dhe kthen një objekt të analizuar me feedparser.
    """
    try:
        response = requests.get(feed_url, timeout=10)

        response.raise_for_status()
        return feedparser.parse(response.text)
    except requests.RequestException as e:
        logging.warning("Timeout ose gabim për burimin %s: %s", feed_url, str(e))
        return None


def fetch_latest_news(category="lokale"):
    """
    Merr lajmet për një kategori të caktuar dhe grupon lajmet e përsëritura afër njëri-tjetrit.
    """
    now = datetime.now(pytz.timezone("Europe/Tirane"))
    limit_24_hours = now - timedelta(hours=24)

    sources = get_sources_by_category(category)
    grouped_titles = defaultdict(list)

    for source in sources:
        try:
            feed = fetch_feed_with_timeout(source["main_url"])
            articles = process_feed(feed, source["name"])
            
            for article in articles:
                title = article["title"].strip().lower()
                if category == "nderkombetare":
                    article["translated_title"] = translate_title(article["title"])
                grouped_titles[title].append(article)
        except Exception as e:
            logging.warning("Gabim gjatë përpunimit të burimit %s: %s", source.get("main_url"), str(e))

    if not grouped_titles:
        logging.warning(f"Nuk u gjetën lajme për kategorinë {category}.")
        return {
            "Top 10 Lajmet e Fundit": [],
            "Lajmet e Përsëritura": [],
            "Lajmet Brenda 24 Orëve": [],
            "Lajmet Tjera": [],
        }, {"total_articles": 0}

    grouped_feed = group_articles(grouped_titles, limit_24_hours)
    feed_summary = {
        "total_articles": sum(len(v) for v in grouped_feed.values()),
    }
    return grouped_feed, feed_summary

def fetch_news_source(source_url, retries=2):
    for attempt in range(retries):
        try:
            # Përpjekje për të marrë të dhënat
            response = requests.get(source_url, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logging.warning(f"Gabim për burimin {source_url}: {e}")
            if attempt < retries - 1:
                logging.info(f"Riprovojmë për burimin {source_url}... ({attempt + 1}/{retries})")
                time.sleep(2)  # Pritje përpara përpjekjes tjetër
            else:
                logging.error(f"Dështoi për burimin {source_url} pas {retries} përpjekjeve.")
                return None

def fetch_news(category, retries=3):
    for attempt in range(retries):
        try:
            # Marr të dhënat
            news_data = actual_fetch_logic(category)
            return news_data
        except TimeoutError as e:
            logging.warning(f"Timeout për kategorinë {category}. Përpjekja {attempt + 1}/{retries}.")
            if attempt == retries - 1:
                logging.error(f"Dështoi për kategorinë {category} pas {retries} përpjekjeve.")
                return None

def process_feed(feed, source_name):
    """
    Përpunon feed dhe kthen artikujt si një listë.
    """
    if not feed or not hasattr(feed, "entries"):
        return []

    articles = []
    default_image = "/static/default_image.png"  # Rruga e imazhit default

    for entry in feed.entries:
        title = entry.title.strip()
        link = entry.link.strip()
        publish_time = struct_time_to_datetime(entry.get("published_parsed"))
        publish_time = convert_to_local_time(publish_time) if publish_time else None

        # Kontrollo për imazhe në media:content ose përdor imazhin default
        image_url = None
        if "media_content" in entry:
            image_url = entry.media_content[0].get("url")
        elif "enclosure" in entry:
            image_url = entry.enclosure.get("url")
        else:
            image_url = default_image  # Përdor imazhin default nëse asnjë nuk gjendet

        articles.append(
            {
                "title": title,
                "link": link,
                "summary": entry.get("summary", "").strip(),
                "published_time": publish_time.isoformat() if publish_time else None,
                "display_time": publish_time.strftime("%d.%m.%Y - %H:%M:%S") if publish_time else "Data e panjohur",
                "image_url": image_url,
                "source_name": source_name,
            }
        )
    return articles

def process_international_news(news_items):
    for news in news_items:
        news["translated_title"] = translate_titull(news["title"])
    return news

def fetch_image_from_article(link):
    """
    Merr imazhin e parë nga përmbajtja e faqes së lajmit, duke trajtuar lazy loading dhe atributet alternative.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(link, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Prioritet për imazhet
        image_tag = soup.find("img")
        if image_tag:
            # Kontrollo për src, data-src, srcset
            image_url = (
                image_tag.get("src") or
                image_tag.get("data-src") or
                image_tag.get("data-bg") or
                image_tag.get("data-srcset") or
                image_tag.get("srcset")
            )
            if image_url:
                return image_url.split(",")[0].strip()  # Merret vetëm URL-ja e parë nga srcset
            
        # Nëse nuk gjendet, kërko tags alternative
        lazy_load_image = soup.find("div", {"class": "lazy-image"})
        if lazy_load_image and lazy_load_image.get("data-src"):
            return lazy_load_image["data-src"]

    except Exception as e:
        logging.warning(f"Gabim gjatë scraping për imazhin nga {link}: {e}")
    return "/static/default_image.png"  # Përdor imazhin default nëse nuk gjendet


def group_articles(grouped_titles, limit_24_hours):
    """
    Grupimi i lajmeve dhe eliminimi i duplikatëve sipas titullit dhe burimit.
    """
    repeated_articles = []
    unique_articles = {"recent": [], "older": []}
    seen_articles = set()  # Set për të mbajtur tituj dhe burime unike

    for title, articles in grouped_titles.items():
        for article in articles:
            unique_key = (article["title"].lower().strip(), article["source_name"].lower())
            if unique_key in seen_articles:
                repeated_articles.append(article)
            else:
                seen_articles.add(unique_key)
                publish_time = article.get("published_time")
                if publish_time and datetime.fromisoformat(publish_time) >= limit_24_hours:
                    unique_articles["recent"].append(article)
                else:
                    unique_articles["older"].append(article)

    # Kombino artikujt për Top 10
    top_articles = unique_articles["recent"] + unique_articles["older"]
    top_articles = [
        article for article in top_articles if article.get("published_time")
    ]
    top_articles.sort(key=lambda x: x["published_time"], reverse=True)

    return {
        "Top 10 Lajmet e Fundit": top_articles[:10],
        "Lajmet e Përsëritura": repeated_articles,
        "Lajmet Brenda 24 Orëve": unique_articles["recent"],
        "Lajmet Tjera": unique_articles["older"],
    }


def get_sources_by_category(category):
    """
    Kthen burimet në bazë të kategorisë.
    """
    if category == "lokale":
        return generate_source_urls(local_domains)
    elif category == "nderkombetare":
        return generate_source_urls(international_domains)
    return []

