"""
Script d'exemple pour migrer les données stockées en mémoire vers la base PostgreSQL
"""
from infrastructure.adapters.postgres_user_repository import PostgresUserRepository
from infrastructure.adapters.postgres_cv_repository import PostgresCvRepository
from infrastructure.adapters.postgres_motivational_letter_repository import PostgresMotivationalLetterRepository
from infrastructure.adapters.local_file_storage import LocalFileStorage
from domain.entities.user import User
from domain.entities.cv import Cv
from domain.entities.motivational_letter import MotivationalLetter
import uuid
import os
from pathlib import Path


def migrate_example_user():
    """
    Exemple de création d'un utilisateur de test
    """
    print("👤 Création d'un utilisateur de test...")
    
    user_repo = PostgresUserRepository()
    
    # Créer un utilisateur de test
    test_user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        google_id="test_google_id_123",
        name="Test User",
        profile_picture_url=None
    )
    
    # Vérifier s'il existe déjà
    existing = user_repo.get_by_email(test_user.email)
    if existing:
        print(f"   ℹ️  L'utilisateur existe déjà : {existing.id}")
        return existing.id
    
    # Créer l'utilisateur
    created_user = user_repo.create(test_user)
    print(f"   ✅ Utilisateur créé : {created_user.id}")
    return created_user.id


def migrate_cv_files(user_id: str, source_dir: str = "data/temp"):
    """
    Migre les fichiers CV du répertoire temporaire vers la base
    
    Args:
        user_id: ID de l'utilisateur propriétaire
        source_dir: Répertoire source contenant les CVs
    """
    print(f"\n📄 Migration des CVs depuis {source_dir}...")
    
    cv_repo = PostgresCvRepository()
    file_storage = LocalFileStorage()
    
    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"   ⚠️  Répertoire {source_dir} introuvable")
        return
    
    # Rechercher les fichiers CV
    cv_files = list(source_path.glob("cv_*.pdf"))
    
    if not cv_files:
        print(f"   ℹ️  Aucun fichier CV trouvé dans {source_dir}")
        return
    
    for cv_file in cv_files:
        print(f"   🔄 Migration de {cv_file.name}...")
        
        try:
            # Lire le contenu du fichier
            with open(cv_file, 'rb') as f:
                file_content = f.read()
            
            # Générer un ID pour le CV
            cv_id = str(uuid.uuid4())
            filename = f"cv_{cv_id}.pdf"
            
            # Sauvegarder dans le nouveau système de stockage
            relative_path = file_storage.save_file(
                file_content=file_content,
                filename=filename,
                subfolder="cvs"
            )
            
            # Créer l'entité CV
            cv = Cv(raw_text="")  # Le texte sera extrait plus tard si nécessaire
            cv.id = cv_id
            cv.user_id = user_id
            cv.filename = cv_file.name
            cv.file_path = relative_path
            cv.file_size = len(file_content)
            
            # Sauvegarder en base
            saved_cv = cv_repo.create(cv)
            
            print(f"      ✅ CV migré : {saved_cv.id}")
            
        except Exception as e:
            print(f"      ❌ Erreur : {e}")
            continue


def migrate_letter_files(user_id: str, source_dir: str = "data/output"):
    """
    Migre les lettres de motivation du répertoire output vers la base
    
    Args:
        user_id: ID de l'utilisateur propriétaire
        source_dir: Répertoire source contenant les lettres
    """
    print(f"\n✉️  Migration des lettres depuis {source_dir}...")
    
    letter_repo = PostgresMotivationalLetterRepository()
    file_storage = LocalFileStorage()
    
    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"   ⚠️  Répertoire {source_dir} introuvable")
        return
    
    # Rechercher les fichiers de lettres
    letter_files = list(source_path.glob("lettre_*.pdf")) + list(source_path.glob("ML*.pdf"))
    
    if not letter_files:
        print(f"   ℹ️  Aucune lettre trouvée dans {source_dir}")
        return
    
    for letter_file in letter_files:
        print(f"   🔄 Migration de {letter_file.name}...")
        
        try:
            # Lire le contenu du fichier
            with open(letter_file, 'rb') as f:
                file_content = f.read()
            
            # Générer un ID pour la lettre
            letter_id = str(uuid.uuid4())
            filename = f"letter_{letter_id}.pdf"
            
            # Sauvegarder dans le nouveau système de stockage
            relative_path = file_storage.save_file(
                file_content=file_content,
                filename=filename,
                subfolder="letters"
            )
            
            # Créer l'entité MotivationalLetter
            letter = MotivationalLetter(raw_text="")
            letter.id = letter_id
            letter.user_id = user_id
            letter.cv_id = None  # On ne peut pas retrouver le lien automatiquement
            letter.job_offer_url = None
            letter.filename = letter_file.name
            letter.file_path = relative_path
            letter.file_size = len(file_content)
            letter.llm_provider = "unknown"
            
            # Sauvegarder en base
            saved_letter = letter_repo.create(letter)
            
            print(f"      ✅ Lettre migrée : {saved_letter.id}")
            
        except Exception as e:
            print(f"      ❌ Erreur : {e}")
            continue


def main():
    """
    Script principal de migration
    """
    print("=" * 60)
    print("🔄 MIGRATION DES DONNÉES VERS POSTGRESQL")
    print("=" * 60)
    
    try:
        # 1. Créer un utilisateur de test
        user_id = migrate_example_user()
        
        # 2. Migrer les CVs
        migrate_cv_files(user_id)
        
        # 3. Migrer les lettres
        migrate_letter_files(user_id)
        
        print("\n" + "=" * 60)
        print("✅ MIGRATION TERMINÉE")
        print("=" * 60)
        print(f"""
📊 Résumé :
   - Utilisateur créé/vérifié : {user_id}
   - CVs et lettres migrés dans data/files/
   - Métadonnées sauvegardées en PostgreSQL

🔍 Vérification :
   python -c "from infrastructure.adapters.postgres_cv_repository import PostgresCvRepository; print(len(PostgresCvRepository().list_all()), 'CVs en base')"
   python -c "from infrastructure.adapters.postgres_motivational_letter_repository import PostgresMotivationalLetterRepository; print(len(PostgresMotivationalLetterRepository().list_all()), 'lettres en base')"
        """)
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la migration : {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
