"""
Port pour le stockage des fichiers (PDFs)
"""
from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path


class FileStorage(ABC):
    """
    Interface pour le stockage des fichiers PDF
    Permet de séparer la logique de stockage (local, S3, etc.)
    """
    
    @abstractmethod
    def save_file(self, file_content: bytes, filename: str, subfolder: str = "") -> str:
        """
        Sauvegarde un fichier et retourne son chemin/URL
        
        Args:
            file_content: Contenu du fichier en bytes
            filename: Nom du fichier
            subfolder: Sous-dossier optionnel (ex: 'cvs', 'letters')
        
        Returns:
            Chemin ou URL du fichier sauvegardé
        """
        pass
    
    @abstractmethod
    def get_file(self, file_path: str) -> Optional[bytes]:
        """
        Récupère le contenu d'un fichier
        
        Args:
            file_path: Chemin ou URL du fichier
        
        Returns:
            Contenu du fichier en bytes, ou None si non trouvé
        """
        pass
    
    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """
        Supprime un fichier
        
        Args:
            file_path: Chemin ou URL du fichier
        
        Returns:
            True si suppression réussie, False sinon
        """
        pass
    
    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """
        Vérifie si un fichier existe
        
        Args:
            file_path: Chemin ou URL du fichier
        
        Returns:
            True si le fichier existe, False sinon
        """
        pass
    
    @abstractmethod
    def get_file_size(self, file_path: str) -> Optional[int]:
        """
        Récupère la taille d'un fichier
        
        Args:
            file_path: Chemin ou URL du fichier
        
        Returns:
            Taille en bytes, ou None si fichier non trouvé
        """
        pass
