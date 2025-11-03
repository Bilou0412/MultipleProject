# 🧭 TEMPLATE — MÉTHODOLOGIE DE CRÉATION DE PROCESSUS AUTOMATISÉ

> **Objectif du document :** Décrire, concevoir et structurer un processus automatisé (technique, IA, data, etc.) de manière claire, modulaire et exécutable.
> **Auteur :** [à compléter]
> **Date :** [à compléter]
> **Version :** [à compléter]

---

## ⚙️ STEP 1 — Définir le flux global

**🎯 Objectif :** Comprendre le parcours complet de la donnée (de l’entrée à la sortie).

**🧩 Flux principal :**

```
[Entrée] → [Traitement] → [Sortie]
```

**🧠 Description du cas d’usage :**

> Expliquer ici ce que fait le système (ex : “Le système reçoit un CV et une offre, les envoie à un LLM, et génère un PDF final.”)

**💬 Questions à se poser :**

* Quelle est la source de la donnée (fichier, API, user, événement) ?
* Quelles transformations doivent être appliquées ?
* Quelle forme prend le résultat final ?

---

## 🧠 STEP 2 — Identifier les rôles et responsabilités

> Séparer les étapes pour éviter le mélange des responsabilités.
> Chaque étape = un rôle clair et testable.

| Étape              | Rôle                           | Responsabilité principale            | Notes |
| ------------------ | ------------------------------ | ------------------------------------ | ----- |
| 1️⃣ Entrée         | [ex : Collecte des fichiers]   | [lecture / validation / préparation] |       |
| 2️⃣ Traitement     | [ex : Envoi à une API LLM]     | [analyse / calcul / enrichissement]  |       |
| 3️⃣ Logique métier | [ex : Orchestration du flux]   | [pilotage / dépendances / contrôle]  |       |
| 4️⃣ Sortie         | [ex : Génération d’un rapport] | [mise en forme / export]             |       |

**💬 Questions à se poser :**

* Chaque étape a-t-elle une mission unique ?
* Les responsabilités sont-elles indépendantes ?
* Quelles dépendances ou erreurs possibles entre les étapes ?

---

## 🧩 STEP 3 — Traduction en composants techniques

> Transformer les étapes en classes ou modules techniques réutilisables.

| Composant                  | Rôle         | Description   | Entrées / Sorties        | Outils utilisés      |
| -------------------------- | ------------ | ------------- | ------------------------ | -------------------- |
| **InputManager**           | Entrée       | [description] | [ex : .csv → dict]       | [ex : pandas, os]    |
| **Processor / LLMClient**  | Traitement   | [description] | [ex : dict → texte]      | [ex : API OpenAI]    |
| **OutputGenerator**        | Sortie       | [description] | [ex : texte → PDF]       | [ex : reportlab]     |
| **Orchestrator / Service** | Coordination | [description] | [coordonne tout le flux] | [ex : asyncio, logs] |

**💬 Questions à se poser :**

* Quelle interface entre chaque composant ?
* Comment gérer erreurs et logs ?
* Peut-on remplacer un composant sans casser le reste ?

---

## 🏗️ STEP 4 — Architecture projet

> Définir la structure standard du projet pour garder une cohérence dans tous les processus.

```
project_root/
│
├── main.py                       # Point d'entrée
│
├── app/
│   ├── __init__.py
│   ├── input_manager.py           # Entrée
│   ├── processor.py               # Traitement
│   ├── output_generator.py        # Sortie
│   └── orchestrator.py            # Coordination
│
├── data/
│   ├── input/                     # Fichiers sources
│   └── output/                    # Résultats générés
│
├── config.py                      # Configuration, clés, variables
│
└── requirements.txt               # Dépendances
```

**💬 Questions à se poser :**

* Où sont les données temporaires ?
* Comment gérer les environnements (dev / prod) ?
* Comment sécuriser les clés API et credentials ?

---

## 🔄 STEP 5 — Boucle d’amélioration et de test

> Préparer le terrain pour l’itération, la mesure et la fiabilité.

| Axe             | Objectif               | Indicateurs | Améliorations possibles       |
| --------------- | ---------------------- | ----------- | ----------------------------- |
| **Performance** | Temps d’exécution      | [à remplir] | [optimisation, batchs]        |
| **Résilience**  | Gestion des erreurs    | [à remplir] | [retries, fallback]           |
| **Qualité**     | Cohérence du résultat  | [à remplir] | [tests unitaires, validation] |
| **Maintenance** | Simplicité d’évolution | [à remplir] | [documentation, refactor]     |

**💬 Questions à se poser :**

* Qu’est-ce qui peut échouer et comment le détecter ?
* Comment mesurer la performance du flux ?
* Quelle couverture de test minimale viser ?

---

## 📘 STEP 6 — Documentation de synthèse

> Clôturer la conception avec une vue synthétique.

| Étape          | Ce qui a été fait | Ce qui a été appris / amélioré |
| -------------- | ----------------- | ------------------------------ |
| Idée initiale  | [à compléter]     | [à compléter]                  |
| Analyse        | [à compléter]     | [à compléter]                  |
| Conception OOP | [à compléter]     | [à compléter]                  |
| Architecture   | [à compléter]     | [à compléter]                  |
| Évaluation     | [à compléter]     | [à compléter]                  |

---

## 🧭 STEP 7 — Check-list de conception rapide

> À passer en revue avant de valider un flux.

* [ ] Le flux **entrée → traitement → sortie** est défini
* [ ] Les **responsabilités** sont séparées
* [ ] Les **composants** sont indépendants et testables
* [ ] L’**architecture de fichiers** est propre et cohérente
* [ ] La **gestion d’erreurs et de logs** est en place
* [ ] La **configuration** est centralisée
* [ ] Les **tests** de base sont définis
* [ ] Les **prochaines améliorations** sont notées

---

## 🔧 STEP 8 — Fiche récapitulative projet

| Élément                     | Détail                                  |
| --------------------------- | --------------------------------------- |
| **Nom du processus**        | [à compléter]                           |
| **But principal**           | [à compléter]                           |
| **Entrées**                 | [formats, sources]                      |
| **Sorties**                 | [formats, destinations]                 |
| **Outils / APIs**           | [LLM, libs, scripts]                    |
| **Fréquence / déclencheur** | [manuelle / planifiée / événementielle] |
| **Responsable**             | [à compléter]                           |
| **Dernière mise à jour**    | [date]                                  |

---

