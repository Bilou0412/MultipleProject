"""
Implémentation PostgreSQL du repository GenerationHistory
"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func
from datetime import datetime, timedelta
import uuid
import math

from domain.entities.generation_history import GenerationHistory
from domain.ports.generation_history_repository import GenerationHistoryRepository
from infrastructure.database.models import GenerationHistoryModel
from infrastructure.adapters.logger_config import setup_logger

logger = setup_logger(__name__)


class PostgresGenerationHistoryRepository(GenerationHistoryRepository):
    """Implémentation PostgreSQL pour l'historique des générations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, history: GenerationHistory) -> GenerationHistory:
        """Crée une nouvelle entrée dans l'historique"""
        if not history.id:
            history.id = str(uuid.uuid4())
        
        if not history.created_at:
            history.created_at = datetime.now()
        
        model = self._entity_to_model(history)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        
        logger.info(f"Historique créé: {history.type} pour {history.user_id}")
        return self._model_to_entity(model)
    
    def get_by_id(self, history_id: str) -> Optional[GenerationHistory]:
        """Récupère une entrée par son ID"""
        model = self.db.query(GenerationHistoryModel).filter(
            GenerationHistoryModel.id == history_id
        ).first()
        
        return self._model_to_entity(model) if model else None
    
    def get_user_history(
        self, 
        user_id: str, 
        page: int = 1, 
        per_page: int = 50,
        search: Optional[str] = None,
        type_filter: Optional[str] = None,
        period_days: Optional[int] = None
    ) -> Dict:
        """Récupère l'historique d'un utilisateur avec pagination et filtres"""
        query = self.db.query(GenerationHistoryModel).filter(
            GenerationHistoryModel.user_id == user_id
        )
        
        # Filtre recherche (entreprise ou poste)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    GenerationHistoryModel.job_title.ilike(search_pattern),
                    GenerationHistoryModel.company_name.ilike(search_pattern)
                )
            )
        
        # Filtre par type
        if type_filter and type_filter in ['pdf', 'text']:
            query = query.filter(GenerationHistoryModel.type == type_filter)
        
        # Filtre par période
        if period_days:
            since_date = datetime.now() - timedelta(days=period_days)
            query = query.filter(GenerationHistoryModel.created_at >= since_date)
        
        # Total
        total = query.count()
        
        # Pagination
        items = query.order_by(
            desc(GenerationHistoryModel.created_at)
        ).offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": math.ceil(total / per_page) if total > 0 else 0,
            "items": [self._model_to_entity(item) for item in items]
        }
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Récupère les statistiques d'un utilisateur"""
        # Total générations
        total = self.db.query(GenerationHistoryModel).filter(
            GenerationHistoryModel.user_id == user_id
        ).count()
        
        # Par type
        pdf_count = self.db.query(GenerationHistoryModel).filter(
            GenerationHistoryModel.user_id == user_id,
            GenerationHistoryModel.type == 'pdf'
        ).count()
        
        text_count = self.db.query(GenerationHistoryModel).filter(
            GenerationHistoryModel.user_id == user_id,
            GenerationHistoryModel.type == 'text'
        ).count()
        
        # Taux de succès
        success_count = self.db.query(GenerationHistoryModel).filter(
            GenerationHistoryModel.user_id == user_id,
            GenerationHistoryModel.status == 'success'
        ).count()
        
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        # Ce mois-ci
        first_day_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month = self.db.query(GenerationHistoryModel).filter(
            GenerationHistoryModel.user_id == user_id,
            GenerationHistoryModel.created_at >= first_day_month
        ).count()
        
        # Dernière génération
        last_gen = self.db.query(GenerationHistoryModel).filter(
            GenerationHistoryModel.user_id == user_id
        ).order_by(desc(GenerationHistoryModel.created_at)).first()
        
        # Nombre d'entreprises uniques
        companies = self.db.query(
            func.count(func.distinct(GenerationHistoryModel.company_name))
        ).filter(
            GenerationHistoryModel.user_id == user_id,
            GenerationHistoryModel.company_name.isnot(None)
        ).scalar() or 0
        
        return {
            "total": total,
            "pdf_count": pdf_count,
            "text_count": text_count,
            "success_rate": round(success_rate, 1),
            "this_month": this_month,
            "last_generation": last_gen.created_at if last_gen else None,
            "unique_companies": companies
        }
    
    def update(self, history: GenerationHistory) -> GenerationHistory:
        """Met à jour une entrée (pour régénération)"""
        model = self.db.query(GenerationHistoryModel).filter(
            GenerationHistoryModel.id == history.id
        ).first()
        
        if not model:
            raise ValueError(f"Historique {history.id} introuvable")
        
        # Mise à jour des champs modifiables
        if history.file_path:
            model.file_path = history.file_path
        if history.file_expires_at:
            model.file_expires_at = history.file_expires_at
        if history.text_content:
            model.text_content = history.text_content
        
        self.db.commit()
        self.db.refresh(model)
        
        logger.info(f"Historique mis à jour: {history.id}")
        return self._model_to_entity(model)
    
    def delete(self, history_id: str) -> None:
        """Supprime une entrée de l'historique"""
        model = self.db.query(GenerationHistoryModel).filter(
            GenerationHistoryModel.id == history_id
        ).first()
        
        if model:
            self.db.delete(model)
            self.db.commit()
            logger.info(f"Historique supprimé: {history_id}")
    
    def get_expired_files(self) -> List[GenerationHistory]:
        """Récupère les entrées avec fichiers expirés (pour cleanup)"""
        models = self.db.query(GenerationHistoryModel).filter(
            GenerationHistoryModel.file_expires_at < datetime.now(),
            GenerationHistoryModel.file_path.isnot(None)
        ).all()
        
        return [self._model_to_entity(model) for model in models]
    
    def get_all_with_pagination(
        self,
        page: int = 1,
        per_page: int = 50,
        user_filter: Optional[str] = None
    ) -> Dict:
        """Récupère tout l'historique (admin) avec pagination"""
        query = self.db.query(GenerationHistoryModel)
        
        if user_filter:
            query = query.filter(GenerationHistoryModel.user_id == user_filter)
        
        total = query.count()
        
        items = query.order_by(
            desc(GenerationHistoryModel.created_at)
        ).offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": math.ceil(total / per_page) if total > 0 else 0,
            "items": [self._model_to_entity(item) for item in items]
        }
    
    def _model_to_entity(self, model: GenerationHistoryModel) -> GenerationHistory:
        """Convertit un modèle SQLAlchemy en entité"""
        return GenerationHistory(
            id=model.id,
            user_id=model.user_id,
            type=model.type,
            job_title=model.job_title,
            company_name=model.company_name,
            job_url=model.job_url,
            cv_filename=model.cv_filename,
            cv_id=model.cv_id,
            file_path=model.file_path,
            text_content=model.text_content,
            status=model.status,
            error_message=model.error_message,
            created_at=model.created_at,
            file_expires_at=model.file_expires_at
        )
    
    def _entity_to_model(self, entity: GenerationHistory) -> GenerationHistoryModel:
        """Convertit une entité en modèle SQLAlchemy"""
        return GenerationHistoryModel(
            id=entity.id or str(uuid.uuid4()),
            user_id=entity.user_id,
            type=entity.type,
            job_title=entity.job_title,
            company_name=entity.company_name,
            job_url=entity.job_url,
            cv_filename=entity.cv_filename,
            cv_id=entity.cv_id,
            file_path=entity.file_path,
            text_content=entity.text_content,
            status=entity.status,
            error_message=entity.error_message,
            created_at=entity.created_at or datetime.now(),
            file_expires_at=entity.file_expires_at
        )
