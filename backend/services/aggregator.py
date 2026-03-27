import asyncio
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from models import SearchCriteria

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scrapers'))

from francetravail import FranceTravailScraper
from hellowork import HelloWorkScraper
from linkedin import LinkedInScraper
from wttj import WTTJScraper
from adzuna import AdzunaScraper

SCRAPERS = {
    "francetravail": FranceTravailScraper,
    "hellowork": HelloWorkScraper,
    "linkedin": LinkedInScraper,
    "wttj": WTTJScraper,
    "adzuna": AdzunaScraper,
}

_executor = ThreadPoolExecutor(max_workers=5)


def _job_to_dict(job) -> dict:
    return job.to_dict() if hasattr(job, "to_dict") else {
        "id": job.id,
        "source": job.source,
        "url": job.url,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "posted_at": job.posted_at.isoformat() if job.posted_at else None,
        "contract_type": None,
        "salary": None,
        "remote": None,
        "description": None,
    }


def _run_scraper(scraper_name: str, criteria: SearchCriteria) -> list[dict]:
    try:
        os.environ["JOB_SEARCHES"] = str(criteria.max_results)
        scraper = SCRAPERS[scraper_name]()
        import dataclasses
        sc_fields = {f.name for f in dataclasses.fields(criteria)}
        sc = SearchCriteria(
            keywords=criteria.keywords,
            location=criteria.location,
            country=criteria.country,
            radius_km=criteria.radius_km,
            contract_types=criteria.contract_types,
            experience_levels=criteria.experience_levels,
            workplace_types=criteria.workplace_types,
            date_posted=criteria.date_posted,
            max_results=criteria.max_results,
        )

        results = []
        for job in scraper.search(sc):
            results.append(_job_to_dict(job))
        return results

    except Exception as e:
        print(f"[{scraper_name}] error: {e}")
        return []


async def aggregate_jobs(
    keywords: list[str],
    location: str = "France",
    country: str = "fr",
    radius_km: Optional[int] = None,
    contract_types: list[str] = None,
    experience_levels: list[str] = None,
    workplace_types: list[str] = None,
    date_posted: Optional[str] = None,
    sources: list[str] = None,
    max_results: int = 10,
) -> list[dict]:
    active_sources = sources if sources else list(SCRAPERS.keys())

    criteria = SearchCriteria(
        keywords=keywords,
        location=location,
        country=country,
        radius_km=radius_km,
        contract_types=contract_types or [],
        experience_levels=experience_levels or [],
        workplace_types=workplace_types or [],
        date_posted=date_posted,
        max_results=max_results,
    )

    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(_executor, _run_scraper, source, criteria)
        for source in active_sources
        if source in SCRAPERS
    ]

    results_per_source = await asyncio.gather(*tasks, return_exceptions=True)

    seen_urls = set()
    all_jobs = []
    for batch in results_per_source:
        if isinstance(batch, Exception):
            continue
        for job in batch:
            url = job.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_jobs.append(job)

    return all_jobs
