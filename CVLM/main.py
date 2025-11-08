

from domain.use_cases.analyze_cv_and_offer import AnalyseCvOffer
from infrastructure.adapters.pypdf_parse import Pypdf_parser
from infrastructure.adapters.open_ai import llmapi
from infrastructure.adapters.fpdf_generator import Fpdf_generator
def main():
    # Instancier les adaptateurs
    parser = Pypdf_parser()
    llm = llmapi()
    pdf_gen = Fpdf_generator()
    
    # Injecter dans le use case
    use_case = AnalyseCvOffer(
        document_parser=parser,
        llm=llm,
        pdf_generator=pdf_gen
    )
    
    # Exécuter
    result_path = use_case.execute()
    print(f"Lettre générée : {result_path}")

if __name__ == "__main__":
    main()