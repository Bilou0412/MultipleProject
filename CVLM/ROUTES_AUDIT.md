# 📊 Audit Complet des Routes API

**Date**: 2025-01-XX  
**Objectif**: Identifier quelles routes suivent le pattern Use Case vs. celles contenant de la logique métier

---

## 📈 Vue d'Ensemble

| **Catégorie** | **Nombre** | **Pourcentage** |
|---------------|------------|-----------------|
| **Total Routes** | 28 | 100% |
| **✅ Optimisées (Use Case)** | 3 | 10.7% |
| **🟢 Simples (OK sans Use Case)** | 12 | 42.9% |
| **🟡 Candidates (à optimiser)** | 9 | 32.1% |
| **🔴 Complexes (optimisation recommandée)** | 4 | 14.3% |

---

## ✅ Routes Optimisées (Use Case Pattern) - 3 routes

### 1. **POST /generate-cover-letter** (`generation.py`)
- ✅ **Status**: OPTIMISÉ
- **Use Case**: `GenerateCoverLetterUseCase` (218 lignes)
- **Complexité route**: 28 lignes (route simple, logique déléguée)
- **Logique métier**: 
  - Validation CV + crédits (UseCaseValidator)
  - Extraction job info (JobInfoExtractor)
  - Génération lettre + PDF (LetterGenerationService)
  - Historique + décompte crédits

### 2. **POST /generate-text** (`generation.py`)
- ✅ **Status**: OPTIMISÉ
- **Use Case**: `GenerateTextUseCase` (327 lignes)
- **Complexité route**: 42 lignes (route simple, logique déléguée)
- **Logique métier**:
  - Validation CV + crédits (UseCaseValidator)
  - Extraction job info (JobInfoExtractor)
  - Génération texte LLM
  - Historique + décompte crédits

### 3. **POST /upload-cv** (`cv.py`)
- ✅ **Status**: OPTIMISÉ
- **Use Case**: `UploadCvUseCase` (289 lignes)
- **Complexité route**: 28 lignes (simplifiée de 70→28 lignes)
- **Logique métier**:
  - Validation fichier (type, taille)
  - Parsing PDF (extraction texte)
  - Stockage fichier (LocalFileStorage)
  - Persistance DB + cleanup erreurs

---

## 🟢 Routes Simples (OK sans Use Case) - 12 routes

Ces routes font uniquement des opérations CRUD simples ou de la délégation directe aux services.

### **user.py** - 1 route
| Route | Logique | Lignes | Raison OK |
|-------|---------|--------|-----------|
| `GET /credits` | Retourne crédits user | 8 | Simple lecture attributs |

### **generation.py** - 1 route
| Route | Logique | Lignes | Raison OK |
|-------|---------|--------|-----------|
| `GET /list-letters` | Liste lettres + CV | 35 | Simple query + join |

### **admin.py** - 10 routes
| Route | Logique | Lignes | Raison OK |
|-------|---------|--------|-----------|
| `GET /admin/stats` | Stats dashboard | 8 | Délégation AdminService |
| `GET /admin/users` | Liste utilisateurs | 27 | Query + mapping simple |
| `GET /admin/promo-codes` | Liste codes promo | 26 | Query + mapping simple |
| `POST /admin/promo-codes/generate` | Créer code promo | 30 | Délégation PromoCodeService |
| `POST /admin/promo-codes/redeem` | Utiliser code promo | 28 | Délégation PromoCodeService |
| `POST /admin/users/promote` | Promouvoir admin | 20 | Délégation AdminService |
| `POST /admin/users/revoke` | Révoquer admin | 20 | Délégation AdminService |
| `POST /admin/users/credits` | Modifier crédits | 35 | Délégation AdminService |
| `DELETE /admin/promo-codes/{code}` | Supprimer code | 18 | Délégation AdminService |
| `PATCH /admin/promo-codes/{code}/toggle` | Toggle actif | 31 | Délégation AdminService |

