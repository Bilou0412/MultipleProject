"""
Modèles Pydantic pour l'administration
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PromoCodeGenerateRequest(BaseModel):
    code: str
    pdf_credits: int
    text_credits: int
    max_uses: int = 0
    expires_at: Optional[datetime] = None


class PromoCodeResponse(BaseModel):
    code: str
    pdf_credits: int
    text_credits: int
    max_uses: int
    current_uses: int
    is_active: bool
    created_at: str
    expires_at: Optional[str] = None


class PromoCodeRedeemRequest(BaseModel):
    code: str


class PromoCodeRedeemResponse(BaseModel):
    status: str
    message: str
    pdf_credits_added: int
    text_credits_added: int
    new_pdf_credits: int
    new_text_credits: int


class UserUpdateCreditsRequest(BaseModel):
    user_id: str
    pdf_credits: int
    text_credits: int


class UserPromoteRequest(BaseModel):
    user_id: str


class DashboardStatsResponse(BaseModel):
    total_users: int
    total_promo_codes: int
    active_promo_codes: int
    total_generations: int
