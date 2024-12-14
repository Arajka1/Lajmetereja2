# -*- coding: utf-8 -*-
import logging
import os
import traceback
from datetime import datetime
from functools import wraps
from urllib.parse import unquote

from flask import Flask, Response, jsonify, redirect, render_template, request, url_for
from flask_caching import Cache
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config
from fetch_news import fetch_latest_news
from news_routes import news_bp
from modules.cache_utils import set_cache, get_cache, set_cache_instance
from threading import Timer
from concurrent.futures import ThreadPoolExecutor

# Deklarime globale
cache_initialized = False

# --------------------------------------------------
# Inicializimi i Aplikacionit dhe Konfigurimeve
# --------------------------------------------------

def initialize_logging():
    """
    Konfigurimi i logimit për aplikacionin.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
    )
    logging.info("Sistemi i logimit është inicializuar.")

def create_app():
    """
    Krijon instancën e aplikacionit Flask dhe inicializon modifikimet.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    initialize_logging()
    initialize_extensions(app)

    # Vendos statusin e inicializimit të cache-it
    app.cache_initialized = cache_initialized

    return app

# Inicializimi i moduleve globale
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()

def initialize_extensions(app):
    """
    Inicializon bazën e të dhënave, migrimet dhe cache-in duke përdorur Redis.
    """
    global cache_initialized

    # Inicializimi i SQLAlchemy dhe Migrate
    db.init_app(app)
    migrate.init_app(app, db)

    # Konfigurimi i Cache
    app.config["CACHE_TYPE"] = "RedisCache"
    app.config["CACHE_REDIS_URL"] = os.getenv(
        "REDIS_URL",
        "redis://default:S1N0FutqvUF0XV6vE31GxjODRvts0CsQ@redis-18319.c100.us-east-1-4.ec2.redns.redis-cloud.com:18319/0",
    )

    try:
        cache.init_app(app)
        set_cache_instance(cache)
        cache_initialized = True
        logging.info("Cache është inicializuar me sukses!")
    except Exception as e:
        cache_initialized = False
        logging.error(f"Gabim gjatë inicializimit të cache-it: {e}")

# --------------------------------------------------
# Modelet e Bazës së të Dhënave
# --------------------------------------------------

