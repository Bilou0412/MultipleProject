#!/bin/bash

# Script de test du workflow d'authentification complet
echo "🧪 Test du workflow d'authentification CVLM"
echo "============================================"

API_URL="http://localhost:8000"

echo ""
echo "1️⃣ Test endpoint racine..."
curl -s -o /dev/null -w "Status: %{http_code}\n" $API_URL/

echo ""
echo "2️⃣ Test endpoint docs (Swagger)..."
curl -s -o /dev/null -w "Status: %{http_code}\n" $API_URL/docs

echo ""
echo "3️⃣ Test authentification Google (token invalide - doit retourner 401)..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST $API_URL/auth/google \
  -H "Content-Type: application/json" \
  -d '{"token": "fake_token"}')
echo "$RESPONSE"

echo ""
echo "4️⃣ Test upload CV sans authentification (doit retourner 401)..."
curl -s -w "\nStatus: %{http_code}\n" -X POST $API_URL/upload-cv \
  -F "cv_file=@README.md"

echo ""
echo "5️⃣ Test list CVs sans authentification (doit retourner 401)..."
curl -s -w "\nStatus: %{http_code}\n" $API_URL/list-cvs

echo ""
echo "6️⃣ Test crédits sans authentification (doit retourner 401)..."
curl -s -w "\nStatus: %{http_code}\n" $API_URL/user/credits

echo ""
echo "7️⃣ Vérification des logs d'erreur récents..."
echo "Dernières erreurs dans les logs:"
docker logs cvlm_api --tail 50 2>&1 | grep -E "(ERROR|WARNING|401|500)" | tail -10

echo ""
echo "✅ Tests terminés"
echo ""
echo "📋 Résumé:"
echo "- Tous les endpoints protégés doivent retourner 401 sans token"
echo "- L'authentification Google doit retourner une erreur pour un token invalide"
echo "- Vérifiez les logs pour d'autres erreurs potentielles"
