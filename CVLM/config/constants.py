"""
Constantes de l'application CVLM
"""
from pathlib import Path
import os

# Credits
DEFAULT_PDF_CREDITS = 10
DEFAULT_TEXT_CREDITS = 10

# File Upload Validation
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_TYPES = ["application/pdf"]
ALLOWED_FILE_EXTENSIONS = [".pdf"]

# Pagination
HISTORY_PAGINATION_DEFAULT = 50
HISTORY_PAGINATION_MAX = 100

# File Storage
FILE_STORAGE_BASE_PATH = os.getenv("FILE_STORAGE_BASE_PATH", "data/files")
TEMP_DIR = Path("data/temp")
OUTPUT_DIR = Path("data/output")

# LLM Providers
LLM_PROVIDER_OPENAI = "openai"
LLM_PROVIDER_GEMINI = "gemini"

# PDF Generators
PDF_GENERATOR_FPDF = "fpdf"
PDF_GENERATOR_WEASYPRINT = "weasyprint"

# Text Generation Types
TEXT_TYPE_WHY_JOIN = "why_join"

# Error Messages
ERROR_NO_PDF_CREDITS = f"Crédits PDF épuisés. Vous avez utilisé vos {DEFAULT_PDF_CREDITS} générations PDF gratuites."
ERROR_NO_TEXT_CREDITS = f"Crédits texte épuisés. Vous avez utilisé vos {DEFAULT_TEXT_CREDITS} générations de texte gratuites."
ERROR_CV_NOT_FOUND = "CV non trouvé"
ERROR_CV_FILE_NOT_FOUND = "Fichier CV introuvable"
ERROR_CV_ACCESS_DENIED = "Accès interdit à ce CV"
ERROR_LETTER_NOT_FOUND = "Lettre non trouvée"
ERROR_LETTER_ACCESS_DENIED = "Accès interdit à cette lettre"
ERROR_FILE_TOO_LARGE = f"Fichier trop volumineux. Taille maximale: {MAX_FILE_SIZE // (1024 * 1024)} MB"
ERROR_INVALID_FILE_TYPE = f"Type de fichier invalide. Types acceptés: {', '.join(ALLOWED_FILE_EXTENSIONS)}"

# CORS Origins
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://www.welcometothejungle.com",
    "https://www.linkedin.com",
    "https://www.indeed.fr",
]

# Add production domain if defined
PRODUCTION_DOMAIN = os.getenv("PRODUCTION_DOMAIN")
if PRODUCTION_DOMAIN:
    CORS_ALLOWED_ORIGINS.append(f"https://{PRODUCTION_DOMAIN}")

CORS_ORIGIN_REGEX = r"chrome-extension://.*"
