"""
Use Case: Génération de texte de motivation personnalisé

Ce use case orchestre le workflow complet de génération d'un texte de motivation
sans PDF, avec gestion transactionnelle des crédits.

Architecture: Hexagonal (Use Case Pattern)
Author: System
Date: 2025-11-20
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from domain.entities.user import User
from domain.services.use_case_validator import UseCaseValidator
from domain.services.job_info_extractor import JobInfoExtractor
from domain.services.credit_service import CreditService
from domain.services.generation_history_service import GenerationHistoryService
from domain.ports.document_parser import DocumentParser
from domain.ports.job_offer_fetcher import JobOfferFetcher
from domain.ports.llm_service import LlmService
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)


# ==================== INPUT/OUTPUT DATA CLASSES ====================

@dataclass
class GenerateTextInput:
    """Données d'entrée pour la génération de texte."""
    cv_id: int
    job_url: str
    text_type: str  # 'why_join', etc.
    llm_provider: str  # 'gemini' ou 'openai'


@dataclass
class GenerateTextOutput:
    """Résultat de la génération de texte."""
    text: str
    cv_filename: str
    job_url: str


# ==================== USE CASE ====================

class GenerateTextUseCase:
    """
    Use Case: Génération de texte de motivation personnalisé.
    
    Responsabilités:
    - Validation du CV et des crédits utilisateur
    - Extraction du contenu CV et récupération de l'offre d'emploi
    - Génération du texte via LLM
    - Enregistrement dans l'historique
    - Décompte des crédits (UNIQUEMENT si succès complet)
    
    Gestion transactionnelle:
    - Vérification crédits AVANT génération
    - Décompte crédits APRÈS génération réussie
    - Pas de perte de crédit en cas d'erreur
    
    Pattern: Use Case orchestrant plusieurs services domain
    """
    
    def __init__(
        self,
        use_case_validator: UseCaseValidator,
        job_info_extractor: JobInfoExtractor,
        credit_service: CreditService,
        history_service: GenerationHistoryService,
        document_parser: DocumentParser,
        job_offer_fetcher: JobOfferFetcher,
        llm_service_factory,  # Factory function to create LLM service based on provider
    ):
        """
        Initialise le use case avec ses dépendances injectées.
        
        Args:
            use_case_validator: Helper pour validation CV + crédits
            job_info_extractor: Helper pour extraction infos job depuis URL
            credit_service: Service de gestion des crédits
            history_service: Service d'historique des générations
            document_parser: Parser pour extraire le contenu des CVs
            job_offer_fetcher: Fetcher pour récupérer les offres d'emploi
            llm_service_factory: Factory pour créer le service LLM selon le provider
        """
        self._validator = use_case_validator
        self._job_extractor = job_info_extractor
        self._credit_service = credit_service
        self._history_service = history_service
        self._document_parser = document_parser
        self._job_fetcher = job_offer_fetcher
        self._llm_factory = llm_service_factory
        
        logger.info("[Use Case] GenerateTextUseCase initialisé")
    
    def execute(self, input_data: GenerateTextInput, current_user: User) -> GenerateTextOutput:
        """
        Exécute le workflow complet de génération de texte.
        
        Workflow:
        1. Validation CV et crédits
        2. Extraction contenu CV
        3. Récupération offre d'emploi (best effort)
        4. Génération texte via LLM
        5. Enregistrement historique
        6. Décompte crédits (si tout OK)
        
        Args:
            input_data: Données d'entrée (cv_id, job_url, text_type, llm_provider)
            current_user: Utilisateur courant authentifié
        
        Returns:
            GenerateTextOutput avec le texte généré
        
        Raises:
            ValueError: Si cv_id manquant ou CV invalide
            RuntimeError: Si crédits insuffisants ou erreur génération
        """
        logger.info(f"[Use Case] Début génération texte pour utilisateur {current_user.email}")
        logger.info(f"[Use Case] Input: cv_id={input_data.cv_id}, job_url={input_data.job_url}, "
                   f"text_type={input_data.text_type}, llm={input_data.llm_provider}")
        
        try:
            # ==================== PHASE 1: VALIDATION ====================
            # Validation centralisée via helper
            cv = self._validator.validate_cv_and_credits(
                cv_id=input_data.cv_id,
                user=current_user,
                credit_type='text'
            )
            logger.info(f"[Use Case] ✓ Validation OK - CV: {cv.filename}")
            
            # ==================== PHASE 2: EXTRACTION CV ====================
            cv_text = self._extract_cv_content(cv.file_path)
            logger.info(f"[Use Case] ✓ CV extrait - {len(cv_text)} caractères")
            
            # ==================== PHASE 3: RÉCUPÉRATION OFFRE ====================
            job_offer_text = self._fetch_job_offer(input_data.job_url)
            logger.info(f"[Use Case] ✓ Offre récupérée - {len(job_offer_text)} caractères")
            
            # ==================== PHASE 4: GÉNÉRATION TEXTE ====================
            generated_text = self._generate_text(
                cv_text=cv_text,
                job_offer_text=job_offer_text,
                text_type=input_data.text_type,
                llm_provider=input_data.llm_provider
            )
            logger.info(f"[Use Case] ✓ Texte généré - {len(generated_text)} caractères")
            
            # ==================== PHASE 5: HISTORIQUE ====================
            self._record_history(
                user_id=current_user.id,
                cv_id=input_data.cv_id,
                cv_filename=cv.filename,
                job_url=input_data.job_url,
                text_content=generated_text,
                status='success'
            )
            logger.info(f"[Use Case] ✓ Historique enregistré")
            
            # ==================== PHASE 6: DÉCOMPTE CRÉDITS ====================
            # ⚠️ IMPORTANT: Décompter uniquement si TOUT a réussi
            self._credit_service.use_text_credit(current_user)
            logger.info(f"[Use Case] ✓ Crédit déduit - Crédits restants: {current_user.text_credits}")
            
            # ==================== SUCCÈS ====================
            logger.info(f"[Use Case] ✅ Génération texte réussie pour {current_user.email}")
            
            return GenerateTextOutput(
                text=generated_text,
                cv_filename=cv.filename,
                job_url=input_data.job_url
            )
            
        except ValueError as e:
            # Erreur de validation (CV, crédits, etc.)
            logger.error(f"[Use Case] ❌ Erreur validation: {e}")
            raise
        except RuntimeError as e:
            # Erreur métier
            logger.error(f"[Use Case] ❌ Erreur métier: {e}")
            raise
        except Exception as e:
            # Erreur technique inattendue
            logger.error(f"[Use Case] ❌ Erreur inattendue: {e}", exc_info=True)
            raise RuntimeError(f"Erreur lors de la génération du texte: {str(e)}")
    
    # ==================== MÉTHODES PRIVÉES ====================
    
    def _extract_cv_content(self, cv_path: Path) -> str:
        """
        Extrait le contenu textuel du CV.
        
        Args:
            cv_path: Chemin vers le fichier CV
        
        Returns:
            Contenu textuel du CV
        
        Raises:
            RuntimeError: Si erreur d'extraction
        """
        try:
            cv_text = self._document_parser.parse_document(input_path=str(cv_path))
            if not cv_text or not cv_text.strip():
                raise RuntimeError("Le CV ne contient pas de texte extractible")
            return cv_text
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'extraction du CV: {str(e)}")
    
    def _fetch_job_offer(self, job_url: str) -> str:
        """
        Récupère le contenu de l'offre d'emploi (best effort).
        
        Args:
            job_url: URL de l'offre d'emploi
        
        Returns:
            Contenu de l'offre d'emploi (chaîne vide si échec)
        """
        try:
            return self._job_fetcher.fetch(url=job_url)
        except Exception as e:
            logger.warning(f"[Use Case] ⚠️  Erreur fetch offre (non bloquant): {e}")
            return ""  # Best effort: continuer même si fetch échoue
    
    def _generate_text(
        self,
        cv_text: str,
        job_offer_text: str,
        text_type: str,
        llm_provider: str
    ) -> str:
        """
        Génère le texte de motivation via LLM.
        
        Args:
            cv_text: Contenu du CV
            job_offer_text: Contenu de l'offre d'emploi
            text_type: Type de texte à générer
            llm_provider: Provider LLM à utiliser
        
        Returns:
            Texte généré
        
        Raises:
            RuntimeError: Si erreur de génération
        """
        try:
            # Créer le service LLM via la factory
            llm_service = self._llm_factory(llm_provider)
            
            # Construire le prompt
            prompt = self._build_prompt(cv_text, job_offer_text, text_type)
            
            # Générer le texte
            generated_text = llm_service.send_to_llm(prompt)
            
            if not generated_text or not generated_text.strip():
                raise RuntimeError("Le LLM a retourné un texte vide")
            
            return generated_text
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la génération du texte: {str(e)}")
    
    def _build_prompt(self, cv_text: str, job_offer_text: str, text_type: str) -> str:
        """
        Construit le prompt pour le LLM selon le type de texte.
        
        Args:
            cv_text: Contenu du CV
            job_offer_text: Contenu de l'offre d'emploi
            text_type: Type de texte à générer
        
        Returns:
            Prompt formaté
        """
        if text_type == "why_join":
            return (
                f"Vous êtes un assistant expert en communication RH.\n\n"
                f"Contexte (CV) :\n{cv_text}\n\n"
                f"Offre d'emploi :\n{job_offer_text}\n\n"
                f"Tâche : Rédigez une réponse concise (3-6 phrases) à la question : "
                f"'Expliquez-nous pourquoi vous souhaitez nous rejoindre.' "
                f"Utilisez un ton professionnel et motivé. Ne fournissez que le texte de la réponse, "
                f"sans préambule ni signature."
            )
        
        # Default prompt pour autres types
        return (
            f"Vous êtes un assistant expert.\n\n"
            f"Contexte (CV) :\n{cv_text}\n\n"
            f"Offre d'emploi :\n{job_offer_text}\n\n"
            f"Tâche : Rédigez un court paragraphe adapté à l'offre."
        )
    
    def _record_history(
        self,
        user_id: int,
        cv_id: int,
        cv_filename: str,
        job_url: str,
        text_content: str,
        status: str
    ) -> None:
        """
        Enregistre la génération dans l'historique (best effort).
        
        Args:
            user_id: ID utilisateur
            cv_id: ID du CV utilisé
            cv_filename: Nom du fichier CV
            job_url: URL de l'offre d'emploi
            text_content: Texte généré
            status: Statut de la génération
        """
        try:
            # Extraction infos job centralisée via helper
            company_name, job_title = self._job_extractor.extract_from_url(job_url)
            
            # Enregistrer dans l'historique
            self._history_service.record_generation(
                user_id=user_id,
                gen_type='text',
                job_title=job_title,
                company_name=company_name,
                job_url=job_url,
                cv_filename=cv_filename,
                cv_id=cv_id,
                text_content=text_content,
                status=status
            )
            
        except Exception as e:
            # L'historique est non-bloquant
            logger.warning(f"[Use Case] ⚠️  Erreur enregistrement historique (non bloquant): {e}")
