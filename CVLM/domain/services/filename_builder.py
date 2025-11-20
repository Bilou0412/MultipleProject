"""
Service de construction de noms de fichiers propres
Centralise la logique de nettoyage et formatage des noms de fichiers
"""

from typing import Optional


class FilenameBuilder:
    """
    Service helper pour construire des noms de fichiers propres.
    
    Responsabilités:
    - Concaténer company_name + job_title
    - Nettoyer caractères spéciaux (espaces, slashes)
    - Supprimer underscores multiples
    - Fournir fallback si pas de données
    - Ajouter extension
    
    Utilisé par:
    - DownloadHistoryFileUseCase
    - Futurs téléchargements de lettres/documents
    """
    
    DEFAULT_FILENAME = "lettre_motivation"
    
    def build_pdf_filename(
        self,
        company_name: Optional[str] = None,
        job_title: Optional[str] = None
    ) -> str:
        """
        Construit un nom de fichier PDF propre à partir de company_name et job_title.
        
        Args:
            company_name: Nom de l'entreprise (peut être None)
            job_title: Titre du poste (peut être None)
        
        Returns:
            Nom de fichier propre avec extension .pdf
            Exemple: "Google_Software_Engineer.pdf"
        
        Process:
        1. Extraire les parties non vides (company, job)
        2. Joindre avec underscore
        3. Nettoyer caractères spéciaux
        4. Supprimer underscores multiples
        5. Ajouter .pdf
        """
        # Phase 1: Extraire parties non vides
        parts = []
        
        if company_name and company_name.strip():
            parts.append(company_name.strip())
        
        if job_title and job_title.strip():
            parts.append(job_title.strip())
        
        # Phase 2: Joindre ou fallback
        if parts:
            filename = '_'.join(parts)
        else:
            filename = self.DEFAULT_FILENAME
        
        # Phase 3: Nettoyer caractères spéciaux
        filename = self._clean_filename(filename)
        
        # Phase 4: Ajouter extension
        return f"{filename}.pdf"
    
    def _clean_filename(self, filename: str) -> str:
        """
        Nettoie un nom de fichier des caractères problématiques.
        
        Args:
            filename: Nom de fichier brut
        
        Returns:
            Nom de fichier nettoyé
        
        Opérations:
        - Remplacer espaces par underscores
        - Remplacer slashes par underscores
        - Supprimer underscores multiples
        - Trim underscores début/fin
        """
        # Remplacer espaces et slashes
        cleaned = filename.replace(' ', '_').replace('/', '_')
        
        # Supprimer underscores multiples
        while '__' in cleaned:
            cleaned = cleaned.replace('__', '_')
        
        # Supprimer underscores au début et à la fin
        cleaned = cleaned.strip('_')
        
        return cleaned
