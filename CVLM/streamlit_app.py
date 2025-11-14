"""
Interface Streamlit pour CVLM - Générateur de Lettre de Motivation
"""
import streamlit as st
from domain.use_cases.analyze_cv_and_offer import AnalyseCvOffer
from infrastructure.adapters.pypdf_parse import Pypdf_parser
from infrastructure.adapters.Google_gemini_api import LlmGemini
from infrastructure.adapters.fpdf_generator import Fpdf_generator
from infrastructure.adapters.welcome_to_jungle_scraper import WelcomeToTheJungleFetcher
from infrastructure.adapters.open_ai_api import LlmOpenAI
from infrastructure.adapters.weasyprint_generator import WeasyPrintGgenerator
import os

# Configuration de la page
st.set_page_config(
    page_title="CVLM - Générateur de Lettre de Motivation",
    page_icon="📄",
    layout="wide"
)

# Titre
st.title("📄 CVLM - Générateur de Lettre de Motivation")
st.markdown("---")

# Sidebar pour la configuration
st.sidebar.header("⚙️ Configuration")

# Sélection du parser CV
st.sidebar.subheader("1️⃣ Parser CV")
parser_choice = st.sidebar.radio(
    "Choisissez le parser",
    ["PyPDF Parser"],
    key="parser"
)

# Sélection de la source d'offre d'emploi
st.sidebar.subheader("2️⃣ Source offre d'emploi")
job_source = st.sidebar.radio(
    "Choisissez la source",
    ["Welcome to the Jungle (URL)", "Fichier PDF local"],
    key="job_source"
)

# Sélection du LLM
st.sidebar.subheader("3️⃣ Service LLM")
llm_choice = st.sidebar.radio(
    "Choisissez le LLM",
    ["OpenAI (GPT)", "Google Gemini"],
    key="llm"
)

# Sélection du générateur PDF
st.sidebar.subheader("4️⃣ Générateur PDF")
pdf_choice = st.sidebar.radio(
    "Choisissez le générateur",
    ["FPDF Generator", "WeasyPrint (En maintenance)"],
    key="pdf_gen"
)

# Zone principale
col1, col2 = st.columns(2)

with col1:
    st.subheader("📂 Fichier CV")
    cv_file = st.file_uploader("Uploadez votre CV (PDF)", type=['pdf'], key="cv")
    
with col2:
    st.subheader("📄 Offre d'emploi")
    if job_source == "Welcome to the Jungle (URL)":
        job_url = st.text_input("URL de l'offre d'emploi", placeholder="https://www.welcometothejungle.com/...")
    else:
        job_file = st.file_uploader("Uploadez l'offre d'emploi (PDF)", type=['pdf'], key="jo")

st.markdown("---")

# Bouton de génération
if st.button("🚀 Générer la lettre de motivation", type="primary", use_container_width=True):
    
    # Validation des inputs
    if not cv_file:
        st.error("❌ Veuillez uploader un CV")
    elif job_source == "Welcome to the Jungle (URL)" and not job_url:
        st.error("❌ Veuillez entrer l'URL de l'offre d'emploi")
    elif job_source == "Fichier PDF local" and not job_file:
        st.error("❌ Veuillez uploader l'offre d'emploi")
    else:
        try:
            with st.spinner("⏳ Génération en cours..."):
                
                # Sauvegarde temporaire des fichiers uploadés
                cv_path = "temp_cv.pdf"
                with open(cv_path, "wb") as f:
                    f.write(cv_file.getbuffer())
                
                if job_source == "Fichier PDF local":
                    jo_path = "temp_jo.pdf"
                    with open(jo_path, "wb") as f:
                        f.write(job_file.getbuffer())
                    use_scraper = False
                else:
                    jo_path = job_url
                    use_scraper = True
                
                # Instanciation des adaptateurs
                parser = Pypdf_parser()
                
                if job_source == "Welcome to the Jungle (URL)":
                    job_fetcher = WelcomeToTheJungleFetcher()
                else:
                    job_fetcher = Pypdf_parser()
                
                if llm_choice == "OpenAI (GPT)":
                    llm = LlmOpenAI()
                else:
                    llm = LlmGemini()
                
                if pdf_choice == "FPDF Generator":
                    pdf_gen = Fpdf_generator()
                else:
                    pdf_gen = WeasyPrintGgenerator()
                
                # Création du use case
                use_case = AnalyseCvOffer(
                    job_offer_fetcher=job_fetcher,
                    document_parser=parser,
                    llm=llm,
                    pdf_generator=pdf_gen
                )
                
                # Exécution
                output_path = "lettre_motivation.pdf"
                result_path = use_case.execute(
                    cv_path=cv_path,
                    jo_path=jo_path,
                    output_path=output_path,
                    use_scraper=use_scraper
                )
                
                # Affichage du succès
                st.success("✅ Lettre de motivation générée avec succès !")
                
                # Téléchargement du fichier
                with open(result_path, "rb") as f:
                    st.download_button(
                        label="📥 Télécharger la lettre",
                        data=f,
                        file_name="lettre_motivation.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                
                # Nettoyage des fichiers temporaires
                if os.path.exists(cv_path):
                    os.remove(cv_path)
                if job_source == "Fichier PDF local" and os.path.exists(jo_path):
                    os.remove(jo_path)
                    
        except Exception as e:
            st.error(f"❌ Erreur : {str(e)}")

# Footer
st.markdown("---")
st.markdown("💡 **Astuce** : Assurez-vous que votre CV et l'offre d'emploi sont bien structurés pour de meilleurs résultats.")