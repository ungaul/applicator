import os
from datetime import datetime
from typing import Iterator, Optional
from dataclasses import dataclass

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
    country: str = "fr"
    radius_km: Optional[int] = None
    max_results: int = 5


class AdzunaScraper:
    base_url = "https://api.adzuna.com/v1/api/jobs"
    name = "adzuna"

    def __init__(self):
        self.app_id = os.getenv("ADZUNA_APP_ID")
        self.app_key = os.getenv("ADZUNA_APP_KEY")
        if not self.app_id or not self.app_key:
            raise ValueError("Missing ADZUNA_APP_ID or ADZUNA_APP_KEY")

    def search(self, criteria: SearchCriteria) -> Iterator[JobOffer]:
        page = 1
        jobs_found = 0
        seen_ids = set()
        results_per_page = 50

        while jobs_found < criteria.max_results:
            url = self._build_search_url(criteria, page, results_per_page)
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            if not results:
                break

            for result in results:
                if jobs_found >= criteria.max_results:
                    break

                job = self._parse_result(result)
                if job and job.id not in seen_ids:
                    seen_ids.add(job.id)
                    jobs_found += 1
                    yield job

            total_count = data.get("count", 0)
            if page * results_per_page >= total_count:
                break
            page += 1

    def _build_search_url(self, criteria: SearchCriteria, page: int, results_per_page: int) -> str:
        base = f"{self.base_url}/{criteria.country}/search/{page}"
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": min(results_per_page, 50),
            "content-type": "application/json",
        }
        if criteria.keywords:
            params["what"] = " ".join(criteria.keywords)
        if criteria.location and criteria.location != "France":
            params["where"] = criteria.location
        if criteria.radius_km:
            params["distance"] = criteria.radius_km

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base}?{query_string}"

    def _parse_result(self, result: dict) -> Optional[JobOffer]:
        job_id = result.get("id")
        if not job_id:
            return None
        try:
            posted_at = None
            if created := result.get("created"):
                posted_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
            return JobOffer(
                id=f"adzuna_{job_id}",
                source=self.name,
                url=result.get("redirect_url"),
                title=result.get("title", "").strip(),
                company=result.get("company", {}).get("display_name", "").strip(),
                location=result.get("location", {}).get("display_name", "").strip() or "France",
                posted_at=posted_at,
            )
        except Exception:
            return None


def search_jobs(keywords: list[str], location: str = "France", country: str = "fr", radius_km: int = None) -> list[str]:
    max_results = int(os.getenv("JOB_SEARCHES", "5"))
    scraper = AdzunaScraper()
    criteria = SearchCriteria(
        keywords=keywords,
        location=location,
        country=country,
        radius_km=radius_km,
        max_results=max_results
    )
    return [job.url for job in scraper.search(criteria)]