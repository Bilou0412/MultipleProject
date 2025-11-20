"""
Service: Extraction d'informations depuis les URLs d'offres d'emploi

Ce service centralise la logique d'extraction de company_name et job_title
depuis les URLs de différentes plateformes (Welcome to the Jungle, etc.).

Utilisé par:
- GenerateCoverLetterUseCase
- GenerateTextUseCase

Réduit la duplication de code entre les Use Cases.
"""
from typing import Tuple, Optional
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)


class JobInfoExtractor:
    """
    Service pour extraire les informations métier depuis les URLs d'offres d'emploi.
    
    Supporte actuellement:
    - Welcome to the Jungle
    
    Extensible pour d'autres plateformes (LinkedIn, Indeed, etc.)
    """
    
    def extract_from_url(self, job_url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extrait le nom de l'entreprise et le titre du poste depuis l'URL.
        
        Args:
            job_url: URL de l'offre d'emploi
        
        Returns:
            Tuple (company_name, job_title)
            Retourne (None, None) si extraction échoue
        
        Example:
            >>> extractor = JobInfoExtractor()
            >>> company, title = extractor.extract_from_url(
            ...     "https://www.welcometothejungle.com/fr/companies/acme-corp/jobs/senior-developer_paris"
            ... )
            >>> print(company, title)
            'Acme Corp' 'Senior Developer'
        """
        company_name = None
        job_title = None
        
        try:
            if 'welcometothejungle' in job_url.lower():
                company_name, job_title = self._extract_from_wttj(job_url)
                logger.debug(
                    f"[JobInfoExtractor] Extraction WTTJ: company='{company_name}', title='{job_title}'"
                )
            else:
                logger.debug(
                    f"[JobInfoExtractor] Plateforme non supportée: {job_url[:50]}"
                )
        
        except Exception as e:
            logger.warning(
                f"[JobInfoExtractor] Erreur extraction (non bloquant): {e}"
            )
        
        return company_name, job_title
    
    def _extract_from_wttj(self, job_url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extrait depuis Welcome to the Jungle.
        
        Format URL attendu:
        https://www.welcometothejungle.com/fr/companies/{company-slug}/jobs/{job-slug}_{location}
        
        Args:
            job_url: URL Welcome to the Jungle
        
        Returns:
            Tuple (company_name, job_title)
        """
        parts = job_url.split('/')
        
        # Vérifier qu'on a assez de parties dans l'URL
        if len(parts) < 6:
            logger.debug(f"[JobInfoExtractor] URL WTTJ trop courte: {job_url}")
            return None, None
        
        # Extraire company (partie 4) et job (partie 6)
        company_slug = parts[4]
        job_slug = parts[6].split('?')[0]  # Supprimer query params
        
        # Formatter: "senior-developer" → "Senior Developer"
        company_name = company_slug.replace('-', ' ').title()
        job_title = job_slug.replace('-', ' ').title()
        
        return company_name, job_title
