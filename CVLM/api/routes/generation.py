"""
Routes de génération de lettres de motivation et textes
Endpoints: /generate-cover-letter, /generate-text, /list-letters
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from api.models.generation import GenerationResponse, TextGenerationRequest, TextGenerationResponse
from domain.entities.user import User
from domain.services.cv_validation_service import CvValidationService
from domain.services.credit_service import CreditService
from domain.services.letter_generation_service import LetterGenerationService
from infrastructure.adapters.postgres_cv_repository import PostgresCvRepository
from infrastructure.adapters.postgres_motivational_letter_repository import PostgresMotivationalLetterRepository
from infrastructure.adapters.postgres_user_repository import PostgresUserRepository
from infrastructure.adapters.pypdf_parse import PyPdfParser
from infrastructure.adapters.welcome_to_jungle_scraper import WelcomeToTheJungleFetcher
from infrastructure.adapters.open_ai_api import OpenAiLlm
from infrastructure.adapters.google_gemini_api import GoogleGeminiLlm
from config.constants import LLM_PROVIDER_GEMINI, TEXT_TYPE_WHY_JOIN
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)


router = APIRouter(prefix="", tags=["generation"])


@router.post("/generate-cover-letter", response_model=GenerationResponse)
async def generate_cover_letter(
    cv_id: str = Form(...),
    job_url: str = Form(...),
    llm_provider: str = Form("openai"),
    pdf_generator: str = Form("fpdf"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Génère une lettre de motivation en PDF à partir d'un CV et d'une offre d'emploi.
    
    Args:
        cv_id: ID du CV à utiliser
        job_url: URL de l'offre d'emploi (Welcome to the Jungle)
        llm_provider: Fournisseur LLM (openai ou gemini)
        pdf_generator: Générateur PDF (fpdf ou weasyprint)
        current_user: Utilisateur connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        GenerationResponse avec file_id, download_url et letter_text
    
    Raises:
        HTTPException 403: Crédits insuffisants
        HTTPException 404: CV introuvable
        HTTPException 500: Erreur de génération
    """
    try:
        # Services
        cv_validation_service = CvValidationService(PostgresCvRepository(db))
        credit_service = CreditService(PostgresUserRepository(db))
        letter_service = LetterGenerationService()
        
        # Valider le CV
        cv = cv_validation_service.get_and_validate_cv(cv_id, current_user)
        
        # Vérifier et utiliser un crédit (lève InsufficientCreditsError si pas de crédit)
        credit_service.check_and_use_pdf_credit(current_user)
        
        # Générer la lettre
        letter_id, pdf_path, letter_text = letter_service.generate_letter_pdf(
            cv=cv,
            job_url=job_url,
            llm_provider=llm_provider,
            pdf_generator=pdf_generator,
            user=current_user
        )
        
        # Sauvegarder en base de données
        try:
            letter = letter_service.save_letter_to_storage(
                letter_id=letter_id,
                pdf_path=pdf_path,
                cv_id=cv_id,
                job_url=job_url,
                letter_text=letter_text,
                llm_provider=llm_provider,
                user=current_user
            )
            
            letter_repo = PostgresMotivationalLetterRepository(db)
            letter_repo.create(letter)
            
        except Exception as e:
            logger.warning(f"Erreur sauvegarde lettre en base: {e}")
        
        # Enregistrer dans l'historique
        try:
            from infrastructure.adapters.postgres_generation_history_repository import PostgresGenerationHistoryRepository
            from domain.services.generation_history_service import GenerationHistoryService
            
            history_repo = PostgresGenerationHistoryRepository(db)
            history_service = GenerationHistoryService(history_repo)
            
            # Extraire les infos de l'offre (simple parsing du job_url)
            company_name = None
            job_title = None
            try:
                if 'welcometothejungle' in job_url:
                    parts = job_url.split('/')
                    if len(parts) >= 6:
                        company_name = parts[4].replace('-', ' ').title()
                        job_title = parts[6].split('?')[0].replace('-', ' ').title()
            except Exception:
                pass
            
            history_service.record_generation(
                user_id=current_user.id,
                gen_type='pdf',
                job_title=job_title,
                company_name=company_name,
                job_url=job_url,
                cv_filename=cv.filename,
                cv_id=cv_id,
                file_path=pdf_path,
                status='success'
            )
            
        except Exception as e:
            logger.warning(f"Erreur enregistrement historique: {e}")
        
        return GenerationResponse(
            status="success",
            file_id=letter_id,
            download_url=f"/download-letter/{letter_id}",
            letter_text=letter_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur génération lettre: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération: {str(e)}")


@router.post("/generate-text", response_model=TextGenerationResponse)
async def generate_text(
    data: TextGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Génère un texte de motivation personnalisé sans PDF.
    
    Args:
        data: Requête avec cv_id, job_url, text_type, llm_provider
        current_user: Utilisateur connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        TextGenerationResponse avec le texte généré
    
    Raises:
        HTTPException 400: CV non sélectionné
        HTTPException 403: Crédits insuffisants
        HTTPException 500: Erreur de génération
    """
    try:
        # Validation
        if not data.cv_id:
            raise HTTPException(
                status_code=400,
                detail="Aucun CV sélectionné. Veuillez d'abord télécharger et sélectionner un CV."
            )
        
        # Services
        cv_validation_service = CvValidationService(PostgresCvRepository(db))
        credit_service = CreditService(PostgresUserRepository(db))
        
        # Valider le CV et vérifier crédit
        cv = cv_validation_service.get_and_validate_cv(data.cv_id, current_user)
        credit_service.check_and_use_text_credit(current_user)
        
        # Parser et fetcher
        document_parser = PyPdfParser()
        job_fetcher = WelcomeToTheJungleFetcher()
        llm = GoogleGeminiLlm() if data.llm_provider.lower() == LLM_PROVIDER_GEMINI else OpenAiLlm()
        
        cv_text = document_parser.parse_document(input_path=str(cv.file_path))
        
        job_offer_text = ""
        try:
            job_offer_text = job_fetcher.fetch(url=data.job_url)
        except Exception as e:
            logger.warning(f"Erreur fetch offre d'emploi: {e}")
        
        # Créer le prompt
        prompt = _build_text_generation_prompt(cv_text, job_offer_text, data.text_type)
        
        # Générer
        generated_text = llm.send_to_llm(prompt)
        logger.info(f"Texte généré pour {current_user.email}")
        
        # Enregistrer dans l'historique
        try:
            from infrastructure.adapters.postgres_generation_history_repository import PostgresGenerationHistoryRepository
            from domain.services.generation_history_service import GenerationHistoryService
            
            history_repo = PostgresGenerationHistoryRepository(db)
            history_service = GenerationHistoryService(history_repo)
            
            # Extraire les infos de l'offre
            company_name = None
            job_title = None
            try:
                if 'welcometothejungle' in data.job_url:
                    parts = data.job_url.split('/')
                    if len(parts) >= 6:
                        company_name = parts[4].replace('-', ' ').title()
                        job_title = parts[6].split('?')[0].replace('-', ' ').title()
            except Exception:
                pass
            
            history_service.record_generation(
                user_id=current_user.id,
                gen_type='text',
                job_title=job_title,
                company_name=company_name,
                job_url=data.job_url,
                cv_filename=cv.filename,
                cv_id=data.cv_id,
                text_content=generated_text,
                status='success'
            )
            
        except Exception as e:
            logger.warning(f"Erreur enregistrement historique: {e}")
        
        return TextGenerationResponse(status="success", text=generated_text)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur génération texte: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list-letters")
async def list_letters(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Liste toutes les lettres générées par l'utilisateur.
    
    Args:
        current_user: Utilisateur connecté (injecté)
        db: Session de base de données (injectée)
    
    Returns:
        Liste des lettres avec metadata (letter_id, filename, cv_filename, etc.)
    """
    try:
        letter_repo = PostgresMotivationalLetterRepository(db)
        cv_repo = PostgresCvRepository(db)
        
        # Récupérer toutes les lettres de l'utilisateur
        letters = letter_repo.get_by_user_id(current_user.id)
        
        letter_infos = []
        for letter in letters:
            # Récupérer le CV associé
            cv = cv_repo.get_by_id(letter.cv_id) if letter.cv_id else None
            
            letter_infos.append({
                "letter_id": letter.id,
                "filename": letter.filename or "lettre_motivation.pdf",
                "cv_filename": cv.filename if cv else "CV supprimé",
                "job_offer_url": letter.job_offer_url or "",
                "created_at": letter.created_at.isoformat(),
                "file_size": letter.file_size,
                "llm_provider": letter.llm_provider
            })
        
        # Trier par date décroissante (plus récent en premier)
        letter_infos.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "status": "success",
            "letters": letter_infos,
            "total": len(letter_infos)
        }
    except Exception as e:
        logger.error(f"Erreur liste lettres: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des lettres: {str(e)}")


def _build_text_generation_prompt(cv_text: str, job_offer_text: str, text_type: str) -> str:
    """
    Construit le prompt pour la génération de texte.
    
    Args:
        cv_text: Contenu du CV extrait
        job_offer_text: Contenu de l'offre d'emploi
        text_type: Type de texte à générer (why_join, etc.)
    
    Returns:
        Prompt formaté pour le LLM
    """
    if text_type == TEXT_TYPE_WHY_JOIN:
        return (
            f"Vous êtes un assistant expert en communication RH.\n\n"
            f"Contexte (CV) :\n{cv_text}\n\n"
            f"Offre d'emploi :\n{job_offer_text}\n\n"
            f"Tâche : Rédigez une réponse concise (3-6 phrases) à la question : "
            f"'Expliquez-nous pourquoi vous souhaitez nous rejoindre.' "
            f"Utilisez un ton professionnel et motivé. Ne fournissez que le texte de la réponse, "
            f"sans préambule ni signature."
        )
    return (
        f"Vous êtes un assistant expert.\n\n"
        f"Contexte (CV) :\n{cv_text}\n\n"
        f"Offre d'emploi :\n{job_offer_text}\n\n"
        f"Tâche : Rédigez un court paragraphe adapté à l'offre."
    )
