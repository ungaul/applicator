import requests
from bs4 import BeautifulSoup
from typing import Optional


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}


def _extract_francetravail(soup: BeautifulSoup) -> dict:
    desc = soup.select_one("div.description-offer")
    return {
        "description": desc.get_text("\n", strip=True) if desc else None,
        "salary": _text(soup, "span.salary"),
        "contract_type": _text(soup, "span.contract-type"),
        "remote": None,
    }


def _extract_hellowork(soup: BeautifulSoup) -> dict:
    desc = soup.select_one("div[data-cy='job-description']") or soup.select_one("div.job-description")
    return {
        "description": desc.get_text("\n", strip=True) if desc else None,
        "salary": _text(soup, "div.salary"),
        "contract_type": None,
        "remote": None,
    }


def _extract_linkedin(soup: BeautifulSoup) -> dict:
    desc = soup.select_one("div.show-more-less-html__markup")
    return {
        "description": desc.get_text("\n", strip=True) if desc else None,
        "salary": _text(soup, "div.salary"),
        "contract_type": _text(soup, "span.job-criteria__text"),
        "remote": None,
    }


def _extract_wttj(soup: BeautifulSoup) -> dict:
    desc = soup.select_one("div[data-testid='job-description']") or soup.select_one("section.job-description")
    return {
        "description": desc.get_text("\n", strip=True) if desc else None,
        "salary": None,
        "contract_type": None,
        "remote": None,
    }


def _extract_generic(soup: BeautifulSoup) -> dict:
    candidates = soup.select("article, main, section, div.description, div.content, div.job-description")
    best = max(candidates, key=lambda el: len(el.get_text()), default=None)
    return {
        "description": best.get_text("\n", strip=True)[:5000] if best else None,
        "salary": None,
        "contract_type": None,
        "remote": None,
    }


EXTRACTORS = {
    "francetravail": _extract_francetravail,
    "hellowork": _extract_hellowork,
    "linkedin": _extract_linkedin,
    "wttj": _extract_wttj,
    "adzuna": _extract_generic,
}


def _text(soup: BeautifulSoup, selector: str) -> Optional[str]:
    el = soup.select_one(selector)
    return el.get_text(strip=True) if el else None


async def fetch_job_page(url: str, source: str) -> dict:
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_sync, url, source)


def _fetch_sync(url: str, source: str) -> dict:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    extractor = EXTRACTORS.get(source, _extract_generic)
    data = extractor(soup)
    data["url"] = url
    data["source"] = source
    return data
