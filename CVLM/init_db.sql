-- Script d'initialisation optionnel pour PostgreSQL
-- Exécuté automatiquement au premier démarrage du conteneur

-- La base de données et l'utilisateur sont déjà créés via les variables d'environnement
-- Ce fichier peut contenir des configurations supplémentaires

-- Créer des extensions utiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Pour la recherche texte

-- Log
\echo 'Base de données CVLM initialisée avec succès'
