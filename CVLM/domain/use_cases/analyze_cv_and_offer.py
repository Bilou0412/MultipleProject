from domain.ports.document_parser import DocumentParser
from domain.ports.llm_service import LlmService
from domain.ports.pdf_generator import PdfGenerator
from domain.ports.job_offer_fetcher import JobOfferFetcher
from domain.entities.cv import Cv
from domain.entities.job_offer import JobOffer
from domain.entities.motivational_letter import MotivationalLetter


class AnalyseCvOffer:
    def __init__(
        self,
        job_offer_fetcher: JobOfferFetcher,
        document_parser: DocumentParser,
        llm: LlmService,
        pdf_generator: PdfGenerator
    ):
        self.document_parser = document_parser
        self.llm = llm
        self.pdf_generator = pdf_generator
        self.job_offer_fetcher = job_offer_fetcher

    def execute(
        self,
        cv_path: str = "data/input/CV.pdf",
        jo_path: str = "data/input/JO.pdf",
        output_path: str = "data/output/ML.pdf",
        use_scraper: bool = False
    ):
        """
        Exécute le use case avec des chemins configurables
        
        Args:
            cv_path: Chemin vers le fichier CV
            jo_path: Chemin vers le fichier offre d'emploi ou URL si use_scraper=True
            output_path: Chemin de sortie pour la lettre générée
            use_scraper: Si True, utilise le job_offer_fetcher au lieu du parser
        """
        # Parse le CV
        cv_raw_text = self.document_parser.parse_document(input_path=cv_path)
        
        # Récupère l'offre d'emploi
# Récupère l'offre d'emploi
        if use_scraper:
            # Utilise le fetcher (scraper) avec l'URL
            job_offer_raw_text = self.job_offer_fetcher.fetch(url=jo_path)  # ← Changé fetch_job_offer à fetch
        else:
            # Utilise le parser pour un fichier local
            job_offer_raw_text = self.document_parser.parse_document(input_path=jo_path)
        
        # Crée les entités
        cv = Cv(cv_raw_text)
        job_offer = JobOffer(job_offer_raw_text)
        
        # Génère le prompt et appelle le LLM
        prompt = self._create_prompt(cv, job_offer)
        raw_text_motivation_letter = self.llm.send_to_llm(prompt)
        
        # Crée la lettre de motivation
        motivational_letter = MotivationalLetter(raw_text_motivation_letter)
        
        # Génère le PDF
        path_pdf = self.pdf_generator.create_pdf(motivational_letter, output_path)
        
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