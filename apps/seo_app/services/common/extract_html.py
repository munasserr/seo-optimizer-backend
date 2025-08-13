from bs4 import BeautifulSoup
import requests


def extract_html(url: str) -> str:
    """Fetch a webpage and return clean, readable text for SEO analysis."""
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove unwanted tags entirely
    for tag in soup(
        ["script", "style", "noscript", "iframe", "header", "footer", "nav"]
    ):
        tag.decompose()

    # Whitelist
    allowed_tags = {
        "p",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "a",
        "strong",
        "em",
        "blockquote",
    }
    for tag in soup.find_all(True):
        if tag.name not in allowed_tags:
            tag.unwrap()  # remove the tag but keep its contents
        else:
            tag.attrs = {}  # remove all attributes (style, class, etc.)

    # Get body content only
    cleaned_html = str(soup.body) if soup.body else str(soup)

    # Remove excessive whitespace
    cleaned_html = " ".join(cleaned_html.split())

    return cleaned_html


def extract_text_from_html(url: str) -> str:
    """Fetch a webpage and return clean, readable text for SEO analysis."""
    response = requests.get(url, timeout=10)
    response.raise_for_status() 

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove unwanted tags
    for tag in soup(
        ["script", "style", "noscript", "iframe", "header", "footer", "nav"]
    ):
        tag.decompose()

    # Extract only meaningful text
    text = soup.get_text(separator=" ", strip=True)

    # Remove excessive spaces/newlines
    cleaned_text = " ".join(text.split())

    return cleaned_text
