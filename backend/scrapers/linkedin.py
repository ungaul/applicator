import os
import re
import time
from datetime import datetime, timedelta
from typing import Iterator, Optional
from dataclasses import dataclass, field
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
    contract_types: list[str] = field(default_factory=list)
    experience_levels: list[str] = field(default_factory=list)
    workplace_types: list[str] = field(default_factory=list)
    date_posted: Optional[str] = None
    max_results: int = 5

class LinkedInScraper:
    base_url = "https://www.linkedin.com"
    name = "linkedin"

    EXPERIENCE_MAPPING = {"internship": "1", "junior": "2", "mid": "3", "senior": "4", "lead": "5", "director": "6"}
    CONTRACT_MAPPING = {"cdi": "F", "cdd": "C", "interim": "T", "stage": "I", "alternance": "I", "freelance": "C"}
    WORKPLACE_MAPPING = {"on_site": "1", "remote": "2", "hybrid": "3"}
    DATE_POSTED_MAPPING = {"past_24h": "r86400", "past_week": "r604800", "past_month": "r2592000"}
    RADIUS_MAPPING = {5: "5", 10: "10", 25: "25", 50: "50", 100: "100"}

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
        start = 0
        jobs_found = 0
        seen_ids = set()

        while jobs_found < criteria.max_results:
            page_url = f"{url}&start={start}"
            html = self._fetch_page(page_url)
            soup = BeautifulSoup(html, "lxml")

            cards = self._extract_job_cards(soup)
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
            start += 25
            time.sleep(self.delay)

    def _build_search_url(self, criteria: SearchCriteria) -> str:
        base = f"{self.base_url}/jobs/search"
        params = {
            "keywords": " ".join(criteria.keywords),
            "location": criteria.location or "",
            "trk": "public_jobs_jobs-search-bar_search-submit",
        }

        if criteria.experience_levels:
            codes = [self.EXPERIENCE_MAPPING.get(e.lower()) for e in criteria.experience_levels]
            codes = [c for c in codes if c]
            if codes:
                params["f_E"] = ",".join(codes)

        if criteria.contract_types:
            codes = [self.CONTRACT_MAPPING.get(c.lower()) for c in criteria.contract_types]
            codes = [c for c in codes if c]
            if codes:
                params["f_JT"] = ",".join(codes)

        if criteria.workplace_types:
            codes = [self.WORKPLACE_MAPPING.get(w.lower()) for w in criteria.workplace_types]
            codes = [c for c in codes if c]
            if codes:
                params["f_WT"] = ",".join(codes)

        if criteria.date_posted:
            code = self.DATE_POSTED_MAPPING.get(criteria.date_posted.lower())
            if code:
                params["f_TPR"] = code

        if criteria.radius_km:
            available = sorted(self.RADIUS_MAPPING.keys())
            closest = min(available, key=lambda x: abs(x - criteria.radius_km))
            params["distance"] = self.RADIUS_MAPPING[closest]

        return f"{base}?{urlencode(params)}"

    def _extract_job_cards(self, soup: BeautifulSoup) -> list:
        for sel in ["div.base-card", "li.jobs-search-results__list-item", "div.job-search-card"]:
            cards = soup.select(sel)
            if cards:
                return cards
        return []

    def _parse_job_card(self, card) -> Optional[JobOffer]:
        try:
            title_elem = card.select_one("h3.base-search-card__title, a.job-card-list__title")
            title = title_elem.get_text(strip=True) if title_elem else None

            company_elem = card.select_one("h4.base-search-card__subtitle, a.job-card-container__company-name")
            company = company_elem.get_text(strip=True) if company_elem else None

            location_elem = card.select_one("span.job-search-card__location, li.job-card-container__metadata-item")
            location = location_elem.get_text(strip=True) if location_elem else None

            link_elem = card.select_one("a.base-card__full-link, a.job-card-list__title")
            url = link_elem.get("href") if link_elem else None

            job_id = None
            if url:
                match = re.search(r"-(\d+)(?:\?|$)", url)
                if match:
                    job_id = match.group(1)
            if not job_id:
                urn = card.get("data-entity-urn", "")
                match = re.search(r"jobPosting:(\d+)", urn)
                if match:
                    job_id = match.group(1)

            if not all([title, company, job_id]):
                return None

            posted_at = self._parse_posted_date(card)

            return JobOffer(
                id=f"linkedin_{job_id}",
                source=self.name,
                url=url or f"{self.base_url}/jobs/view/{job_id}",
                title=title,
                company=company,
                location=location or "France",
                posted_at=posted_at,
            )
        except Exception:
            return None

    def _parse_posted_date(self, card) -> Optional[datetime]:
        date_elem = card.select_one("time.job-search-card__listdate")
        if date_elem:
            dt_attr = date_elem.get("datetime")
            if dt_attr:
                try:
                    return datetime.fromisoformat(dt_attr.replace("Z", "+00:00"))
                except ValueError:
                    pass
        return None

def search_jobs(
    keywords: list[str],
    location: str = "France",
    radius_km: int = None,
    contract_types: list[str] = None,
    experience_levels: list[str] = None,
    workplace_types: list[str] = None,
    date_posted: str = None
) -> list[str]:
    max_results = int(os.getenv("JOB_SEARCHES", "5"))
    scraper = LinkedInScraper()
    criteria = SearchCriteria(
        keywords=keywords,
        location=location,
        radius_km=radius_km,
        contract_types=contract_types or [],
        experience_levels=experience_levels or [],
        workplace_types=workplace_types or [],
        date_posted=date_posted,
        max_results=max_results
    )
    return [job.url for job in scraper.search(criteria)]