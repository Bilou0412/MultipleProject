#!/usr/bin/env python3
"""
Script de test pour l'API CVLM
"""
import requests
import sys
from pathlib import Path

API_URL = "http://localhost:8000"

def test_health():
    """Test du endpoint health"""
    print("\n🔍 Test du health check...")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            print("✅ API opérationnelle")
            print(f"   {response.json()}")
            return True
        else:
            print(f"❌ Erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Impossible de contacter l'API: {e}")
        print("   Vérifiez que l'API est lancée (python api_server.py)")
        return False

def test_upload_cv():
    """Test de l'upload d'un CV"""
    print("\n📤 Test de l'upload d'un CV...")
    
    # Chercher un CV de test
    cv_path = Path("data/input/CV.pdf")
    
    if not cv_path.exists():
        print(f"❌ Fichier CV non trouvé: {cv_path}")
        print("   Placez un CV de test dans data/input/CV.pdf")
        return None
    
    try:
        with open(cv_path, 'rb') as f:
            files = {'cv_file': ('CV.pdf', f, 'application/pdf')}
            response = requests.post(f"{API_URL}/upload-cv", files=files)
        
        if response.status_code == 200:
            data = response.json()
            cv_id = data['cv_id']
            print(f"✅ CV uploadé avec succès")
            print(f"   ID: {cv_id}")
            print(f"   Fichier: {data['filename']}")
            return cv_id
        else:
            print(f"❌ Erreur d'upload: {response.status_code}")
            print(f"   {response.json()}")
            return None
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def test_generate_letter(cv_id, job_url):
    """Test de la génération d'une lettre"""
    print("\n📝 Test de génération de lettre...")
    print(f"   CV ID: {cv_id}")
    print(f"   Job URL: {job_url}")
    
    try:
        data = {
            'cv_id': cv_id,
            'job_url': job_url,
            'llm_provider': 'openai',
            'pdf_generator': 'fpdf'
        }
        
        print("   ⏳ Génération en cours (peut prendre 30-60s)...")
        response = requests.post(f"{API_URL}/generate-cover-letter", data=data)
        
        if response.status_code == 200:
            result = response.json()
            file_id = result['file_id']
            print(f"✅ Lettre générée avec succès")
            print(f"   File ID: {file_id}")
            print(f"   URL de téléchargement: {result['download_url']}")
            return file_id
        else:
            print(f"❌ Erreur de génération: {response.status_code}")
            print(f"   {response.json()}")
            return None
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def test_download(file_id):
    """Test du téléchargement de la lettre"""
    print("\n⬇️  Test de téléchargement...")
    
    try:
        response = requests.get(f"{API_URL}/download/{file_id}")
        
        if response.status_code == 200:
            # Sauvegarder le fichier
            output_path = Path("data/output/test_lettre_motivation.pdf")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Lettre téléchargée")
            print(f"   Sauvegardée dans: {output_path}")
            return True
        else:
            print(f"❌ Erreur de téléchargement: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_cleanup(cv_id):
    """Test du nettoyage"""
    print("\n🧹 Test de nettoyage...")
    
    try:
        response = requests.delete(f"{API_URL}/cleanup/{cv_id}")
        
        if response.status_code == 200:
            print("✅ Fichiers nettoyés")
            return True
        else:
            print(f"⚠️  Erreur de nettoyage: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Test complet de l'API"""
    print("=" * 60)
    print("🧪 Tests de l'API CVLM")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        sys.exit(1)
    
    # Test 2: Upload CV
    cv_id = test_upload_cv()
    if not cv_id:
        sys.exit(1)
    
    # Test 3: Génération de lettre
    # Utiliser une vraie URL d'offre pour un test complet
    job_url = input("\n🔗 Entrez l'URL d'une offre Welcome to the Jungle (ou appuyez sur Entrée pour passer): ").strip()
    
    if job_url:
        file_id = test_generate_letter(cv_id, job_url)
        
        if file_id:
            # Test 4: Téléchargement
            test_download(file_id)
    else:
        print("⏭️  Génération ignorée (pas d'URL fournie)")
    
    # Test 5: Nettoyage
    test_cleanup(cv_id)
    
    print("\n" + "=" * 60)
    print("✅ Tests terminés !")
    print("=" * 60)
    
    # Test bonus: Stats
    print("\n📊 Statistiques de l'API:")
    try:
        response = requests.get(f"{API_URL}/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   CVs en mémoire: {stats['cvs_in_storage']}")
            print(f"   Lettres en mémoire: {stats['letters_in_storage']}")
    except:
        pass

if __name__ == "__main__":
    main()