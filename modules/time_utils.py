import logging
import re
from datetime import datetime, timedelta
import pytz
from bs4 import BeautifulSoup


def struct_time_to_datetime(struct_time_obj):
    """
    Converts a time.struct_time object to a timezone-aware datetime object in UTC.
    """
    try:
        if not struct_time_obj:
            logging.warning("struct_time_obj is None, returning None.")
            return None

        dt = datetime(*struct_time_obj[:6], tzinfo=pytz.UTC)
        return dt
    except Exception as e:
        logging.error(f"Error converting struct_time to datetime: {e}")
        return None


def convert_to_local_time(published_time, timezone="Europe/Tirane"):
    """
    Converts the given time to the specified timezone.
    If `timezone` is not specified, it defaults to 'Europe/Tirane'.
    """
    if not published_time:
        logging.warning("Published time is None.")
        return None

    try:
        local_timezone = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        logging.error(f"Invalid timezone: {timezone}")
        return None

    if isinstance(published_time, datetime):
        if published_time.tzinfo is None:
            published_time = pytz.utc.localize(published_time)
        return published_time.astimezone(local_timezone)

    logging.warning("Unsupported time format for conversion.")
    return None


def parse_relative_time(time_text, timezone="Europe/Tirane"):
    """
    Converts relative time phrases into a datetime object. Returns `None` if parsing fails.
    """
    now = datetime.now(pytz.timezone(timezone))

    patterns = {
        r"(\d+)\s*minuta më parë": lambda m: now - timedelta(minutes=int(m.group(1))),
        r"(\d+)\s*orë më parë": lambda m: now - timedelta(hours=int(m.group(1))),
        r"(\d+)\s*ditë më parë": lambda m: now - timedelta(days=int(m.group(1))),
        r"^dje$": lambda _: now - timedelta(days=1),
    }

    for pattern, handler in patterns.items():
        match = re.match(pattern, time_text.strip().lower())
        if match:
            return handler(match)

    logging.warning(f"Failed to parse relative time: {time_text}")
    return None


def parse_date_with_formats(date_string, formats, timezone="Europe/Tirane"):
    """
    Parses a date string using a list of formats and returns a timezone-aware datetime object.
    """
    local_timezone = pytz.timezone(timezone)

    for fmt in formats:
        try:
            dt = datetime.strptime(date_string, fmt)
            return local_timezone.localize(dt)
        except ValueError:
            continue

    logging.warning(
        f"Failed to parse date string: {date_string} with provided formats."
    )
    return None


def parse_publish_date(date_string):
    """
    Tries to parse a publish date from various formats and relative phrases.
    """
    timezone = "Europe/Tirane"

    # Kontroll për fraza relative si "para 2 orësh"
    relative_time = parse_relative_time(date_string, timezone)
    if relative_time:
        return relative_time

    # Formate të njohura të datës
    date_formats = [
        "%d.%m.%Y - %H:%M",  # 02.12.2024 - 18:48
        "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601
        "%Y-%m-%d %H:%M:%S",  # 2024-12-02 18:48:00
        "%d/%m/%Y %H:%M",  # 02/12/2024 18:48
        "%d-%m-%Y %H:%M",  # 02-12-2024 18:48
    ]

    return parse_date_with_formats(date_string, date_formats, timezone)


def extract_date_from_html(soup):
    """
    Extracts a date from the HTML content using multiple selectors.
    """
    timezone = "Europe/Tirane"
    date_selectors = [
        "span.post_date",  # 02.12.2024 - 18:48
        "div.article-posted",  # Para 2 ore
    ]

    for selector in date_selectors:
        element = soup.select_one(selector)
        if element:
            date_string = element.text.strip()
            parsed_date = parse_publish_date(date_string)
            if parsed_date:
                return parsed_date

    logging.warning("No valid date found in HTML.")
    return None


def extract_date_from_html_debug(soup, html_content):
    """
    Debug version of date extractor that logs the HTML content if date parsing fails.
    """
    parsed_date = extract_date_from_html(soup)
    if not parsed_date:
        with open("debug_failed_html.txt", "a") as f:
            f.write("\n\n--- HTML Content ---\n")
            f.write(html_content)
        logging.warning("Failed to extract date. Logged HTML to debug_failed_html.txt")
    return parsed_date
