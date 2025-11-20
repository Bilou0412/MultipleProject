"""
Implémentation PostgreSQL du CvRepository
"""
from typing import Optional, List
from sqlalchemy.orm import Session
import uuid

from domain.ports.cv_repository import CvRepository
from domain.entities.cv import Cv
from infrastructure.database.models import CvModel
from infrastructure.database.config import get_session_factory


class PostgresCvRepository(CvRepository):
    """
    Repository pour les CVs utilisant PostgreSQL
    """
    
    def __init__(self, session: Optional[Session] = None):
        self.session_factory = get_session_factory()
        self._external_session = session
    
    def _get_session(self) -> Session:
        if self._external_session:
            return self._external_session
        return self.session_factory()
    
    def _cv_model_to_entity(self, model: CvModel) -> Cv:
        """Convertit un modèle SQLAlchemy en entité Cv"""
        cv = Cv(raw_text=model.raw_text or "")
        cv.id = model.id
        cv.user_id = model.user_id
        cv.filename = model.filename
        cv.file_path = model.file_path
        cv.file_size = model.file_size
        cv.created_at = model.created_at
        cv.updated_at = model.updated_at
        return cv
    
    def _cv_entity_to_model(self, cv: Cv) -> CvModel:
        """Convertit une entité Cv en modèle SQLAlchemy"""
        return CvModel(
            id=cv.id or str(uuid.uuid4()),
            user_id=cv.user_id,
            filename=cv.filename,
            file_path=cv.file_path,
            file_size=cv.file_size,
            raw_text=cv.raw_text,
            created_at=cv.created_at,
            updated_at=cv.updated_at
        )
    
    def create(self, cv: Cv) -> Cv:
        session = self._get_session()
        try:
            if not cv.id:
                cv.id = str(uuid.uuid4())
            
            model = self._cv_entity_to_model(cv)
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._cv_model_to_entity(model)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if not self._external_session:
                session.close()
    
    def get_by_id(self, cv_id: str) -> Optional[Cv]:
        session = self._get_session()
        try:
            model = session.query(CvModel).filter(CvModel.id == cv_id).first()
            return self._cv_model_to_entity(model) if model else None
        finally:
            if not self._external_session:
                session.close()
    
    def get_by_user_id(self, user_id: str) -> List[Cv]:
        session = self._get_session()
        try:
            models = session.query(CvModel).filter(CvModel.user_id == user_id).all()
            return [self._cv_model_to_entity(model) for model in models]
        finally:
            if not self._external_session:
                session.close()
    
    def update(self, cv: Cv) -> Cv:
        session = self._get_session()
        try:
            model = session.query(CvModel).filter(CvModel.id == cv.id).first()
            if not model:
                raise ValueError(f"CV with id {cv.id} not found")
            
            model.user_id = cv.user_id
            model.filename = cv.filename
            model.file_path = cv.file_path
            model.file_size = cv.file_size
            model.raw_text = cv.raw_text
            model.updated_at = cv.updated_at
            
            session.commit()
            session.refresh(model)
            return self._cv_model_to_entity(model)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if not self._external_session:
                session.close()
    
    def delete(self, cv_id: str) -> bool:
        session = self._get_session()
        try:
            model = session.query(CvModel).filter(CvModel.id == cv_id).first()
            if not model:
                return False
            
            session.delete(model)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if not self._external_session:
                session.close()
    
    def list_all(self) -> List[Cv]:
        session = self._get_session()
        try:
            models = session.query(CvModel).all()
            return [self._cv_model_to_entity(model) for model in models]
        finally:
            if not self._external_session:
                session.close()
