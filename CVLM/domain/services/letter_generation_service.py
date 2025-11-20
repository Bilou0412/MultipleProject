"""
Service de génération de lettres de motivation
Encapsule la logique métier complexe
"""
import uuid
from pathlib import Path
from typing import Tuple

from domain.entities.motivational_letter import MotivationalLetter
from domain.entities.user import User
from domain.entities.cv import Cv

from infrastructure.adapters.pypdf_parse import PyPdfParser
from infrastructure.adapters.google_gemini_api import GoogleGeminiLlm
from infrastructure.adapters.fpdf_generator import FpdfGenerator
from infrastructure.adapters.welcome_to_jungle_scraper import WelcomeToTheJungleFetcher
from infrastructure.adapters.open_ai_api import OpenAiLlm
from infrastructure.adapters.weasyprint_generator import WeasyPrintGenerator
from infrastructure.adapters.local_file_storage import LocalFileStorage
from infrastructure.adapters.logger_config import setup_logger

from config.constants import (
    LLM_PROVIDER_GEMINI,
    PDF_GENERATOR_WEASYPRINT,
    OUTPUT_DIR
)

logger = setup_logger(__name__)


class LetterGenerationService:
    """Service pour la génération de lettres de motivation"""
    
    def __init__(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.file_storage = LocalFileStorage()
    
    def _create_llm_service(self, provider: str):
        """Crée le service LLM approprié"""
        if provider.lower() == LLM_PROVIDER_GEMINI:
            return GoogleGeminiLlm()
        return OpenAiLlm()
    
    def _create_pdf_generator(self, generator_type: str):
        """Crée le générateur PDF approprié"""
        if generator_type.lower() == PDF_GENERATOR_WEASYPRINT:
            return WeasyPrintGenerator()
        return FpdfGenerator()
    
    def generate_letter_pdf(
        self,
        cv: Cv,
        job_url: str,
        llm_provider: str,
        pdf_generator: str,
        user: User
    ) -> Tuple[str, str, str]:
        """
        Génère une lettre de motivation en PDF
        
        Args:
            cv: Entité CV
            job_url: URL de l'offre d'emploi
            llm_provider: Provider LLM (openai/gemini)
            pdf_generator: Type de générateur PDF (fpdf/weasyprint)
            user: Utilisateur courant
        
        Returns:
            Tuple (letter_id, file_path, letter_text)
        """
        # Instancier les adapters
        document_parser = PyPdfParser()
        job_fetcher = WelcomeToTheJungleFetcher()
        llm = self._create_llm_service(llm_provider)
        pdf_gen = self._create_pdf_generator(pdf_generator)
        
        # === PHASE 1: Extraction CV ===
        cv_text = cv.raw_text  # On a déjà le texte du CV depuis l'entité
        
        # === PHASE 2: Récupération offre d'emploi ===
        job_offer_text = job_fetcher.fetch(url=job_url)
        
        # === PHASE 3: Génération texte via LLM ===
        prompt = self._build_letter_prompt(cv_text, job_offer_text)
        letter_text = llm.send_to_llm(prompt)
        
        # === PHASE 4: Génération PDF ===
        letter_id = str(uuid.uuid4())
        output_path = OUTPUT_DIR / f"lettre_{letter_id}.pdf"
        
        # Créer l'entité MotivationalLetter temporaire pour le PDF
        from domain.entities.motivational_letter import MotivationalLetter
        temp_letter = MotivationalLetter(raw_text=letter_text)
        
        # Générer le PDF
        pdf_path = pdf_gen.create_pdf(temp_letter, str(output_path))
        
        logger.info(f"Lettre générée: {letter_id} pour l'utilisateur {user.email}")
        
        return letter_id, pdf_path, letter_text
    
    def _build_letter_prompt(self, cv_text: str, job_offer_text: str) -> str:
        """
        Construit le prompt pour la génération de lettre de motivation.
        
        Args:
            cv_text: Contenu textuel du CV
            job_offer_text: Contenu de l'offre d'emploi
        
        Returns:
            Prompt formaté pour le LLM
        """
        return f"""
Tu es un assistant expert en rédaction professionnelle.

🎯 Objectif :
Rédige une **lettre de motivation complète et immédiatement exploitable**,
adaptée à l'offre d'emploi et au CV ci-dessous.

⚙️ Règles :
- Donne uniquement le texte final de la lettre, sans aucun commentaire, balise, guillemet, ou texte d'explication.
- Ne mets **aucun élément entre crochets** (pas de [Date], [Nom], etc.).
- Si une information manque (par ex. adresse, nom du recruteur), écris une **formule naturelle générique** (ex. "Madame, Monsieur," ou "le service recrutement").
- Formate la lettre pour être prête à l'envoi (coordonnées en haut, objet, paragraphes bien séparés, signature).
- Langue : français professionnel, fluide et naturel.
- Ton : motivé, sincère, précis, sans exagération.

🧾 Texte du CV :
{cv_text}

📄 Texte de l'offre d'emploi :
{job_offer_text}

🪶 Rédige maintenant la lettre de motivation finale :
        """.strip()
    
    def save_letter_to_storage(
        self,
        letter_id: str,
        pdf_path: str,
        cv_id: str,
        job_url: str,
        letter_text: str,
        llm_provider: str,
        user: User
    ) -> MotivationalLetter:
        """
        Sauvegarde la lettre générée dans le stockage
        
        Returns:
            Entité MotivationalLetter créée
        """
        # Lire le PDF
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        # Sauvegarder via file storage
        file_path = self.file_storage.save_letter(
            letter_id=letter_id,
            content=pdf_content,
            filename=f"lettre_{letter_id}.pdf"
        )
        
        # Créer l'entité
        letter = MotivationalLetter(
            id=letter_id,
            user_id=user.id,
            cv_id=cv_id,
            job_offer_url=job_url,
            filename=f"lettre_{letter_id}.pdf",
            file_path=file_path,
            file_size=len(pdf_content),
            raw_text=letter_text,
            llm_provider=llm_provider
        )
        
        logger.info(f"Lettre sauvegardée: {letter_id}, taille: {len(pdf_content)} bytes")
        
        return letter
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrait le texte d'un PDF"""
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text.strip() if text else "Lettre générée. Consultez le PDF."
        except Exception as e:
            logger.warning(f"Erreur extraction texte PDF: {e}")
            return "Lettre générée. Consultez le PDF."
