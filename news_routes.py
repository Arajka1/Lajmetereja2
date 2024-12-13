from flask import Blueprint
from news_utils import process_news_category  # Importoni funksionin nga news_utils

news_bp = Blueprint("news", __name__)

@news_bp.route("/lokale")
def lokale():
    return process_news_category("lokale", "index.html", "Lajmet Lokale")

@news_bp.route("/nderkombetare")
def nderkombetare():
    return process_news_category(
        "nderkombetare", "nderkombetare.html", "Lajmet Ndërkombëtare"
    )
