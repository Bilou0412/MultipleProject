"""
Service pour gérer l'historique des générations
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import os

from domain.entities.generation_history import GenerationHistory
from domain.ports.generation_history_repository import GenerationHistoryRepository
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)


class GenerationHistoryService:
    """Service métier pour l'historique des générations"""
    
    def __init__(self, history_repo: GenerationHistoryRepository):
        self.history_repo = history_repo
    
    def record_generation(
        self,
        user_id: str,
        gen_type: str,  # 'pdf' ou 'text'
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
        job_url: Optional[str] = None,
        cv_filename: Optional[str] = None,
        cv_id: Optional[str] = None,
        file_path: Optional[str] = None,
        text_content: Optional[str] = None,
        status: str = 'success',
        error_message: Optional[str] = None
    ) -> GenerationHistory:
        """
        Enregistre une nouvelle génération dans l'historique
        Appelé après chaque génération PDF ou texte
        """
        history = GenerationHistory(
            id=None,  # Auto-généré
            user_id=user_id,
            type=gen_type,
            job_title=job_title,
            company_name=company_name,
            job_url=job_url,
            cv_filename=cv_filename,
            cv_id=cv_id,
            file_path=file_path,
            text_content=text_content,
            status=status,
            error_message=error_message,
            created_at=datetime.now(),
            file_expires_at=datetime.now() + timedelta(days=90) if gen_type == 'pdf' else None
        )
        
        created = self.history_repo.create(history)
        logger.info(f"Génération {gen_type} enregistrée pour user {user_id}")
        return created
    
    def get_user_history(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 50,
        search: Optional[str] = None,
        type_filter: Optional[str] = None,
        period_days: Optional[int] = None
    ) -> Dict:
        """Récupère l'historique paginé d'un utilisateur"""
        return self.history_repo.get_user_history(
            user_id=user_id,
            page=page,
            per_page=per_page,
            search=search,
            type_filter=type_filter,
            period_days=period_days
        )
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Récupère les statistiques d'un utilisateur"""
        return self.history_repo.get_user_stats(user_id)
    
    def delete_entry(self, history_id: str, user_id: str) -> None:
        """
        Supprime une entrée de l'historique
        Vérifie que l'entrée appartient bien à l'utilisateur
        """
        history = self.history_repo.get_by_id(history_id)
        
        if not history:
            raise ValueError(f"Entrée {history_id} introuvable")
        
        if history.user_id != user_id:
            raise PermissionError(f"Accès refusé : cette entrée ne vous appartient pas")
        
        # Supprimer le fichier physique si existe
        if history.file_path and os.path.exists(history.file_path):
            try:
                os.remove(history.file_path)
                logger.info(f"Fichier supprimé: {history.file_path}")
            except Exception as e:
                logger.warning(f"Erreur suppression fichier: {e}")
        
        self.history_repo.delete(history_id)
        logger.info(f"Entrée historique supprimée: {history_id}")
    
    def regenerate_pdf(
        self,
        history_id: str,
        user_id: str,
        new_file_path: str
    ) -> GenerationHistory:
        """
        Met à jour l'historique après régénération d'un PDF
        Utilisé quand le fichier a expiré et que l'user régénère
        """
        history = self.history_repo.get_by_id(history_id)
        
        if not history:
            raise ValueError(f"Entrée {history_id} introuvable")
        
        if history.user_id != user_id:
            raise PermissionError(f"Accès refusé")
        
        # Mettre à jour avec le nouveau fichier
        history.file_path = new_file_path
        history.file_expires_at = datetime.now() + timedelta(days=90)
        
        updated = self.history_repo.update(history)
        logger.info(f"PDF régénéré pour historique {history_id}")
        return updated
    
    def cleanup_expired_files(self) -> int:
        """
        Nettoie les fichiers expirés (>90 jours)
        À appeler via un cron job quotidien
        """
        expired_entries = self.history_repo.get_expired_files()
        cleaned = 0
        
        for entry in expired_entries:
            if entry.file_path and os.path.exists(entry.file_path):
                try:
                    os.remove(entry.file_path)
                    cleaned += 1
                    logger.info(f"Fichier expiré supprimé: {entry.file_path}")
                except Exception as e:
                    logger.error(f"Erreur suppression {entry.file_path}: {e}")
            
            # Mettre à jour l'entrée (garder métadonnées, effacer path)
            entry.file_path = None
            self.history_repo.update(entry)
        
        logger.info(f"Cleanup terminé: {cleaned} fichiers supprimés")
        return cleaned
    
    def export_user_history(self, user_id: str) -> Dict:
        """
        Exporte tout l'historique d'un utilisateur en JSON
        Pour backup ou portabilité
        """
        result = self.history_repo.get_user_history(
            user_id=user_id,
            page=1,
            per_page=10000,  # Tout récupérer
            search=None,
            type_filter=None,
            period_days=None
        )
        
        # Formater pour export
        export_data = {
            "export_date": datetime.now().isoformat(),
            "user_id": user_id,
            "total_generations": result["total"],
            "generations": [
                {
                    "id": item.id,
                    "type": item.type,
                    "job_title": item.job_title,
                    "company_name": item.company_name,
                    "job_url": item.job_url,
                    "cv_filename": item.cv_filename,
                    "text_content": item.text_content if item.type == 'text' else None,
                    "status": item.status,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "is_downloadable": item.is_downloadable(),
                    "days_until_expiration": item.days_until_expiration()
                }
                for item in result["items"]
            ]
        }
        
        logger.info(f"Export historique pour user {user_id}: {result['total']} entrées")
        return export_data
