# infrastructure/adapters/fpdf_generator.py
from domain.ports.pdf_generator import PdfGenerator, Document
from fpdf import FPDF


class FpdfGenerator(PdfGenerator):
    def create_pdf(self, document: Document, output_path: str) -> str:
        pdf = FPDF()
        pdf.add_page()
        
        # Marges
        pdf.set_margins(20, 20, 20)
        
        # ✅ Utiliser DejaVu (police Unicode qui supporte les accents français)
        pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
        pdf.set_font('DejaVu', size=11)
        
        # Ajouter le texte
        pdf.multi_cell(0, 7, document.raw_text)
        
        # Sauvegarder
        pdf.output(output_path)
        
        return output_path