**Raison**: Toutes ces routes admin **délèguent directement** aux services (AdminService, PromoCodeService). Pas de logique métier dans les routes.

---

## 🟡 Routes Candidates (Optimisation possible) - 9 routes

Ces routes contiennent une logique métier modérée qui pourrait bénéficier d'une extraction en Use Case.

### **history.py** - 6 routes

#### 1. **GET /user/history** - Liste historique avec filtres
```python
# 50 lignes de logique
- Parsing période (7/30/90 jours)
- Appel GenerationHistoryService.get_user_history()
- Mapping HistoryEntryResponse (is_downloadable, is_expired, days_until_expiration)
```
**Complexité**: 🟡 Moyenne (50 lignes)  
**Recommandation**: Pourrait être Use Case `GetUserHistoryUseCase` si logique de filtrage devient complexe

#### 2. **GET /user/history/stats** - Statistiques utilisateur
```python
# 24 lignes de logique
- Appel GenerationHistoryService.get_user_stats()
- Mapping HistoryStatsResponse
```
**Complexité**: 🟢 Faible (24 lignes)  
**Recommandation**: OK comme délégation service, mais pourrait être Use Case

#### 3. **GET /user/history/{id}/text** - Récupérer texte généré
```python
# 32 lignes de logique
- Vérification ownership (user_id == history.user_id)
- Vérification type (doit être 'text')
- Mapping HistoryTextResponse
```
**Complexité**: 🟡 Moyenne (validation ownership)  
**Recommandation**: Extraction Use Case `GetHistoryTextUseCase` (validation ownership = logique métier)

#### 4. **DELETE /user/history/{id}** - Supprimer entrée historique
```python
# 28 lignes de logique
- Appel GenerationHistoryService.delete_entry()
- Gestion erreurs (PermissionError, ValueError)
```
**Complexité**: 🟢 Faible (28 lignes)  
**Recommandation**: OK comme délégation service

#### 5. **GET /user/history/export** - Exporter historique JSON
```python
# 18 lignes de logique
- Appel GenerationHistoryService.export_user_history()
- Construction Response avec headers JSON
```
**Complexité**: 🟢 Faible (18 lignes)  
**Recommandation**: OK comme délégation service

#### 6. **GET /list-cvs** (`cv.py`) - Liste CVs utilisateur
```python
# Logique inconnue (non lue complètement)
```
**Complexité**: ❓ À analyser  
**Recommandation**: Lire le code complet pour évaluer

---

## 🔴 Routes Complexes (Optimisation RECOMMANDÉE) - 4 routes

Ces routes contiennent une **logique métier significative** qui devrait être extraite en Use Cases.

### **download.py** - 3 routes

#### 1. **GET /download-letter/{letter_id}** - Télécharger lettre PDF
```python
# 28 lignes de logique métier
1. Repository: PostgresMotivationalLetterRepository.get_by_id()
2. Validation ownership: letter.user_id != current_user.id → 403
3. File storage: file_storage.get_letter_path()
4. Validation fichier existe: Path.exists() → 404
5. Retour FileResponse
```
**Complexité**: 🔴 Haute (validation ownership + fichier)  
**Recommandation**: **Use Case `DownloadLetterUseCase`**
- Phases: (1) Get letter (2) Validate ownership (3) Check file (4) Return path

#### 2. **GET /user/history/{id}/download** - Télécharger depuis historique
```python
# 60 lignes de logique métier
1. Repository: PostgresGenerationHistoryRepository.get_by_id()
2. Validation ownership: history.user_id != current_user.id → 403
3. Validation downloadable: history.is_downloadable() → 410
4. Validation fichier: os.path.exists() → 404
5. Construction filename propre:
   - Extraction company_name + job_title
   - Nettoyage caractères spéciaux
   - Suppression underscores multiples
6. Retour FileResponse
```
**Complexité**: 🔴 Très Haute (60 lignes, logique filename complexe)  
**Recommandation**: **Use Case `DownloadHistoryFileUseCase`**
- Phases: (1) Get history (2) Validate ownership (3) Check downloadable (4) Build filename (5) Return file

