import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.aggregator import aggregate_jobs
from services.fetcher import fetch_job_page

router = APIRouter()

class SearchRequest(BaseModel):
    keywords: list[str]
    location: str = "France"
    radius_km: Optional[int] = None
    contract_types: list[str] = []
    experience_levels: list[str] = []
    workplace_types: list[str] = []
    date_posted: Optional[str] = None
    sources: list[str] = []
    max_results: int = 10


class FetchRequest(BaseModel):
    url: str
    source: str


@router.post("/search")
async def search_jobs(req: SearchRequest):
    try:
        results = await aggregate_jobs(
            keywords=req.keywords,
            location=req.location,
            radius_km=req.radius_km,
            contract_types=req.contract_types,
            experience_levels=req.experience_levels,
            workplace_types=req.workplace_types,
            date_posted=req.date_posted,
            sources=req.sources,
            max_results=req.max_results,
        )
        return {"jobs": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch")
async def fetch_job(req: FetchRequest):
    try:
        data = await fetch_job_page(req.url, req.source)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
