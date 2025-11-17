"""
Implémentation locale du FileStorage
Stocke les fichiers sur le système de fichiers local
"""
from pathlib import Path
from typing import Optional
import os
import shutil

from domain.ports.file_storage import FileStorage


class LocalFileStorage(FileStorage):
    """
    Stockage local des fichiers PDF
    """
    
    def __init__(self, base_path: str = "data/files"):
        """
        Args:
            base_path: Répertoire de base pour le stockage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_file(self, file_content: bytes, filename: str, subfolder: str = "") -> str:
        """
        Sauvegarde un fichier localement
        
        Returns:
            Chemin relatif du fichier sauvegardé
        """
        # Crée le sous-dossier si nécessaire
        target_dir = self.base_path / subfolder if subfolder else self.base_path
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Chemin complet du fichier
        file_path = target_dir / filename
        
        # Sauvegarde le fichier
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Retourne le chemin relatif
        return str(file_path.relative_to(self.base_path))
    
    def get_file(self, file_path: str) -> Optional[bytes]:
        """
        Récupère le contenu d'un fichier
        """
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            return None
        
        try:
            with open(full_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"⚠️ Erreur lecture fichier {file_path}: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """
        Supprime un fichier
        """
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            return False
        
        try:
            full_path.unlink()
            return True
        except Exception as e:
            print(f"⚠️ Erreur suppression fichier {file_path}: {e}")
            return False
    
    def file_exists(self, file_path: str) -> bool:
        """
        Vérifie si un fichier existe
        """
        full_path = self.base_path / file_path
        return full_path.exists()
    
    def get_file_size(self, file_path: str) -> Optional[int]:
        """
        Récupère la taille d'un fichier
        """
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            return None
        
        try:
            return full_path.stat().st_size
        except Exception as e:
            print(f"⚠️ Erreur récupération taille {file_path}: {e}")
            return None
    
    # === Méthodes spécifiques pour CVs ===
    
    def save_cv(self, cv_id: str, content: bytes, filename: str) -> str:
        """
        Sauvegarde un CV
        
        Args:
            cv_id: ID unique du CV
            content: Contenu binaire du fichier PDF
            filename: Nom original du fichier
            
        Returns:
            Chemin complet du fichier sauvegardé
        """
        cv_dir = self.base_path / "cvs"
        cv_dir.mkdir(parents=True, exist_ok=True)
        
        # Nom du fichier : cv_{id}.pdf
        file_path = cv_dir / f"cv_{cv_id}.pdf"
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return str(file_path)
    
    def get_cv_path(self, cv_id: str) -> Optional[str]:
        """
        Récupère le chemin d'un CV
        
        Args:
            cv_id: ID du CV
            
        Returns:
            Chemin complet du fichier ou None si inexistant
        """
        file_path = self.base_path / "cvs" / f"cv_{cv_id}.pdf"
        
        if file_path.exists():
            return str(file_path)
        
        return None
    
    def delete_cv(self, cv_id: str) -> bool:
        """
        Supprime un CV
        
        Args:
            cv_id: ID du CV à supprimer
            
        Returns:
            True si supprimé, False sinon
        """
        file_path = self.base_path / "cvs" / f"cv_{cv_id}.pdf"
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            return True
        except Exception as e:
            print(f"⚠️ Erreur suppression CV {cv_id}: {e}")
            return False
    
    # === Méthodes spécifiques pour lettres de motivation ===
    
    def save_letter(self, letter_id: str, content: bytes, filename: str) -> str:
        """
        Sauvegarde une lettre de motivation
        
        Args:
            letter_id: ID unique de la lettre
            content: Contenu binaire du fichier PDF
            filename: Nom original du fichier
            
        Returns:
            Chemin complet du fichier sauvegardé
        """
        letter_dir = self.base_path / "letters"
        letter_dir.mkdir(parents=True, exist_ok=True)
        
        # Nom du fichier : letter_{id}.pdf
        file_path = letter_dir / f"letter_{letter_id}.pdf"
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return str(file_path)
    
    def get_letter_path(self, letter_id: str) -> Optional[str]:
        """
        Récupère le chemin d'une lettre
        
        Args:
            letter_id: ID de la lettre
            
        Returns:
            Chemin complet du fichier ou None si inexistant
        """
        file_path = self.base_path / "letters" / f"letter_{letter_id}.pdf"
        
        if file_path.exists():
            return str(file_path)
        
        return None
    
    def delete_letter(self, letter_id: str) -> bool:
        """
        Supprime une lettre de motivation
        
        Args:
            letter_id: ID de la lettre à supprimer
            
        Returns:
            True si supprimé, False sinon
        """
        file_path = self.base_path / "letters" / f"letter_{letter_id}.pdf"
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            return True
        except Exception as e:
            print(f"⚠️ Erreur suppression lettre {letter_id}: {e}")
            return False

    
    def get_absolute_path(self, file_path: str) -> str:
        """
        Récupère le chemin absolu d'un fichier
        
        Args:
            file_path: Chemin relatif du fichier
        
        Returns:
            Chemin absolu du fichier
        """
        return str((self.base_path / file_path).absolute())