#### 3. **DELETE /cleanup/{cv_id}** - Supprimer CV + fichiers
```python
# 24 lignes de logique métier
1. Service: CvValidationService.get_and_validate_cv() (validation ownership)
2. File storage: file_storage.delete_cv()
3. Repository: cv_repo.delete()
4. Logging
```
**Complexité**: 🔴 Haute (suppression fichier + DB, transaction implicite)  
**Recommandation**: **Use Case `DeleteCvUseCase`**
- Phases: (1) Validate CV + ownership (2) Delete file (3) Delete DB (4) Rollback si erreur

### **auth.py** - 1 route (à analyser)

#### 4. **POST /google** - Authentification Google OAuth
```python
# Logique inconnue (non lue complètement)
```
**Complexité**: ❓ À analyser  
**Recommandation**: Lire le code complet (probablement complexe: OAuth flow, JWT, création user)

---

## 🎯 Recommandations d'Optimisation

### **Priorité 1 - CRITIQUE** (4 Use Cases)

#### 1. **DownloadHistoryFileUseCase** (download.py ligne 79)
**Raison**: 60 lignes, logique complexe de filename + validations multiples  
**Impact**: Route la plus complexe du système  
**Bénéfices**:
- ✅ Extraction logique filename (réutilisable)
- ✅ Testabilité (mock file_storage, repo)
- ✅ Séparation responsabilités

```python
# Phases Use Case:
1. Get history entry
2. Validate ownership (user_id check)
3. Validate downloadable (expiration, status)
4. Build filename (company + job_title cleaning)
5. Check file exists
6. Return file path
```

#### 2. **DeleteCvUseCase** (download.py ligne 155)
**Raison**: Suppression fichier + DB, risque incohérence  
**Impact**: Opération critique (perte données si erreur)  
**Bénéfices**:
- ✅ Transaction explicite (rollback si erreur file)
- ✅ Cleanup complet (file + DB atomique)
- ✅ Testabilité

```python
# Phases Use Case:
1. Validate CV + ownership
2. Delete file (LocalFileStorage)
3. Delete DB record (CvRepository)
4. Rollback si erreur (transaction)
```

#### 3. **DownloadLetterUseCase** (download.py ligne 29)
**Raison**: Validation ownership + file check  
**Impact**: Sécurité (ownership) + UX (404 vs 500)  
**Bénéfices**:
- ✅ Logique validation centralisée
- ✅ Testabilité

```python
# Phases Use Case:
1. Get letter
2. Validate ownership
3. Check file exists
4. Return file path
```

#### 4. **AuthenticateWithGoogleUseCase** (auth.py ligne 20)
**Raison**: OAuth flow complexe (probablement)  
**Impact**: Sécurité critique  
**Bénéfices**:
- ✅ Logique OAuth isolée
- ✅ Testabilité (mock Google API)

---

### **Priorité 2 - OPTIONNEL** (2 Use Cases)

#### 5. **GetHistoryTextUseCase** (history.py ligne 161)
**Raison**: Validation ownership + type check  
**Complexité**: Moyenne (32 lignes)  
**Bénéfices**: Logique validation ownership réutilisable

#### 6. **GetUserHistoryUseCase** (history.py ligne 27)
**Raison**: Parsing période + filtres  
**Complexité**: Moyenne (50 lignes)  
**Bénéfices**: Centraliser logique filtrage si complexification future

---

## 📊 Métriques Détaillées

### Répartition par Fichier

