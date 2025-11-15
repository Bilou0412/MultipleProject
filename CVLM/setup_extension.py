#!/usr/bin/env python3
"""
Script d'installation automatique de l'extension CVLM
"""
import os
import sys
from pathlib import Path

# Contenu des fichiers de l'extension
MANIFEST_JSON = """{
  "manifest_version": 3,
  "name": "CVLM - Générateur de Lettre de Motivation",
  "version": "1.0.0",
  "description": "Générez automatiquement des lettres de motivation depuis les offres d'emploi en ligne",
  "permissions": [
    "activeTab",
    "storage",
    "scripting"
  ],
  "host_permissions": [
    "https://www.welcometothejungle.com/*",
    "https://www.linkedin.com/*",
    "https://www.indeed.fr/*"
  ],
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": [
        "https://www.welcometothejungle.com/*/jobs/*",
        "https://www.linkedin.com/jobs/*",
        "https://www.indeed.fr/*/viewjob*"
      ],
      "js": ["content.js"],
      "css": ["content.css"]
    }
  ]
}"""

BACKGROUND_JS = """// Background script pour l'extension CVLM
console.log('CVLM Extension activée');

// Écouter les messages depuis le content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'jobPageDetected') {
    console.log('Page d\'offre détectée:', request.url);
    // Vous pouvez ajouter une notification ici
  }
  
  if (request.action === 'openPopup') {
    chrome.action.openPopup();
  }
});"""

def create_directory(path):
    """Crée un dossier s'il n'existe pas"""
    Path(path).mkdir(parents=True, exist_ok=True)
    print(f"✅ Dossier créé: {path}")

def create_file(path, content):
    """Crée un fichier avec le contenu spécifié"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Fichier créé: {path}")

def check_dependencies():
    """Vérifie les dépendances Python"""
    print("\n🔍 Vérification des dépendances...")
    
    required = ['fastapi', 'uvicorn', 'pydantic']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (manquant)")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Installez les dépendances manquantes:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

def create_extension_structure():
    """Crée la structure de l'extension"""
    print("\n📦 Création de la structure de l'extension...")
    
    # Créer les dossiers
    create_directory("extension")
    create_directory("extension/icons")
    
    # Créer manifest.json
    create_file("extension/manifest.json", MANIFEST_JSON)
    
    # Créer background.js
    create_file("extension/background.js", BACKGROUND_JS)
    
    # Instructions pour les autres fichiers
    print("\n📋 Fichiers à copier manuellement:")
    print("  - popup.html (depuis l'artifact)")
    print("  - popup.js (depuis l'artifact)")
    print("  - content.js (depuis l'artifact)")
    print("  - content.css (depuis l'artifact)")
    print("\n  Copiez ces fichiers dans le dossier 'extension/'")

def create_icons_readme():
    """Crée le README pour les icônes"""
    readme_content = """# Création des icônes CVLM

## Option 1: Générateur en ligne (Rapide)

1. Allez sur https://favicon.io/favicon-generator/
2. Configurez:
   - Text: CV
   - Font: Arial Bold
   - Background: #667eea (violet-bleu)
   - Font Color: white
3. Téléchargez et renommez:
   - favicon-16x16.png → icon16.png
   - favicon-32x32.png → icon48.png (redimensionner)
   - android-chrome-192x192.png → icon128.png (redimensionner)

## Option 2: Canva (Design personnalisé)

1. Allez sur https://www.canva.com
2. Créez un design 128x128px
3. Ajoutez une icône de document/lettre
4. Exportez en PNG
5. Redimensionnez pour créer les 3 tailles

## Option 3: Figma

Utilisez le template d'icône d'extension Chrome disponible sur Figma Community

## Placer les icônes

Copiez les 3 fichiers dans: extension/icons/
- icon16.png (16x16 pixels)
- icon48.png (48x48 pixels)
- icon128.png (128x128 pixels)
"""
    create_file("extension/icons/README.md", readme_content)

def create_env_example():
    """Crée un fichier .env.example"""
    env_content = """# Configuration API CVLM

# Clés API LLM (au moins une requise)
OPENAI_API_KEY=sk-votre-clé-openai-ici
GEMINI_API_KEY=votre-clé-gemini-ici

# Configuration serveur (optionnel)
API_HOST=0.0.0.0
API_PORT=8000

# CORS (en production, limitez aux origines spécifiques)
ALLOWED_ORIGINS=*
"""
    if not os.path.exists(".env"):
        create_file(".env.example", env_content)
        print("\n⚠️  Créez un fichier .env à partir de .env.example")
        print("   et ajoutez vos clés API")

def main():
    """Point d'entrée principal"""
    print("=" * 60)
    print("🚀 Installation de l'extension CVLM")
    print("=" * 60)
    
    # Vérifier qu'on est dans le bon dossier
    if not os.path.exists("domain") or not os.path.exists("infrastructure"):
        print("\n❌ Erreur: Lancez ce script depuis la racine du projet CVLM")
        print("   (le dossier contenant 'domain/' et 'infrastructure/')")
        sys.exit(1)
    
    # Vérifier les dépendances
    if not check_dependencies():
        sys.exit(1)
    
    # Créer la structure
    create_extension_structure()
    
    # Créer le README pour les icônes
    create_icons_readme()
    
    # Créer .env.example
    create_env_example()
    
    # Créer les dossiers de données
    create_directory("data/temp")
    
    print("\n" + "=" * 60)
    print("✅ Installation terminée !")
    print("=" * 60)
    
    print("\n📋 Prochaines étapes:")
    print("1. Copiez les fichiers popup.html, popup.js, content.js, content.css")
    print("   dans le dossier 'extension/'")
    print("2. Créez les icônes (voir extension/icons/README.md)")
    print("3. Configurez le fichier .env avec vos clés API")
    print("4. Lancez l'API: python api_server.py")
    print("5. Chargez l'extension dans Chrome (chrome://extensions/)")
    
    print("\n🎉 Tout est prêt ! Bonne génération de lettres de motivation !")

if __name__ == "__main__":
    main()