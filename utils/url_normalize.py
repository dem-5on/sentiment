import re
import feedparser

def normalize_rss_url(raw_url: str) -> str:
    """
    Normalize a user-provided RSS source string into a valid URL.
    - Adds https:// if missing
    - Appends /rss if it looks like just a domain
    """
    url = raw_url.strip()

    # Ensure protocol
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # If it's clearly an RSS/atom feed already, return as-is
    if re.search(r"(rss|feed|xml)", url, re.IGNORECASE):
        return url

    # Otherwise, assume /rss endpoint
    if url.endswith("/"):
        url += "rss"
    else:
        url += "/rss"

    return url



def is_valid_rss_feed(url: str) -> bool:
    parsed = feedparser.parse(url)
    return not parsed.bozo
