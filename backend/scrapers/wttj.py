import os
from datetime import datetime
from typing import Iterator, Optional
from dataclasses import dataclass, field

import requests

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
    contract_types: list[str] = field(default_factory=list)
    workplace_types: list[str] = field(default_factory=list)
    max_results: int = 5


class WTTJScraper:
    base_url = "https://www.welcometothejungle.com"
    name = "wttj"

    ALGOLIA_APP_ID = "CSEKHVMS53"
    ALGOLIA_API_KEY = "4bd8f6215d0cc52b26430765769e65a0"
    ALGOLIA_INDEX = "wttj_jobs_production_fr"

    CONTRACT_MAPPING = {
        "full_time": "cdi", "part_time": "cdi", "fixed_term": "cdd",
        "temporary": "interim", "internship": "stage", "apprenticeship": "alternance",
        "freelance": "freelance", "vie": "cdd",
    }

    CONTRACT_FILTER_MAPPING = {
        "cdi": ["full_time", "part_time"],
        "cdd": ["fixed_term", "vie"],
        "interim": ["temporary"],
        "stage": ["internship"],
        "alternance": ["apprenticeship"],
        "freelance": ["freelance"],
    }

    def __init__(self):
        self.hits_per_page = 20

    def search(self, criteria: SearchCriteria) -> Iterator[JobOffer]:
        jobs_found = 0
        page = 0
        seen_ids = set()

        query = self._build_query(criteria)
        filters = self._build_filters(criteria)

        while jobs_found < criteria.max_results:
            results = self._fetch_algolia(query, filters, page)
            hits = results.get("hits", [])
            if not hits:
                break

            for hit in hits:
                if jobs_found >= criteria.max_results:
                    break
                job = self._parse_hit(hit)
                if job and job.id not in seen_ids:
                    seen_ids.add(job.id)
                    jobs_found += 1
                    yield job

            if page >= results.get("nbPages", 1) - 1:
                break
            page += 1

    def _fetch_algolia(self, query: str, filters: str, page: int) -> dict:
        url = f"https://{self.ALGOLIA_APP_ID.lower()}-dsn.algolia.net/1/indexes/{self.ALGOLIA_INDEX}/query"
        headers = {
            "X-Algolia-API-Key": self.ALGOLIA_API_KEY,
            "X-Algolia-Application-Id": self.ALGOLIA_APP_ID,
            "Content-Type": "application/json",
            "Referer": "https://www.welcometothejungle.com/",
            "Origin": "https://www.welcometothejungle.com",
        }
        payload = {"query": query, "hitsPerPage": self.hits_per_page, "page": page}
        if filters:
            payload["filters"] = filters
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def _build_query(self, criteria: SearchCriteria) -> str:
        parts = list(criteria.keywords)
        if criteria.location and criteria.location.lower() != "france":
            parts.append(criteria.location)
        return " ".join(parts) if parts else ""

    def _build_filters(self, criteria: SearchCriteria) -> str:
        filters = []
        if criteria.contract_types:
            contract_filters = []
            for ct in criteria.contract_types:
                if ct in self.CONTRACT_FILTER_MAPPING:
                    contract_filters += [f"contract_type:{wttj}" for wttj in self.CONTRACT_FILTER_MAPPING[ct]]
            if contract_filters:
                filters.append(f"({' OR '.join(contract_filters)})")

        if criteria.workplace_types:
            if "remote" in criteria.workplace_types:
                filters.append("(remote:fulltime OR remote:partial)")
            elif "on_site" in criteria.workplace_types:
                filters.append("remote:no")

        return " AND ".join(filters) if filters else ""

    def _parse_hit(self, hit: dict) -> Optional[JobOffer]:
        try:
            job_id = hit.get("reference") or hit.get("objectID")
            if not job_id:
                return None

            title = hit.get("name", "").strip()
            if not title:
                return None

            org = hit.get("organization", {})
            company = org.get("name", "").strip()

            offices = hit.get("offices", [])
            if offices:
                office = offices[0]
                city = office.get("city", "")
                country = office.get("country", "")
                location = f"{city}, {country}" if city else country
            else:
                location = "France"

            org_slug = org.get("slug", "")
            job_slug = hit.get("slug", "")
            url = f"{self.base_url}/fr/companies/{org_slug}/jobs/{job_slug}" if org_slug and job_slug else ""

            posted_at = None
            published = hit.get("published_at")
            if published:
                try:
                    posted_at = datetime.fromisoformat(published.replace("Z", "+00:00"))
                except ValueError:
                    pass

            return JobOffer(
                id=f"wttj_{job_id}",
                source=self.name,
                url=url,
                title=title,
                company=company or "Non spécifié",
                location=location or "France",
                posted_at=posted_at,
            )
        except Exception:
            return None

def search_jobs(
    keywords: list[str],
    location: str = "France",
    contract_types: list[str] = None,
    workplace_types: list[str] = None
) -> list[str]:
    max_results = int(os.getenv("JOB_SEARCHES", "5"))
    scraper = WTTJScraper()
    criteria = SearchCriteria(
        keywords=keywords,
        location=location,
        contract_types=contract_types or [],
        workplace_types=workplace_types or [],
        max_results=max_results
    )
    return [job.url for job in scraper.search(criteria)]