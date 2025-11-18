"""
Script de migration : Ajouter les colonnes de crédits à la table users
"""
import os
from sqlalchemy import create_engine, text

# Configuration base de données
DB_USER = os.getenv("POSTGRES_USER", "cvlm_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "cvlm_password")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "cvlm_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def migrate():
    """Ajoute les colonnes pdf_credits et text_credits si elles n'existent pas"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Vérifier si les colonnes existent déjà
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name IN ('pdf_credits', 'text_credits');
        """)
        
        result = conn.execute(check_query)
        existing_columns = [row[0] for row in result]
        
        # Ajouter pdf_credits si elle n'existe pas
        if 'pdf_credits' not in existing_columns:
            print("➕ Ajout de la colonne pdf_credits...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN pdf_credits INTEGER NOT NULL DEFAULT 10;
            """))
            conn.commit()
            print("✅ Colonne pdf_credits ajoutée")
        else:
            print("✓ Colonne pdf_credits existe déjà")
        
        # Ajouter text_credits si elle n'existe pas
        if 'text_credits' not in existing_columns:
            print("➕ Ajout de la colonne text_credits...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN text_credits INTEGER NOT NULL DEFAULT 10;
            """))
            conn.commit()
            print("✅ Colonne text_credits ajoutée")
        else:
            print("✓ Colonne text_credits existe déjà")
        
        # Mettre à jour les utilisateurs existants qui auraient NULL
        print("🔄 Mise à jour des crédits des utilisateurs existants...")
        conn.execute(text("""
            UPDATE users 
            SET pdf_credits = 10 
            WHERE pdf_credits IS NULL OR pdf_credits < 0;
        """))
        conn.execute(text("""
            UPDATE users 
            SET text_credits = 10 
            WHERE text_credits IS NULL OR text_credits < 0;
        """))
        conn.commit()
        print("✅ Migration terminée avec succès!")

if __name__ == "__main__":
    print("🚀 Démarrage de la migration...")
    migrate()
