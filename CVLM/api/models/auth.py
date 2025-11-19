"""
Modèles Pydantic pour l'authentification
"""
from pydantic import BaseModel
from typing import Optional


class AuthTokenRequest(BaseModel):
    token: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str]
    pdf_credits: int
    text_credits: int
    is_admin: bool
    created_at: str
