from flask import current_app, render_template
from datetime import datetime
from config import Config
from modules.cache_utils import get_cache, set_cache
import logging
import traceback
from fetch_news import fetch_latest_news


def process_news_category(category, template_name, title):
    """
    Përpunon lajmet për një kategori specifike dhe shfaq template-n.
    """
    try:
        start_time = datetime.now()  # Pika e fillimit
        logging.info(f"Processing news for category: {category}")

        # Kontrolloni nëse cache është inicializuar duke përdorur current_app
        if not getattr(current_app, 'cache_initialized', False):
            logging.warning(
                "Cache nuk është inicializuar. Duke përdorur të dhënat pa cache."
            )
            return render_template(
                "error.html",
                message="Cache nuk është i inicializuar.",
                error_details="Probleme me inicializimin e Cache-it.",
            ), 500

        logging.debug(f"Cache state for {category}: {current_app.cache_initialized}")
        grouped_feed = {
            "Top 10 Lajmet e Fundit": get_cache(
                f"grouped_feed_{category}_top_10_lajmet_e_fundit"
            )
            or [],
            "Lajmet e Përsëritura": get_cache(
                f"grouped_feed_{category}_lajmet_e_përsëritura"
            )
            or [],
            "Lajmet Brenda 24 Orëve": get_cache(
                f"grouped_feed_{category}_lajmet_brenda_24_orëve"
            )
            or [],
            "Lajmet Tjera": get_cache(f"grouped_feed_{category}_lajmet_tjera") or [],
        }

        if not any(grouped_feed.values()):
            logging.info(
                f"Cache is empty for category {category}. Fetching fresh data."
            )
            grouped_feed, _ = fetch_latest_news(category=category)

            if isinstance(grouped_feed, dict):
                for key, value in grouped_feed.items():
                    cache_key = (
                        f"grouped_feed_{category}_{key.lower().replace(' ', '_')}"
                    )
                    set_cache(cache_key, value, timeout=Config.CACHE_TIMEOUT)
                    logging.info(f"Data cached for key: {cache_key}")
        else:
            logging.info(f"Using cached data for {category}")

        max_items = 100
        for key in grouped_feed:
            grouped_feed[key] = grouped_feed[key][:max_items]

        end_time = datetime.now()  # Pika e përfundimit
        processing_time = end_time - start_time
        logging.debug(f"Processing for category {category} took {processing_time}")

        logging.info(f"Successfully processed news for category: {category}")
        return render_template(
            template_name,
            title=title,
            grouped_new_news=grouped_feed["Top 10 Lajmet e Fundit"],
            grouped_duplicate_news=grouped_feed["Lajmet e Përsëritura"],
            grouped_24hr_news=grouped_feed["Lajmet Brenda 24 Orëve"],
            grouped_other_news=grouped_feed["Lajmet Tjera"],
            news_count={
                "Total": sum(len(v) for v in grouped_feed.values()),
                "Top 10 Lajmet e Fundit": len(grouped_feed["Top 10 Lajmet e Fundit"]),
                "Lajmet e Përsëritura": len(grouped_feed["Lajmet e Përsëritura"]),
                "Lajmet Brenda 24 Orëve": len(grouped_feed["Lajmet Brenda 24 Orëve"]),
                "Lajmet Tjera": len(grouped_feed["Lajmet Tjera"]),
            },
        )
    except Exception as e:
        logging.error(
            f"Error processing news for category {category}: {traceback.format_exc()}"
        )
        return (
            render_template(
                "error.html",
                message="Gabim gjatë përpunimit të lajmeve!",
                error_details=str(e),
            ),
            500,
        )
