"""Fetches and cleans website content so it can be handed to the LLM."""
import logging
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MAX_CHARS = 8000  # keep the LLM prompt a reasonable size


async def scrape_website(url: str) -> str:
    """
    Fetch a URL and return cleaned, readable text content.
    Returns an empty string if the fetch fails (caller should fall back
    to the questions flow in that case).
    """
    if not url.startswith("http"):
        url = f"https://{url}"

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (JubalaBot)"})
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Strip non-content tags
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = " ".join(text.split())  # collapse whitespace

        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS]

        logger.info(f"Scraped {len(text)} chars from {url}")
        return text

    except Exception as e:
        logger.error(f"Failed to scrape {url}: {e}")
        return ""
