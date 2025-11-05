from domain.ports.document_parser import DocumentParser
from domain.ports.llm_service import LlmService
from domain.ports.pdf_generator import PdfGenerator
from domain.entities.cv import Cv
from domain.entities.job_offer import JobOffer
from domain.entities.motivational_letter import MotivationalLetter


class AnalyseCvOffer:
    def __init__(self, document_parser: DocumentParser, llm: LlmService, pdf_generator: PdfGenerator):
        self.document_parser = document_parser
        self.llm = llm
        self.pdf_generator = pdf_generator

    def execute(self):
        cv_raw_text = self.document_parser.parse_document("data/input/CV.pdf")
        job_offer_raw_text = self.document_parser.parse_document(
            "data/input/JO.pdf")
        cv = Cv(cv_raw_text)
        job_offer = JobOffer(job_offer_raw_text)
        prompt = self._create_prompt(cv, job_offer)
        raw_text_motivation_letter = self.llm.send_to_llm(prompt)
        motivational_letter = MotivationalLetter(raw_text_motivation_letter)
        path_pdf = self.pdf_generator.create_pdf(
            motivational_letter, "data/output/ML.pdf")

        return (path_pdf)

    def _create_prompt(self, cv: Cv, job_offer: JobOffer):
        pass
