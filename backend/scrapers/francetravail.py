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


class FranceTravailScraper:
    base_url = "https://candidat.francetravail.fr"
    name = "francetravail"

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
            page_url = f"{url}&page={page}" if page > 1 else url
            html = self._fetch_page(page_url)
            soup = BeautifulSoup(html, "lxml")

            cards = soup.select("li.result[data-id-offre]")
            if not cards:
                cards = soup.select("li.result")
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
        base = f"{self.base_url}/offres/recherche"
        params = {"offresPartenaires": "true", "tri": "0"}

        keywords_parts = list(criteria.keywords)
        if criteria.location and criteria.location.lower() != "france":
            keywords_parts.append(criteria.location)
        if keywords_parts:
            params["motsCles"] = " ".join(keywords_parts)
        if criteria.radius_km:
            params["rayon"] = str(criteria.radius_km)

        return f"{base}?{urlencode(params)}"

    def _parse_job_card(self, card) -> Optional[JobOffer]:
        job_id = card.get("data-id-offre")
        if not job_id:
            link = card.select_one("a[href*='/offres/recherche/detail/']")
            if link:
                match = re.search(r"/detail/([A-Z0-9]+)", link.get("href", ""))
                if match:
                    job_id = match.group(1)
        if not job_id:
            return None

        url = f"{self.base_url}/offres/recherche/detail/{job_id}"
        title_elem = card.select_one("h2.media-heading span.media-heading-title") or card.select_one("h2.media-heading")
        title = title_elem.get_text(strip=True) if title_elem else None

        company = None
        location = None
        subtext = card.select_one("p.subtext")
        if subtext:
            content = subtext.get_text(strip=True)
            if " - " in content:
                parts = content.split(" - ", 1)
                company = parts[0].strip()
                location = parts[1].strip() if len(parts) > 1 else None

        if not title:
            return None

        return JobOffer(
            id=f"francetravail_{job_id}",
            source=self.name,
            url=url,
            title=title,
            company=company or "Entreprise confidentielle",
            location=location or "France",
        )


def search_jobs(keywords: list[str], location: str = "France", radius_km: int = None) -> list[str]:
    max_results = int(os.getenv("JOB_SEARCHES", "5"))
    scraper = FranceTravailScraper()
    criteria = SearchCriteria(
        keywords=keywords,
        location=location,
        radius_km=radius_km,
        max_results=max_results
    )
    return [job.url for job in scraper.search(criteria)]