from abc import ABC, abstractmethod
from pypdf import PdfReader


class UserEntries(ABC):
    def __init__(self, path):
        self.path = path
        self.raw_data = None

    def get_raw_data(self):
        self.raw_data = extract_pdf(self.path)


class JobOpening(UserEntries):
    def __init__(self, path):
        super().__init__(path)


class Cv(UserEntries):
    def __init__(self, path):
        super().__init__(path)


class Lm(UserEntries):
    def __init__(self):
        print()


def extract_pdf(path):
    reader = PdfReader(path)
    pdf_pages = []
    for page in reader.pages:
        pdf_pages.append(page.extract_text())
    return ("".join(pdf_pages))
