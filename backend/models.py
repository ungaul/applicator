from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class JobOffer:
    id: str
    source: str
    url: str
    title: str
    company: str
    location: str
    posted_at: Optional[datetime] = None
    contract_type: Optional[str] = None
    salary: Optional[str] = None
    remote: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "url": self.url,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
            "contract_type": self.contract_type,
            "salary": self.salary,
            "remote": self.remote,
            "description": self.description,
        }


@dataclass
class SearchCriteria:
    keywords: list[str]
    location: str = "France"
    country: str = "fr"
    radius_km: Optional[int] = None
    contract_types: list[str] = field(default_factory=list)
    experience_levels: list[str] = field(default_factory=list)
    workplace_types: list[str] = field(default_factory=list)
    date_posted: Optional[str] = None
    sources: list[str] = field(default_factory=list)
    max_results: int = 5
