#!/bin/bash
set -e

echo "🚀 Démarrage de l'application CVLM..."

# Attendre que PostgreSQL soit prêt
echo "⏳ Attente de PostgreSQL..."
until pg_isready -h postgres -p 5432 -U cvlm_user; do
  echo "PostgreSQL n'est pas encore prêt - attente..."
  sleep 2
done

echo "✅ PostgreSQL est prêt !"

# Initialiser la base de données si nécessaire
echo "🔧 Initialisation de la base de données..."
python -c "
from infrastructure.database.config import init_database
try:
    init_database()
    print('✅ Base de données initialisée')
except Exception as e:
    print(f'ℹ️  Base de données déjà initialisée ou erreur: {e}')
"

echo "🎉 Démarrage de l'application..."

# Exécuter la commande passée en argument
exec "$@"
