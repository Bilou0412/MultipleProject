#!/bin/bash

echo "🔒 SÉCURISATION DU PROJET CVLM AVANT PRODUCTION"
echo "================================================"
echo ""

# 1. Backup du .env actuel
echo "1️⃣ Sauvegarde du .env actuel..."
if [ -f .env ]; then
    cp .env .env.backup
    echo "✅ .env sauvegardé dans .env.backup"
else
    echo "⚠️  Pas de fichier .env trouvé"
fi

# 2. Générer un nouveau JWT_SECRET
echo ""
echo "2️⃣ Génération d'un nouveau JWT_SECRET..."
NEW_JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "✅ Nouveau JWT_SECRET: $NEW_JWT_SECRET"
echo "   👉 À ajouter manuellement dans votre .env en production"

# 3. Vérifier si .env est dans .gitignore
echo ""
echo "3️⃣ Vérification du .gitignore..."
if grep -q "^\.env$" .gitignore; then
    echo "✅ .env est déjà dans .gitignore"
else
    echo ".env" >> .gitignore
    echo "✅ .env ajouté au .gitignore"
fi

# 4. Supprimer .env de l'historique Git (DANGEREUX - fait un backup avant!)
echo ""
echo "4️⃣ Nettoyage de l'historique Git..."
echo "⚠️  ATTENTION: Cette opération va réécrire l'historique Git!"
read -p "Voulez-vous supprimer .env de l'historique Git? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Suppression de .env de l'historique Git..."
    
    # Backup du repo
    cd ..
    tar -czf "CVLM-backup-$(date +%Y%m%d-%H%M%S).tar.gz" CVLM/
    cd CVLM
    echo "✅ Backup créé dans ../CVLM-backup-*.tar.gz"
    
    # Nettoyage avec filter-branch
    git filter-branch --force --index-filter \
        "git rm --cached --ignore-unmatch .env" \
        --prune-empty --tag-name-filter cat -- --all
    
    echo "✅ .env supprimé de l'historique"
    echo "⚠️  Pour mettre à jour GitHub, faites: git push origin --force --all"
else
    echo "❌ Nettoyage Git annulé"
fi

# 5. Créer .env.example sans valeurs sensibles
echo ""
echo "5️⃣ Création de .env.example..."
cat > .env.example << 'EOF'
# Configuration de la base de données
DATABASE_URL=postgresql://username:password@localhost:5432/dbname

# Configuration OpenAI
OPENAI_API_KEY=sk-your-openai-api-key-here

# Configuration Google Gemini (optionnel)
GOOGLE_API_KEY=your-google-gemini-key-here

# Configuration Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com

# JWT Secret (générer avec: python -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=your-random-jwt-secret-key-here

# Environment
ENVIRONMENT=production
EOF
echo "✅ .env.example créé"

# 6. Vérifier les autres fichiers sensibles
echo ""
echo "6️⃣ Recherche d'autres fichiers sensibles..."
echo "Fichiers potentiellement sensibles:"
find . -type f \( -name "*.key" -o -name "*.pem" -o -name "*.p12" -o -name "credentials.json" \) 2>/dev/null
echo ""

# 7. Résumé
echo ""
echo "============================================"
echo "✅ SÉCURISATION TERMINÉE"
echo "============================================"
echo ""
echo "📋 ACTIONS À FAIRE MANUELLEMENT:"
echo ""
echo "1. Créer un nouveau projet Google Cloud Console"
echo "   - Générer de NOUVELLES clés OAuth"
echo "   - Révoquer les anciennes clés exposées"
echo ""
echo "2. Créer une nouvelle clé OpenAI"
echo "   - Dashboard: https://platform.openai.com/api-keys"
echo "   - Révoquer l'ancienne clé"
echo ""
echo "3. Mettre à jour .env en production avec:"
echo "   JWT_SECRET_KEY=$NEW_JWT_SECRET"
echo "   GOOGLE_CLIENT_ID=<nouvelle-clé>"
echo "   OPENAI_API_KEY=<nouvelle-clé>"
echo ""
echo "4. Mettre à jour extension/manifest.json avec le nouveau CLIENT_ID"
echo ""
echo "5. Si vous avez nettoyé Git, pusher les changements:"
echo "   git push origin --force --all"
echo ""
echo "⚠️  Ne JAMAIS commiter le nouveau .env!"
echo ""
