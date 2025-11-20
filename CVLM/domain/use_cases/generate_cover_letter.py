"""
Use Case: Génération d'une lettre de motivation en PDF
Orchestre toute la logique métier avec gestion transactionnelle
"""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Tuple

from domain.entities.cv import Cv
from domain.entities.user import User
from domain.entities.motivational_letter import MotivationalLetter
from domain.ports.cv_repository import CvRepository
from domain.ports.user_repository import UserRepository
from domain.ports.motivational_letter_repository import MotivationalLetterRepository
from domain.ports.generation_history_repository import GenerationHistoryRepository
from domain.services.cv_validation_service import CvValidationService
from domain.services.credit_service import CreditService
from domain.services.letter_generation_service import LetterGenerationService
from domain.services.generation_history_service import GenerationHistoryService
from domain.exceptions import InsufficientCreditsError, ResourceNotFoundError
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)


@dataclass
class GenerateCoverLetterInput:
    """Input du use case"""
    user_id: str
    cv_id: str
    job_url: str
    llm_provider: str = "openai"
    pdf_generator: str = "fpdf"


@dataclass
class GenerateCoverLetterOutput:
    """Output du use case"""
    letter_id: str
    pdf_path: str
    letter_text: str
    download_url: str
    credits_remaining: int


class GenerateCoverLetterUseCase:
    """
    Use Case: Génère une lettre de motivation PDF
    
    Responsabilités:
    1. Valider le CV et l'accès utilisateur
    2. Vérifier les crédits (avec gestion transactionnelle)
    3. Orchestrer la génération (LLM + PDF)
    4. Sauvegarder la lettre en base
    5. Enregistrer dans l'historique
    6. Décompter les crédits SEULEMENT si tout réussit
    """
    
    def __init__(
        self,
        cv_validation_service: CvValidationService,
        credit_service: CreditService,
        letter_generation_service: LetterGenerationService,
        history_service: GenerationHistoryService,
        letter_repository: MotivationalLetterRepository,
        user_repository: UserRepository
    ):
        self.cv_validation = cv_validation_service
        self.credit_service = credit_service
        self.letter_service = letter_generation_service
        self.history_service = history_service
        self.letter_repo = letter_repository
        self.user_repo = user_repository
    
    def execute(
        self,
        input_data: GenerateCoverLetterInput,
        current_user: User
    ) -> GenerateCoverLetterOutput:
        """
        Exécute le use case avec gestion transactionnelle
        
        Stratégie:
        1. Vérifier AVANT (CV existe, crédits suffisants)
        2. Générer (LLM + PDF)
        3. Sauvegarder (DB + historique)
        4. Décompter crédits SEULEMENT si 1-3 réussissent
        
        Raises:
            ResourceNotFoundError: CV introuvable ou accès refusé
            InsufficientCreditsError: Pas assez de crédits
            Exception: Erreur de génération
        """
        letter_id = None
        pdf_path = None
        
        try:
            # === PHASE 1: VALIDATION (pas de side effect) ===
            logger.info(f"[Use Case] Génération lettre pour user={current_user.email}, cv={input_data.cv_id}")
            
            # 1.1 Valider le CV et l'accès
            cv = self.cv_validation.get_and_validate_cv(input_data.cv_id, current_user)
            logger.debug(f"[Use Case] CV validé: {cv.filename}")
            
            # 1.2 Vérifier les crédits (SANS décompter encore)
            if not self.credit_service.has_credits(current_user, credit_type="pdf"):
                logger.warning(f"[Use Case] Crédits insuffisants pour {current_user.email}")
                raise InsufficientCreditsError(
                    f"Crédits PDF insuffisants. Crédits restants: {current_user.pdf_credits}"
                )
            
            logger.debug(f"[Use Case] Crédits suffisants: {current_user.pdf_credits} PDF restants")
            
            # === PHASE 2: GÉNÉRATION (création de fichier) ===
            logger.info(f"[Use Case] Démarrage génération avec {input_data.llm_provider}")
            
            letter_id, pdf_path, letter_text = self.letter_service.generate_letter_pdf(
                cv=cv,
                job_url=input_data.job_url,
                llm_provider=input_data.llm_provider,
                pdf_generator=input_data.pdf_generator,
                user=current_user
            )
            
            logger.info(f"[Use Case] Lettre générée: {letter_id}, taille: {len(letter_text)} chars")
            
            # === PHASE 3: SAUVEGARDE (transaction DB) ===
            
            # 3.1 Créer l'entité MotivationalLetter
            letter_entity = self.letter_service.save_letter_to_storage(
                letter_id=letter_id,
                pdf_path=pdf_path,
                cv_id=input_data.cv_id,
                job_url=input_data.job_url,
                letter_text=letter_text,
                llm_provider=input_data.llm_provider,
                user=current_user
            )
            
            # 3.2 Sauvegarder en DB
            saved_letter = self.letter_repo.create(letter_entity)
            logger.debug(f"[Use Case] Lettre sauvegardée en DB: {saved_letter.id}")
            
            # 3.3 Enregistrer dans l'historique
            company_name, job_title = self._extract_job_info(input_data.job_url)
            
            self.history_service.record_generation(
                user_id=current_user.id,
                gen_type='pdf',
                job_title=job_title,
                company_name=company_name,
                job_url=input_data.job_url,
                cv_filename=cv.filename,
                cv_id=input_data.cv_id,
                file_path=pdf_path,
                status='success'
            )
            
            logger.debug(f"[Use Case] Historique enregistré pour {current_user.email}")
            
            # === PHASE 4: DÉCOMPTE CRÉDITS (seulement si tout a réussi) ===
            self.credit_service.check_and_use_pdf_credit(current_user)
            
            # Recharger l'utilisateur pour avoir les crédits à jour
            updated_user = self.user_repo.get_by_id(current_user.id)
            
            logger.info(
                f"[Use Case] ✅ Génération réussie: letter={letter_id}, "
                f"crédits restants={updated_user.pdf_credits}"
            )
            
            # === SUCCÈS: Retourner le résultat ===
            return GenerateCoverLetterOutput(
                letter_id=saved_letter.id,
                pdf_path=pdf_path,
                letter_text=letter_text,
                download_url=f"/download-letter/{saved_letter.id}",
                credits_remaining=updated_user.pdf_credits
            )
            
        except InsufficientCreditsError:
            # Erreur attendue, on la propage
            raise
            
        except ResourceNotFoundError:
            # Erreur attendue, on la propage
            raise
            
        except Exception as e:
            # Erreur inattendue: on log et on nettoie
            logger.error(f"[Use Case] ❌ Erreur génération: {str(e)}", exc_info=True)
            
            # Nettoyage: supprimer le fichier PDF si créé
            if pdf_path and Path(pdf_path).exists():
                try:
                    Path(pdf_path).unlink()
                    logger.debug(f"[Use Case] Fichier PDF nettoyé: {pdf_path}")
                except Exception as cleanup_error:
                    logger.warning(f"[Use Case] Erreur nettoyage PDF: {cleanup_error}")
            
            # Enregistrer l'échec dans l'historique
            if letter_id:
                try:
                    company_name, job_title = self._extract_job_info(input_data.job_url)
                    
                    self.history_service.record_generation(
                        user_id=current_user.id,
                        gen_type='pdf',
                        job_title=job_title,
                        company_name=company_name,
                        job_url=input_data.job_url,
                        cv_filename=cv.filename if cv else None,
                        cv_id=input_data.cv_id,
                        file_path=None,
                        status='failed',
                        error_message=str(e)
                    )
                except Exception as history_error:
                    logger.warning(f"[Use Case] Erreur enregistrement historique échec: {history_error}")
            
            # Propager l'erreur
            raise Exception(f"Erreur lors de la génération de la lettre: {str(e)}") from e
    
    def _extract_job_info(self, job_url: str) -> Tuple[str, str]:
        """
        Extrait le nom de l'entreprise et le titre du poste depuis l'URL
        
        Returns:
            Tuple (company_name, job_title)
        """
        company_name = None
        job_title = None
        
        try:
            if 'welcometothejungle' in job_url.lower():
                parts = job_url.split('/')
                if len(parts) >= 6:
                    company_name = parts[4].replace('-', ' ').title()
                    job_title = parts[6].split('?')[0].replace('-', ' ').title()
        except Exception as e:
            logger.debug(f"[Use Case] Erreur extraction infos job: {e}")
        
        return company_name, job_title
