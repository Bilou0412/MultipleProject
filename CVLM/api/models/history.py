"""
Modèles Pydantic pour l'historique
"""
from pydantic import BaseModel
from typing import Optional, List


class HistoryEntryResponse(BaseModel):
    id: str
    type: str
    job_title: Optional[str]
    company_name: Optional[str]
    job_url: Optional[str]
    cv_filename: Optional[str]
    status: str
    created_at: str
    is_downloadable: bool
    is_expired: bool
    days_until_expiration: Optional[int]


class HistoryListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: List[HistoryEntryResponse]


class HistoryStatsResponse(BaseModel):
    total: int
    pdf_count: int
    text_count: int
    success_rate: float
    this_month: int
    last_generation: Optional[str]
    unique_companies: int


class HistoryTextResponse(BaseModel):
    id: str
    text_content: str
    job_title: Optional[str]
    company_name: Optional[str]
    created_at: str
