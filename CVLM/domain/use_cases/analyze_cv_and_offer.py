from domain.ports.document_parser import DocumentParser
from domain.ports.llm_service import LlmService
from domain.ports.pdf_generator import PdfGenerator
from domain.ports.job_offer_fetcher import JobOfferFetcher
from domain.entities.cv import Cv
from domain.entities.job_offer import JobOffer
from domain.entities.motivational_letter import MotivationalLetter


class AnalyseCvOffer:
    def __init__(self,job_offer_fetcher: JobOfferFetcher, document_parser: DocumentParser, llm: LlmService, pdf_generator: PdfGenerator):
        self.document_parser = document_parser
        self.llm = llm
        self.pdf_generator = pdf_generator
        self.job_offer_fetcher = job_offer_fetcher

    def execute(self):
        cv_raw_text = self.document_parser.parse_document(input_path="data/input/CV.pdf")
        job_offer_raw_text = self.job_offer_fetcher.fetch("https://www.welcometothejungle.com/fr/companies/elax-energie/jobs/lead-dev-python-cdi-remote_paris")
        cv = Cv(cv_raw_text)
        job_offer = JobOffer(job_offer_raw_text)
        prompt = self._create_prompt(cv, job_offer)
        raw_text_motivation_letter = self.llm.send_to_llm(prompt)
        motivational_letter = MotivationalLetter(raw_text_motivation_letter)
        path_pdf = self.pdf_generator.create_pdf(
            motivational_letter, "data/output/ML.pdf")

        return (path_pdf)

    def _create_prompt(self, cv: Cv, job_offer: JobOffer) -> str:
        prompt = f"""
        Tu es un assistant expert en rédaction professionnelle.
    
        🎯 Objectif :
        Rédige une **lettre de motivation complète et immédiatement exploitable**,
        adaptée à l’offre d’emploi et au CV ci-dessous.
    
        ⚙️ Règles :
        - Donne uniquement le texte final de la lettre, sans aucun commentaire, balise, guillemet, ou texte d’explication.
        - Ne mets **aucun élément entre crochets** (pas de [Date], [Nom], etc.).
        - Si une information manque (par ex. adresse, nom du recruteur), écris une **formule naturelle générique** (ex. "Madame, Monsieur," ou "le service recrutement").
        - Formate la lettre pour être prête à l’envoi (coordonnées en haut, objet, paragraphes bien séparés, signature).
        - Langue : français professionnel, fluide et naturel.
        - Ton : motivé, sincère, précis, sans exagération.
    
        🧾 Texte du CV :
        {cv.raw_text}
    
        📄 Texte de l’offre d’emploi :
        {job_offer.raw_text}
    
        🪶 Rédige maintenant la lettre de motivation finale :
        """
        return prompt.strip()



