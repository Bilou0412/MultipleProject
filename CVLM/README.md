# CVLM - Générateur de lettres de motivation

## 🎯 Objectif
Ce projet permet de générer automatiquement une lettre de motivation à partir :
- d’un **CV** (PDF)
- d’une **fiche de poste** (texte ou PDF)
en utilisant une API LLM.

## 🧱 Architecture
```

project_root/
│
├── main.py                  # Point d’entrée
├── app/
│   ├── file_manager.py      # Gestion des fichiers et extraction de texte
│   ├── llm_client.py        # Communication avec l’API LLM
│   ├── pdf_generator.py     # Génération du PDF final
│   └── job_application_service.py  # Orchestration du flux
└── data/
├── input/               # CV et fiches de poste
└── output/              # Lettres générées

````

## ⚙️ Installation
```bash
pip install -r requirements.txt
````

## 🚀 Utilisation

```bash
python main.py
```

## 🧠 À venir

* Extraction des CV multi-format (PDF, DOCX)
* Nettoyage et parsing automatique
* Génération de PDF final

```
