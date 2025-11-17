"""
Script d'initialisation de la base de données PostgreSQL
"""
from infrastructure.adapters.database_config import init_database, drop_all_tables
import sys


def main():
    """Initialise la base de données"""
    print("🔧 Initialisation de la base de données CVLM...")
    
    # Demande confirmation si suppression
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        response = input("⚠️  Voulez-vous SUPPRIMER toutes les tables existantes ? (oui/non): ")
        if response.lower() in ['oui', 'yes', 'o', 'y']:
            print("🗑️  Suppression des tables...")
            drop_all_tables()
    
    # Crée les tables
    init_database()
    
    print("""
✅ Base de données initialisée avec succès !

📋 Tables créées :
   - users (utilisateurs avec auth Google)
   - cvs (CVs des utilisateurs)
   - motivational_letters (lettres de motivation générées)

🔑 Configuration :
   Assurez-vous que le fichier .env contient l'URL de connexion PostgreSQL
   DATABASE_URL=postgresql://user:password@host:port/database

🚀 Prochaines étapes :
   1. Configurer l'authentification Google OAuth
   2. Lancer l'API : python api_server.py
   3. Ou utiliser Streamlit : streamlit run streamlit_app.py
    """)


if __name__ == "__main__":
    main()
