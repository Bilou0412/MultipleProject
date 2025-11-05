from abc import ABC, abstractmethod
from domain.entities.document import Document


class PdfGenerator(ABC):

    @abstractmethod
    def create_pdf(self, document: Document, output_path:str):
        pass
