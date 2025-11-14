# infrastructure/adapters/weasyprint_generator.py
from domain.ports.pdf_generator import PdfGenerator, Document
from weasyprint import HTML


class WeasyPrintGgenerator(PdfGenerator):
    def create_pdf(self, document: Document, output_path: str) -> str:
        # Créer du HTML simple avec le texte
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 2cm;
                    line-height: 1.6;
                }}
            </style>
        </head>
        <body>
            <pre style="white-space: pre-wrap; font-family: Arial;">
{document.raw_text}
            </pre>
        </body>
        </html>
        """

        # Générer le PDF
        HTML(string=html_content).write_pdf(output_path)

        return output_path
