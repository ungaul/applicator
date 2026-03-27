import os
import re
import time
from datetime import datetime
from typing import Iterator, Optional
from dataclasses import dataclass
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup


@dataclass
class JobOffer:
    id: str
    source: str
    url: str
    title: str
    company: str
    location: str
    posted_at: Optional[datetime] = None


@dataclass
class SearchCriteria:
    keywords: list[str]
    location: str = "France"
    radius_km: Optional[int] = None
    max_results: int = 5


class HelloWorkScraper:
    base_url = "https://www.hellowork.com"
    name = "hellowork"

    def __init__(self):
        self.delay = 2

    def _get_headers(self) -> dict:
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        }

    def _fetch_page(self, url: str) -> str:
        response = requests.get(url, headers=self._get_headers(), timeout=30)
        response.raise_for_status()
        return response.text

    def search(self, criteria: SearchCriteria) -> Iterator[JobOffer]:
        url = self._build_search_url(criteria)
        page = 1
        jobs_found = 0
        seen_ids = set()

        while jobs_found < criteria.max_results:
            page_url = f"{url}&p={page}" if page > 1 else url
            html = self._fetch_page(page_url)
            soup = BeautifulSoup(html, "lxml")

            cards = soup.select("li[data-id-storage-item-id]")
            if not cards:
                links = soup.select("a[href*='/fr-fr/emplois/']")
                seen_hrefs = set()
                cards = []
                for link in links:
                    href = link.get("href", "")
                    if href in seen_hrefs:
                        continue
                    seen_hrefs.add(href)
                    parent = link.find_parent("li")
                    if parent and parent not in cards:
                        cards.append(parent)
            if not cards:
                break

            new_jobs = 0
            for card in cards:
                if jobs_found >= criteria.max_results:
                    break
                job = self._parse_job_card(card)
                if job and job.id not in seen_ids:
                    seen_ids.add(job.id)
                    jobs_found += 1
                    new_jobs += 1
                    yield job

            if new_jobs == 0:
                break
            page += 1
            time.sleep(self.delay)

    def _build_search_url(self, criteria: SearchCriteria) -> str:
        base = f"{self.base_url}/fr-fr/emploi/recherche.html"
        params = {}
        if criteria.keywords:
            params["k"] = " ".join(criteria.keywords)
        if criteria.location:
            params["l"] = criteria.location
        if criteria.radius_km:
            params["ray"] = str(criteria.radius_km)
        return f"{base}?{urlencode(params)}" if params else base

    def _parse_job_card(self, card) -> Optional[JobOffer]:
        try:
            job_id = card.get("data-id-storage-item-id")
            if not job_id:
                return None

            link = card.select_one("a[href*='/emplois/']")
            url = link.get("href", "") if link else f"/fr-fr/emplois/{job_id}.html"
            if url.startswith("/"):
                url = f"{self.base_url}{url}"

            title_input = card.select_one('input[name="title"]')
            if title_input:
                title = title_input.get("value", "").strip()
            else:
                title_elem = card.select_one("p.tw-typo-l, h3, h2")
                title = title_elem.get_text(strip=True) if title_elem else None

            company_input = card.select_one('input[name="company"]')
            if company_input:
                company = company_input.get("value", "").strip()
            else:
                company_elem = card.select_one("p.tw-typo-s.tw-inline")
                company = company_elem.get_text(strip=True) if company_elem else None

            location = None
            tags = card.select("div.tw-tag-secondary-s, div.tw-readonly.tw-tag-secondary-s")
            for tag in tags:
                text = tag.get_text(strip=True)
                if re.search(r"\d{2,5}$|^\d{5}", text):
                    location = text
                    break

            if not title:
                return None

            return JobOffer(
                id=f"hellowork_{job_id}",
                source=self.name,
                url=url,
                title=title,
                company=company or "Non spécifié",
                location=location or "France",
            )
        except Exception:
            return None


def search_jobs(keywords: list[str], location: str = "France", radius_km: int = None) -> list[str]:
    max_results = int(os.getenv("JOB_SEARCHES", "5"))
    scraper = HelloWorkScraper()
    criteria = SearchCriteria(
        keywords=keywords,
        location=location,
        radius_km=radius_km,
        max_results=max_results
    )
    return [job.url for job in scraper.search(criteria)]