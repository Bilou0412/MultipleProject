from pypdf import PdfReader
from domain.ports.document_parser import DocumentParser


class PyPdfParser(DocumentParser):
    def parse_document(self, input_path: str):
        pdf = PdfReader(input_path)
        text_pdf = ""
        for page in pdf.pages:
            text_pdf += page.extract_text()
        return text_pdf