| **Fichier** | **Total Routes** | **Optimisées** | **Simples** | **Candidates** | **Complexes** |
|-------------|------------------|----------------|-------------|----------------|---------------|
| `generation.py` | 4 | 2 ✅ | 1 🟢 | 0 | 0 |
| `cv.py` | 2 | 1 ✅ | 0 | 1 🟡 | 0 |
| `download.py` | 3 | 0 | 0 | 0 | 3 🔴 |
| `history.py` | 6 | 0 | 0 | 6 🟡 | 0 |
| `user.py` | 1 | 0 | 1 🟢 | 0 | 0 |
| `admin.py` | 10 | 0 | 10 🟢 | 0 | 0 |
| `auth.py` | 2 | 0 | 0 | 0 | 1 🔴 (+ 1 ❓) |

### Complexité par Ligne de Code

| **Catégorie** | **Lignes Moyennes** | **Range** |
|---------------|---------------------|-----------|
| **Optimisées (Use Case)** | 28-42 lignes | Route simple |
| **Simples (délégation service)** | 8-35 lignes | Légères |
| **Candidates** | 18-50 lignes | Modérées |
| **Complexes** | 24-60 lignes | Lourdes |

---

## 🏗️ Plan d'Action Recommandé

### **Phase 1 - Download Routes** (Impact critique)
1. ✅ Créer `DownloadHistoryFileUseCase` (60 lignes → 30 lignes route)
2. ✅ Créer `DeleteCvUseCase` (24 lignes → 15 lignes route)
3. ✅ Créer `DownloadLetterUseCase` (28 lignes → 15 lignes route)

**Résultat attendu**:
- 3 routes simplifiées (112 lignes → 60 lignes = **-46%**)
- Transaction atomique pour `DeleteCvUseCase`
- Logique filename extractible en service helper

### **Phase 2 - Auth Route** (Sécurité)
4. ✅ Analyser `/google` (auth.py)
5. ✅ Créer `AuthenticateWithGoogleUseCase` si logique complexe

### **Phase 3 - History Routes** (Optionnel)
6. ⚠️ Évaluer si `GetHistoryTextUseCase` nécessaire
7. ⚠️ Évaluer si `GetUserHistoryUseCase` nécessaire

---

## 🎓 Principes d'Optimisation

### **Quand extraire en Use Case ?**
✅ **OUI** si la route contient:
- Validation métier (ownership, crédits, statut)
- Logique multi-étapes (5+ étapes)
- Appels multiples aux repositories/services
- Gestion d'erreurs complexe
- Transactions (file + DB)

❌ **NON** si la route:
- Fait juste une délégation simple à un service
- N'a qu'une seule opération CRUD
- < 20 lignes de logique

### **Pattern Use Case Actuel**
```python
# Route (adapter léger)
@router.post("/endpoint")
async def endpoint(
    data: Request,
    user: User = Depends(get_current_user),
    use_case: UseCase = Depends(get_use_case)
):
    input_data = UseCaseInput(...)
    output = use_case.execute(input_data, user)
    return Response(output)

# Use Case (orchestration métier)
class UseCase:
    def execute(self, input: Input, user: User) -> Output:
        # Phase 1: Validation
        # Phase 2: Business logic
        # Phase 3: Side effects (DB, file)
        # Phase 4: Return result
```

---

## 📝 Conclusion

### État Actuel
- **10.7%** des routes suivent le pattern Use Case (3/28)
- **42.9%** sont OK sans Use Case (délégation simple)
- **46.4%** pourraient bénéficier d'une optimisation (13 routes)

### Objectif Cible (après optimisation)
- **25%** avec Use Case (7/28 routes) - Les plus complexes
- **75%** délégation service (21/28 routes) - Les simples

### Impact Optimisation Complète
- **4 Use Cases critiques** à créer (download + auth)
- **~150 lignes** de logique métier extraites des routes
- **Testabilité** améliorée (mock repositories/services)
- **Maintenabilité** améliorée (logique centralisée)

---

**Prochaine étape**: Commencer Phase 1 avec `DownloadHistoryFileUseCase` ?
