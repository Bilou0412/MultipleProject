"""
Implémentation PostgreSQL du UserRepository
"""
from typing import Optional, List
from sqlalchemy.orm import Session
import uuid

from domain.ports.user_repository import UserRepository
from domain.entities.user import User
from infrastructure.database.models import UserModel
from infrastructure.database.config import get_session_factory


class PostgresUserRepository(UserRepository):
    """
    Repository pour les utilisateurs utilisant PostgreSQL
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        Args:
            session: Session SQLAlchemy (si None, créée automatiquement)
        """
        self.session_factory = get_session_factory()
        self._external_session = session
    
    def _get_session(self) -> Session:
        """Récupère la session (externe ou nouvelle)"""
        if self._external_session:
            return self._external_session
        return self.session_factory()
    
    def _user_model_to_entity(self, model: UserModel) -> User:
        """Convertit un modèle SQLAlchemy en entité User"""
        return User(
            id=model.id,
            email=model.email,
            google_id=model.google_id,
            name=model.name,
            profile_picture_url=model.profile_picture_url,
            pdf_credits=model.pdf_credits,
            text_credits=model.text_credits,
            is_admin=model.is_admin,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _user_entity_to_model(self, user: User) -> UserModel:
        """Convertit une entité User en modèle SQLAlchemy"""
        return UserModel(
            id=user.id or str(uuid.uuid4()),
            email=user.email,
            google_id=user.google_id,
            name=user.name,
            profile_picture_url=user.profile_picture_url,
            pdf_credits=user.pdf_credits,
            text_credits=user.text_credits,
            is_admin=user.is_admin,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    def create(self, user: User) -> User:
        """Crée un nouvel utilisateur"""
        session = self._get_session()
        try:
            if not user.id:
                user.id = str(uuid.uuid4())
            
            model = self._user_entity_to_model(user)
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._user_model_to_entity(model)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if not self._external_session:
                session.close()
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Récupère un utilisateur par son ID"""
        session = self._get_session()
        try:
            model = session.query(UserModel).filter(UserModel.id == user_id).first()
            return self._user_model_to_entity(model) if model else None
        finally:
            if not self._external_session:
                session.close()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Récupère un utilisateur par son email"""
        session = self._get_session()
        try:
            model = session.query(UserModel).filter(UserModel.email == email).first()
            return self._user_model_to_entity(model) if model else None
        finally:
            if not self._external_session:
                session.close()
    
    def get_by_google_id(self, google_id: str) -> Optional[User]:
        """Récupère un utilisateur par son Google ID"""
        session = self._get_session()
        try:
            model = session.query(UserModel).filter(UserModel.google_id == google_id).first()
            return self._user_model_to_entity(model) if model else None
        finally:
            if not self._external_session:
                session.close()
    
    def update(self, user: User) -> User:
        """Met à jour un utilisateur"""
        session = self._get_session()
        try:
            model = session.query(UserModel).filter(UserModel.id == user.id).first()
            if not model:
                raise ValueError(f"User with id {user.id} not found")
            
            model.email = user.email
            model.google_id = user.google_id
            model.name = user.name
            model.profile_picture_url = user.profile_picture_url
            model.pdf_credits = user.pdf_credits
            model.text_credits = user.text_credits
            model.updated_at = user.updated_at
            
            session.commit()
            session.refresh(model)
            return self._user_model_to_entity(model)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if not self._external_session:
                session.close()
    
    def delete(self, user_id: str) -> bool:
        """Supprime un utilisateur"""
        session = self._get_session()
        try:
            model = session.query(UserModel).filter(UserModel.id == user_id).first()
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
    
    def list_all(self) -> List[User]:
        """Liste tous les utilisateurs"""
        session = self._get_session()
        try:
            models = session.query(UserModel).all()
            return [self._user_model_to_entity(model) for model in models]
        finally:
            if not self._external_session:
                session.close()
    
    def get_all(self) -> List[User]:
        """Récupère tous les utilisateurs (alias de list_all)"""
        return self.list_all()
