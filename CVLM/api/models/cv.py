"""
Modèles Pydantic pour les CVs
"""
from pydantic import BaseModel
from typing import List


class CvInfo(BaseModel):
    cv_id: str
    filename: str
    upload_date: str
    file_size: int


class UploadResponse(BaseModel):
    status: str
    cv_id: str
    filename: str


class CvListResponse(BaseModel):
    status: str
    cvs: List[CvInfo]
