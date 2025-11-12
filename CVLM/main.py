

from domain.use_cases.analyze_cv_and_offer import AnalyseCvOffer
from infrastructure.adapters.pypdf_parse import Pypdf_parser
from infrastructure.adapters.Google_gemini_api import LlmGemini
from infrastructure.adapters.fpdf_generator import Fpdf_generator
from infrastructure.adapters.welcome_to_jungle_scraper import WelcomeToJungleScraper
from infrastructure.adapters.open_ai_api import LlmOpenAI

def main():
    # Instancier les adaptateurs
    parser = Pypdf_parser()
    llm = LlmOpenAI()
    pdf_gen = Fpdf_generator()
    job_offer_fetcher = WelcomeToJungleScraper()

    # Injecter dans le use case
    use_case = AnalyseCvOffer(
        job_offer_fetcher=job_offer_fetcher,
        document_parser=parser,
        llm=llm,
        pdf_generator=pdf_gen
    )

    # Exécuter
    result_path = use_case.execute()
    print(f"Lettre générée : {result_path}")


if __name__ == "__main__":
    main()