class VisitorStat(db.Model):
    """
    Model për të regjistruar informacionet e vizitorëve.
    """
    __tablename__ = "visitor_stats"
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(100), nullable=False)
    endpoint = db.Column(db.String(1000), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    device = db.Column(db.String(200), nullable=True)
    browser = db.Column(db.String(200), nullable=True)
    timezone = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f"<VisitorStat {self.ip} {self.endpoint[:50]}... {self.timestamp}>"

# --------------------------------------------------
# Dekoratori për Siguri
# --------------------------------------------------

PRIVATE_STATS_USERNAME = os.getenv("STATS_USERNAME", "default_username")
PRIVATE_STATS_PASSWORD = os.getenv("STATS_PASSWORD", "default_password")

def require_password(f):
    """
    Dekorator për të mbrojtur disa rrugë me username dhe fjalëkalim.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if (
            not auth
            or auth.username != PRIVATE_STATS_USERNAME
            or auth.password != PRIVATE_STATS_PASSWORD
        ):
            return Response(
                "Qasje e paautorizuar. Ju lutem vendosni username dhe fjalëkalimin korrekt.",
                401,
                {"WWW-Authenticate": 'Basic realm="Login Required"'},
            )
        return f(*args, **kwargs)
    return decorated_function

# --------------------------------------------------
# Rrugët (Routes)
# --------------------------------------------------

app = create_app()
app.register_blueprint(news_bp)

@app.route("/")
def index():
    return redirect(url_for("lokale"))

@app.route("/latest_news", methods=["GET"])
def latest_news():
    """
    Kthen lajmet më të fundit nga cache ose krijon lajme të reja nëse ato mungojnë.
    """
    try:
        # Përdor cache për të kontrolluar lajmet lokale
        cache_key = "grouped_feed_lokale"
        cached_news = get_cache(cache_key)
        if cached_news:
            logging.info("Lajmet e fundit u kthyen nga cache.")
            return jsonify({"news": cached_news}), 200

        # Nëse cache është bosh, mbushe atë
        grouped_feed, _ = fetch_latest_news(category="lokale")
        set_cache(cache_key, grouped_feed, timeout=86400)
        logging.info("Lajmet e fundit u krijuan dhe u ruajtën në cache.")
        return jsonify({"news": grouped_feed}), 200
    except Exception as e:
        logging.error(f"Gabim gjatë kthimit të lajmeve të fundit: {e}")
        return jsonify({"error": "Gabim gjatë kthimit të lajmeve të fundit."}), 500

def fetch_latest_news(category):
    """
    Mbushe lajmet e fundit për një kategori të dhënë.
    """
    news_sources = get_sources_for_category(category)
    grouped_feed = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_source = {executor.submit(fetch_news_from_source, source): source for source in news_sources}
        for future in future_to_source:
            try:
                result = future.result(timeout=10)  # Timeout për çdo burim
                if result:
                    grouped_feed.extend(result)
            except Exception as e:
                logging.warning(f"Gabim gjatë marrjes së lajmeve nga burimi {future_to_source[future]}: {e}")

    summary = {"Total": len(grouped_feed)}
    return grouped_feed, summary


@app.route("/lokale", endpoint="lokale")
def lokale():
    cache_key = "grouped_feed_lokale"
    cached_news = get_cache(cache_key)
    if cached_news:
        logging.info("Lajmet Lokale u ngarkuan nga cache.")
        return render_template("index.html", news=cached_news, news_count={"Total": len(cached_news)})
    
    # Nis përpunimin në sfond për rifreskimin e lajmeve
    try:
        grouped_feed, summary = fetch_latest_news(category="lokale")
        set_cache(cache_key, grouped_feed, timeout=86400)
        logging.info("Cache u rifreskua për kategorinë 'lokale'.")
    except Exception as e:
        logging.error(f"Gabim gjatë rifreskimit të lajmeve lokale: {e}")
    
    # Kthe një faqe me të dhënat nga cache edhe nëse përpunimi në sfond është ende në vazhdim
    return render_template("index.html", news=cached_news or [], news_count={"Total": len(cached_news) if cached_news else 0})

@app.route("/nderkombetare", endpoint="nderkombetare")
def nderkombetare():
    cache_key = "grouped_feed_nderkombetare"
    cached_news = get_cache(cache_key)
    if cached_news:
        logging.info("Lajmet Ndërkombëtare u ngarkuan nga cache.")
        return render_template("nderkombetare.html", news=cached_news, news_count={"Total": len(cached_news)})

    # Nis përpunimin në sfond për rifreskimin e lajmeve
    try:
        grouped_feed, summary = fetch_latest_news(category="nderkombetare")
        set_cache(cache_key, grouped_feed, timeout=86400)
        logging.info("Cache u rifreskua për kategorinë 'nderkombetare'.")
    except Exception as e:
        logging.error(f"Gabim gjatë rifreskimit të lajmeve ndërkombëtare: {e}")

    # Kthe një faqe me të dhënat nga cache edhe nëse përpunimi në sfond është ende në vazhdim
    return render_template("nderkombetare.html", news=cached_news or [], news_count={"Total": len(cached_news) if cached_news else 0})


@app.route("/refresh_news", methods=["POST"])
def refresh_news():
    try:
        category = request.json.get("category", "lokale")
        if category not in ["lokale", "nderkombetare"]:
            return jsonify({"error": "Kategoria nuk njihet."}), 400

        # Rifresko cache-in për kategorinë e kërkuar
        grouped_feed, summary = fetch_latest_news(category=category)
        cache_key = f"grouped_feed_{category}"
        set_cache(cache_key, grouped_feed, timeout=86400)

        logging.info(f"Rifreskimi manual për kategorinë '{category}' përfundoi.")
        return jsonify({"message": f"Lajmet për kategorinë '{category}' u rifreskuan me sukses!"}), 200
    except Exception as e:
        logging.error(f"Gabim gjatë rifreskimit manual të lajmeve: {traceback.format_exc()}")
        return jsonify({"error": "Gabim gjatë rifreskimit të lajmeve.", "details": str(e)}), 500

@app.route("/lajm/<path:link>")
def vizito_lajm(link):
    try:
        link = unquote(link)
        if not link.startswith("http"):
            raise ValueError("URL duhet të fillojë me http ose https!")
        return redirect(link)
    except Exception as e:
        logging.error(f"Gabim gjatë hapjes së lajmit: {e}")
        return render_template("error.html", message="Gabim gjatë hapjes së lajmit!", error_details=str(e)), 500

@app.after_request
def add_header(response):
    if "Cache-Control" not in response.headers:
        response.headers["Cache-Control"] = "public, max-age=31536000"
    return response

# --------------------------------------------------
# Rifreskimi automatik i cache-it
# --------------------------------------------------

def auto_refresh_cache():
    """
    Rifreskon cache-in automatikisht çdo 3 minuta për kategoritë 'lokale' dhe 'nderkombetare'.
    """
    try:
        for category in ["lokale", "nderkombetare"]:
            grouped_feed, summary = fetch_latest_news(category=category)
            cache_key = f"grouped_feed_{category}"
            set_cache(cache_key, grouped_feed, timeout=86400)
            logging.info(f"Cache për kategorinë '{category}' u rifreskua automatikisht.")
    except Exception as e:
        logging.error(f"Gabim gjatë rifreskimit automatik të cache-it: {traceback.format_exc()}")
    finally:
        # Rifreskimi pas 3 minutash
        Timer(180, auto_refresh_cache).start()

# --------------------------------------------------
# Ekzekutimi i aplikacionit
# --------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # Nisni rifreskimin automatik për kategoritë 'lokale' dhe 'nderkombetare'
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

