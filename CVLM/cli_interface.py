"""
Interface en ligne de commande pour CVLM
"""
from typing import Dict, Type
from domain.use_cases.analyze_cv_and_offer import AnalyseCvOffer
from infrastructure.adapters.pypdf_parse import Pypdf_parser
from infrastructure.adapters.Google_gemini_api import LlmGemini
from infrastructure.adapters.fpdf_generator import Fpdf_generator
from infrastructure.adapters.welcome_to_jungle_scraper import WelcomeToTheJungleFetcher
from infrastructure.adapters.open_ai_api import LlmOpenAI
from infrastructure.adapters.weasyprint_generator import WeasyPrintGgenerator
from domain.ports.document_parser import DocumentParser
from domain.ports.llm_service import LlmService
from domain.ports.pdf_generator import PdfGenerator
from domain.ports.job_offer_fetcher import JobOfferFetcher


class CliInterface:
    """Interface CLI pour configurer et exécuter l'application"""
    
    def __init__(self):
        # Registre des adaptateurs disponibles
        self.parsers: Dict[str, Type[DocumentParser]] = {
            "1": ("PyPDF Parser", Pypdf_parser),
        }
        
        self.job_fetchers: Dict[str, Type[JobOfferFetcher]] = {
            "1": ("Welcome to the Jungle Scraper", WelcomeToTheJungleFetcher),
            "2": ("PyPDF Parser (fichier local)", Pypdf_parser),
        }
        
        self.llm_services: Dict[str, Type[LlmService]] = {
            "1": ("OpenAI (GPT)", LlmOpenAI),
            "2": ("Google Gemini", LlmGemini),
        }
        
        self.pdf_generators: Dict[str, Type[PdfGenerator]] = {
            "1": ("FPDF Generator", Fpdf_generator),
            "2": ("WeasyPrint Generator (En maintenance)", WeasyPrintGgenerator),
        }
    
    def display_header(self):
        """Affiche l'en-tête de l'application"""
        print("\n" + "="*60)
        print("   📄 CVLM - Générateur de Lettre de Motivation")
        print("="*60 + "\n")
    
    def display_menu(self, title: str, options: Dict[str, tuple]) -> str:
        """Affiche un menu et retourne le choix de l'utilisateur"""
        print(f"\n{'─'*60}")
        print(f"  {title}")
        print(f"{'─'*60}")
        
        for key, (name, _) in options.items():
            print(f"  [{key}] {name}")
        
        print(f"{'─'*60}")
        
        while True:
            choice = input("\n➤ Votre choix : ").strip()
            if choice in options:
                return choice
            print("❌ Choix invalide. Réessayez.")
    
    def confirm_selection(self, selections: dict) -> bool:
        """Affiche un récapitulatif et demande confirmation"""
        print("\n" + "="*60)
        print("   📋 RÉCAPITULATIF DE VOTRE CONFIGURATION")
        print("="*60)
        
        for key, value in selections.items():
            print(f"  • {key}: {value}")
        
        print("="*60)
        
        while True:
            confirm = input("\n✓ Confirmer et générer la lettre ? (o/n) : ").strip().lower()
            if confirm in ['o', 'oui', 'y', 'yes']:
                return True
            elif confirm in ['n', 'non', 'no']:
                return False
            print("❌ Réponse invalide. Tapez 'o' pour oui ou 'n' pour non.")
    
    def get_input_paths(self, use_scraper: bool) -> tuple:
        """Demande les chemins des fichiers d'entrée"""
        print("\n" + "─"*60)
        print("  📂 FICHIERS D'ENTRÉE")
        print("─"*60)
        
        cv_path = input("\n➤ Chemin du CV (défaut: data/input/CV.pdf) : ").strip()
        if not cv_path:
            cv_path = "data/input/CV.pdf"
        
        if use_scraper:
            jo_path = input("\n➤ URL de l'offre d'emploi : ").strip()
            if not jo_path:
                print("❌ L'URL est obligatoire pour le scraper.")
                return self.get_input_paths(use_scraper)
        else:
            jo_path = input("\n➤ Chemin de l'offre d'emploi (défaut: data/input/JO.pdf) : ").strip()
            if not jo_path:
                jo_path = "data/input/JO.pdf"
        
        return cv_path, jo_path
    
    def get_output_path(self) -> str:
        """Demande le chemin de sortie"""
        output_path = input("\n➤ Chemin de sortie (défaut: data/output/ML.pdf) : ").strip()
        if not output_path:
            output_path = "data/output/ML.pdf"
        return output_path
    
    def run(self):
        """Lance l'interface CLI"""
        self.display_header()
        
        # Sélection du parser CV
        parser_choice = self.display_menu(
            "1️⃣  Choisissez le parser pour le CV",
            self.parsers
        )
        parser_name, parser_class = self.parsers[parser_choice]
        
        # Sélection du fetcher d'offre d'emploi
        job_fetcher_choice = self.display_menu(
            "2️⃣  Choisissez la source pour l'offre d'emploi",
            self.job_fetchers
        )
        job_fetcher_name, job_fetcher_class = self.job_fetchers[job_fetcher_choice]
        use_scraper = job_fetcher_choice == "1"
        
        # Sélection du service LLM
        llm_choice = self.display_menu(
            "3️⃣  Choisissez le service LLM",
            self.llm_services
        )
        llm_name, llm_class = self.llm_services[llm_choice]
        
        # Sélection du générateur PDF
        pdf_choice = self.display_menu(
            "4️⃣  Choisissez le générateur PDF",
            self.pdf_generators
        )
        pdf_name, pdf_class = self.pdf_generators[pdf_choice]
        
        # Demande des chemins de fichiers
        cv_path, jo_path = self.get_input_paths(use_scraper)
        output_path = self.get_output_path()
        
        # Récapitulatif
        selections = {
            "Parser CV": parser_name,
            "Source offre d'emploi": job_fetcher_name,
            "Service LLM": llm_name,
            "Générateur PDF": pdf_name,
            "Fichier CV": cv_path,
            "Offre d'emploi": jo_path,
            "Fichier de sortie": output_path
        }
        
        if not self.confirm_selection(selections):
            print("\n❌ Opération annulée.\n")
            return
        
        # Instanciation et exécution
        print("\n⏳ Génération en cours...\n")
        
        try:
            # Instancier les adaptateurs
            parser = parser_class()
            job_fetcher = job_fetcher_class()
            llm = llm_class()
            pdf_gen = pdf_class()
            
            # Créer et exécuter le use case
            use_case = AnalyseCvOffer(
                job_offer_fetcher=job_fetcher,
                document_parser=parser,
                llm=llm,
                pdf_generator=pdf_gen
            )
            
            # Modifier temporairement les chemins si nécessaire
            result_path = use_case.execute(
                cv_path=cv_path,
                jo_path=jo_path,
                output_path=output_path,
                use_scraper=use_scraper
            )
            
            print("="*60)
            print(f"  ✅ Lettre générée avec succès !")
            print(f"  📄 Emplacement : {result_path}")
            print("="*60 + "\n")
            
        except Exception as e:
            print("\n" + "="*60)
            print(f"  ❌ ERREUR : {str(e)}")
            print("="*60 + "\n")


def main():
    """Point d'entrée de l'application"""
    cli = CliInterface()
    cli.run()


if __name__ == "__main__":
    main()