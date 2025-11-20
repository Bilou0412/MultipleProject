"""
Implémentation PostgreSQL du MotivationalLetterRepository
"""
from typing import Optional, List
from sqlalchemy.orm import Session
import uuid

from domain.ports.motivational_letter_repository import MotivationalLetterRepository
from domain.entities.motivational_letter import MotivationalLetter
from infrastructure.database.models import MotivationalLetterModel
from infrastructure.database.config import get_session_factory


class PostgresMotivationalLetterRepository(MotivationalLetterRepository):
    """
    Repository pour les lettres de motivation utilisant PostgreSQL
    """
    
    def __init__(self, session: Optional[Session] = None):
        self.session_factory = get_session_factory()
        self._external_session = session
    
    def _get_session(self) -> Session:
        if self._external_session:
            return self._external_session
        return self.session_factory()
    
    def _letter_model_to_entity(self, model: MotivationalLetterModel) -> MotivationalLetter:
        """Convertit un modèle SQLAlchemy en entité MotivationalLetter"""
        letter = MotivationalLetter(raw_text=model.raw_text or "")
        letter.id = model.id
        letter.user_id = model.user_id
        letter.cv_id = model.cv_id
        letter.job_offer_url = model.job_offer_url
        letter.filename = model.filename
        letter.file_path = model.file_path
        letter.file_size = model.file_size
        letter.llm_provider = model.llm_provider
        letter.created_at = model.created_at
        letter.updated_at = model.updated_at
        return letter
    
    def _letter_entity_to_model(self, letter: MotivationalLetter) -> MotivationalLetterModel:
        """Convertit une entité MotivationalLetter en modèle SQLAlchemy"""
        return MotivationalLetterModel(
            id=letter.id or str(uuid.uuid4()),
            user_id=letter.user_id,
            cv_id=letter.cv_id,
            job_offer_url=letter.job_offer_url,
            filename=letter.filename,
            file_path=letter.file_path,
            file_size=letter.file_size,
            raw_text=letter.raw_text,
            llm_provider=letter.llm_provider,
            created_at=letter.created_at,
            updated_at=letter.updated_at
        )
    
    def create(self, letter: MotivationalLetter) -> MotivationalLetter:
        session = self._get_session()
        try:
            if not letter.id:
                letter.id = str(uuid.uuid4())
            
            model = self._letter_entity_to_model(letter)
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._letter_model_to_entity(model)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if not self._external_session:
                session.close()
    
    def get_by_id(self, letter_id: str) -> Optional[MotivationalLetter]:
        session = self._get_session()
        try:
            model = session.query(MotivationalLetterModel).filter(
                MotivationalLetterModel.id == letter_id
            ).first()
            return self._letter_model_to_entity(model) if model else None
        finally:
            if not self._external_session:
                session.close()
    
    def get_by_user_id(self, user_id: str) -> List[MotivationalLetter]:
        session = self._get_session()
        try:
            models = session.query(MotivationalLetterModel).filter(
                MotivationalLetterModel.user_id == user_id
            ).all()
            return [self._letter_model_to_entity(model) for model in models]
        finally:
            if not self._external_session:
                session.close()
    
    def get_by_cv_id(self, cv_id: str) -> List[MotivationalLetter]:
        session = self._get_session()
        try:
            models = session.query(MotivationalLetterModel).filter(
                MotivationalLetterModel.cv_id == cv_id
            ).all()
            return [self._letter_model_to_entity(model) for model in models]
        finally:
            if not self._external_session:
                session.close()
    
    def update(self, letter: MotivationalLetter) -> MotivationalLetter:
        session = self._get_session()
        try:
            model = session.query(MotivationalLetterModel).filter(
                MotivationalLetterModel.id == letter.id
            ).first()
            if not model:
                raise ValueError(f"Letter with id {letter.id} not found")
            
            model.user_id = letter.user_id
            model.cv_id = letter.cv_id
            model.job_offer_url = letter.job_offer_url
            model.filename = letter.filename
            model.file_path = letter.file_path
            model.file_size = letter.file_size
            model.raw_text = letter.raw_text
            model.llm_provider = letter.llm_provider
            model.updated_at = letter.updated_at
            
            session.commit()
            session.refresh(model)
            return self._letter_model_to_entity(model)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if not self._external_session:
                session.close()
    
    def delete(self, letter_id: str) -> bool:
        session = self._get_session()
        try:
            model = session.query(MotivationalLetterModel).filter(
                MotivationalLetterModel.id == letter_id
            ).first()
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
    
    def list_all(self) -> List[MotivationalLetter]:
        session = self._get_session()
        try:
            models = session.query(MotivationalLetterModel).all()
            return [self._letter_model_to_entity(model) for model in models]
        finally:
            if not self._external_session:
                session.close()
