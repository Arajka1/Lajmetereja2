import atexit
import json
import logging
import os
from deep_translator import GoogleTranslator
from modules.cache_utils import get_cache, set_cache

# Setting up logging
logging.basicConfig(level=logging.INFO)

TRANSLATION_CACHE_TIMEOUT = 86400  # 24 orë

translation_cache = {}

CACHE_FILE = "translation_cache.json"  # Skedar për ruajtjen e përkthimeve
CACHE_LIMIT = 1000  # Kufiri i titujve të ruajtur në cache


def ngarko_translation_cache():
    """
    Ngarkon cache-in e përkthimit nga një skedar JSON.
    """
    global translation_cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                translation_cache = json.load(f)
            logging.info(f"Cache u ngarkua me sukses me {len(translation_cache)} tituj.")
        except (json.JSONDecodeError, OSError) as e:
            logging.error(f"Gabim gjatë ngarkimit të cache: {e}")
            translation_cache = {}  # Reset cache on error


def ruaj_translation_cache():
    """
    Ruaj cache-in e përkthimit në një skedar JSON.
    """
    try:
        if len(translation_cache) > CACHE_LIMIT:
            logging.info(f"Cache tejkaloi limitin prej {CACHE_LIMIT}, duke pastruar cache.")
            translation_cache.clear()
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(translation_cache, f, ensure_ascii=False, indent=4)
        logging.info("Cache u ruajt me sukses.")
    except OSError as e:
        logging.error(f"Gabim gjatë ruajtjes së cache-it: {e}")


def translate_title(title):
    """
    Përkthen titullin dhe ruan përkthimin në cache.
    """
    if not title:
        logging.warning("Titulli është i zbrazët.")
        return title

    # Kontrollo në cache
    cached_translation = get_cache(f"translation:{title}")
    if cached_translation:
        logging.info(f"Titulli i përkthyer u gjet në cache: {cached_translation}")
        return cached_translation

    try:
        translated = GoogleTranslator(source="auto", target="sq").translate(title)
        logging.info(f"Përkthimi për titullin: '{title}' -> '{translated}'")

        # Ruaj përkthimin në cache
        set_cache(f"translation:{title}", translated, timeout=TRANSLATION_CACHE_TIMEOUT)
        return translated
    except Exception as e:
        logging.error(f"Gabim gjatë përkthimit: {e}")
        return title  # Kthe titullin origjinal në rast gabimi
    

# Ngarko cache-in ekzistues kur moduli importohet
ngarko_translation_cache()

# Ruaj cache-in automatikisht kur programi përfundon
atexit.register(ruaj_translation_cache)

# Testimi i funksionalitetit
if __name__ == "__main__":
    test_title = "Hello world"
    translated_title = translate_title(test_title)
    print(f"Original: {test_title}\nTranslated: {translated_title}")
