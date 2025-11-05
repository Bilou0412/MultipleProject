from domain.ports.document_parser import DocumentParser
from domain.ports.llm_service import LlmService
from domain.ports.pdf_generator import PdfGenerator


class AnalyseCvOffer:
    def __init__(self, document_parser:DocumentParser, llm:LlmService, pdf_generator:PdfGenerator):
        self.document_parser = document_parser
        self.llm = llm
        self.pdf_generator = pdf_generator


    def execute(self):
        
        pass
