from domain.ports.document_parser import DocumentParser
from domain.ports.llm_service import LlmService
from domain.ports.pdf_generator import PdfGenerator
from domain.ports.job_offer_fetcher import JobOfferFetcher
from domain.ports.cv_repository import CvRepository
from domain.ports.motivational_letter_repository import MotivationalLetterRepository
from domain.ports.file_storage import FileStorage
from domain.entities.cv import Cv
from domain.entities.job_offer import JobOffer
from domain.entities.motivational_letter import MotivationalLetter
from typing import Optional
import uuid
from pathlib import Path


class AnalyseCvOffer:
    def __init__(
        self,
        job_offer_fetcher: JobOfferFetcher,
        document_parser: DocumentParser,
        llm: LlmService,
        pdf_generator: PdfGenerator,
        cv_repository: Optional[CvRepository] = None,
        letter_repository: Optional[MotivationalLetterRepository] = None,
        file_storage: Optional[FileStorage] = None
    ):
        self.document_parser = document_parser
        self.llm = llm
        self.pdf_generator = pdf_generator
        self.job_offer_fetcher = job_offer_fetcher
        self.cv_repository = cv_repository
        self.letter_repository = letter_repository
        self.file_storage = file_storage

    def execute(
        self,
        cv_path: str = "data/input/CV.pdf",
        jo_path: str = "data/input/JO.pdf",
        output_path: str = "data/output/ML.pdf",
        use_scraper: bool = False,
        user_id: Optional[str] = None,
        cv_id: Optional[str] = None,
        persist: bool = False
    ):
        """
        Exécute le use case avec des chemins configurables
        
        Args:
            cv_path: Chemin vers le fichier CV
            jo_path: Chemin vers le fichier offre d'emploi ou URL si use_scraper=True
            output_path: Chemin de sortie pour la lettre générée
            use_scraper: Si True, utilise le job_offer_fetcher au lieu du parser
            user_id: ID de l'utilisateur (optionnel, pour la persistance)
            cv_id: ID du CV existant (optionnel, évite de parser à nouveau)
            persist: Si True, sauvegarde en base de données
        
        Returns:
            Tuple (path_pdf, letter_id) si persist=True, sinon juste path_pdf
        """
        # Récupère ou parse le CV
        if cv_id and self.cv_repository:
            cv_entity = self.cv_repository.get_by_id(cv_id)
            if not cv_entity:
                raise ValueError(f"CV avec id {cv_id} introuvable")
            cv_raw_text = cv_entity.raw_text
        else:
            cv_raw_text = self.document_parser.parse_document(input_path=cv_path)
        
        # Récupère l'offre d'emploi
        if use_scraper:
            job_offer_raw_text = self.job_offer_fetcher.fetch(url=jo_path)
        else:
            job_offer_raw_text = self.document_parser.parse_document(input_path=jo_path)
        
        # Crée les entités
        cv = Cv(raw_text=cv_raw_text)
        job_offer = JobOffer(raw_text=job_offer_raw_text)
        
        # Génère le prompt et appelle le LLM
        prompt = self._create_prompt(cv, job_offer)
        raw_text_motivation_letter = self.llm.send_to_llm(prompt)
        
        # Crée la lettre de motivation
        motivational_letter = MotivationalLetter(raw_text=raw_text_motivation_letter)
        
        # Génère le PDF
        path_pdf = self.pdf_generator.create_pdf(motivational_letter, output_path)
        
        # Persistance si demandée
        if persist and self.letter_repository and self.file_storage:
            letter_id = str(uuid.uuid4())
            
            # Lit le fichier PDF généré
            with open(path_pdf, 'rb') as f:
                pdf_content = f.read()
            
            # Stocke le fichier
            filename = f"letter_{letter_id}.pdf"
            relative_path = self.file_storage.save_file(
                pdf_content, 
                filename, 
                subfolder="letters"
            )
            
            # Met à jour l'entité
            motivational_letter.id = letter_id
            motivational_letter.user_id = user_id
            motivational_letter.cv_id = cv_id
            motivational_letter.job_offer_url = jo_path if use_scraper else None
            motivational_letter.filename = filename
            motivational_letter.file_path = relative_path
            motivational_letter.file_size = len(pdf_content)
            motivational_letter.llm_provider = getattr(self.llm, 'provider_name', 'unknown')
            
            # Sauvegarde en DB
            saved_letter = self.letter_repository.create(motivational_letter)
            
            return path_pdf, saved_letter.id
        
        return path_pdf

    def _create_prompt(self, cv: Cv, job_offer: JobOffer) -> str:
        prompt = f"""
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
{cv.raw_text}
        
        📄 Texte de l'offre d'emploi :
{job_offer.raw_text}
        
        🪶 Rédige maintenant la lettre de motivation finale :
        """
        return prompt.strip()