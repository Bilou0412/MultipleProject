"""
Routes de génération de lettres de motivation et textes
Endpoints: /generate-cover-letter, /generate-text, /list-letters
"""

from fastapi import APIRouter, Depends, Form, HTTPException

from api.dependencies import (
    get_current_user,
    get_letter_repository,
    get_cv_repository,
    get_generate_cover_letter_use_case,
    get_generate_text_use_case
)
from api.models.generation import GenerationResponse, TextGenerationRequest, TextGenerationResponse
from domain.entities.user import User
from domain.use_cases.generate_cover_letter import (
    GenerateCoverLetterUseCase,
    GenerateCoverLetterInput
)
from domain.use_cases.generate_text import GenerateTextUseCase
from infrastructure.adapters.postgres_motivational_letter_repository import PostgresMotivationalLetterRepository
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
    use_case: GenerateCoverLetterUseCase = Depends(get_generate_cover_letter_use_case)
):
    """
    Génère une lettre de motivation en PDF à partir d'un CV et d'une offre d'emploi.
    
    Args:
        cv_id: ID du CV à utiliser
        job_url: URL de l'offre d'emploi (Welcome to the Jungle)
        llm_provider: Fournisseur LLM (openai ou gemini)
        pdf_generator: Générateur PDF (fpdf ou weasyprint)
        current_user: Utilisateur connecté (injecté)
        use_case: Use case de génération (injecté)
    
    Returns:
        GenerationResponse avec file_id, download_url et letter_text
    
    Raises:
        HTTPException 403: Crédits insuffisants
        HTTPException 404: CV introuvable
        HTTPException 500: Erreur de génération
    """
    try:
        # Créer l'input du use case
        input_data = GenerateCoverLetterInput(
            user_id=current_user.id,
            cv_id=cv_id,
            job_url=job_url,
            llm_provider=llm_provider,
            pdf_generator=pdf_generator
        )
        
        # Exécuter le use case (orchestration complète)
        output = use_case.execute(input_data, current_user)
        
        # Retourner la réponse
        return GenerationResponse(
            status="success",
            file_id=output.letter_id,
            download_url=output.download_url,
            letter_text=output.letter_text
        )
        
    except HTTPException:
        # HTTPException déjà formatée, on la propage
        raise
    except Exception as e:
        logger.error(f"Erreur génération lettre: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération: {str(e)}"
        )


@router.post("/generate-text", response_model=TextGenerationResponse)
async def generate_text(
    data: TextGenerationRequest,
    current_user: User = Depends(get_current_user),
    use_case: GenerateTextUseCase = Depends(get_generate_text_use_case)
):
    """
    Génère un texte de motivation personnalisé sans PDF.
    
    Args:
        data: Requête avec cv_id, job_url, text_type, llm_provider
        current_user: Utilisateur connecté (injecté)
        use_case: Use Case de génération texte (injecté)
    
    Returns:
        TextGenerationResponse avec le texte généré
    
    Raises:
        HTTPException 400: CV non sélectionné ou invalide
        HTTPException 403: Crédits insuffisants
        HTTPException 500: Erreur de génération
    """
    try:
        # Préparer l'input du use case
        from domain.use_cases.generate_text import GenerateTextInput
        
        input_data = GenerateTextInput(
            cv_id=data.cv_id,
            job_url=data.job_url,
            text_type=data.text_type,
            llm_provider=data.llm_provider
        )
        
        # Exécuter le use case
        output = use_case.execute(input_data, current_user)
        
        return TextGenerationResponse(status="success", text=output.text)
        
    except ValueError as e:
        # Erreur de validation (CV, etc.)
        logger.error(f"Erreur validation génération texte: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # Erreur métier (crédits, génération, etc.)
        logger.error(f"Erreur métier génération texte: {e}")
        # Déterminer le status code selon le message
        if "crédit" in str(e).lower() or "insufficient" in str(e).lower():
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur génération texte: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list-letters")
async def list_letters(
    current_user: User = Depends(get_current_user),
    letter_repo: PostgresMotivationalLetterRepository = Depends(get_letter_repository),
    cv_repo = Depends(get_cv_repository)
):
    """
    Liste toutes les lettres générées par l'utilisateur.
    
    Args:
        current_user: Utilisateur connecté (injecté)
        letter_repo: Repository lettres (injecté)
        cv_repo: Repository CVs (injecté)
    
    Returns:
        Liste des lettres avec metadata (letter_id, filename, cv_filename, etc.)
    """
    try:
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
