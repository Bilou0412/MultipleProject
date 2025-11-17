from abc import ABC, abstractmethod
from typing import Protocol


class Document(Protocol):
    """Protocol pour les documents ayant un raw_text"""
    raw_text: str


class PdfGenerator(ABC):
    """Interface pour générer des PDFs à partir de documents"""
    
    @abstractmethod
    def create_pdf(self, document: Document, output_path: str) -> str:
        pass
