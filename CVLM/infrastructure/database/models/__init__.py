"""
Modèles SQLAlchemy pour la base de données
"""
from .user_model import UserModel
from .cv_model import CvModel
from .letter_model import MotivationalLetterModel
from .promo_code_model import PromoCodeModel
from .generation_history_model import GenerationHistoryModel

__all__ = [
    'UserModel',
    'CvModel',
    'MotivationalLetterModel',
    'PromoCodeModel',
    'GenerationHistoryModel'
]
