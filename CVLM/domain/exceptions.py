"""
Exceptions métier custom pour CVLM
Séparer les erreurs métier des erreurs HTTP
"""


class CVLMBusinessError(Exception):
    """Exception de base pour toutes les erreurs métier CVLM"""
    pass


class InsufficientCreditsError(CVLMBusinessError):
    """L'utilisateur n'a plus de crédits disponibles"""
    def __init__(self, credit_type: str, message: str = None):
        self.credit_type = credit_type
        self.message = message or f"Crédits {credit_type} épuisés"
        super().__init__(self.message)


class ResourceNotFoundError(CVLMBusinessError):
    """Ressource introuvable"""
    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.message = f"{resource_type} avec ID {resource_id} introuvable"
        super().__init__(self.message)


class UnauthorizedAccessError(CVLMBusinessError):
    """Accès non autorisé à une ressource"""
    def __init__(self, resource_type: str, message: str = None):
        self.resource_type = resource_type
        self.message = message or f"Accès interdit à {resource_type}"
        super().__init__(self.message)


class FileValidationError(CVLMBusinessError):
    """Erreur de validation de fichier"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class PromoCodeError(CVLMBusinessError):
    """Erreur liée aux codes promo"""
    pass


class PromoCodeExpiredError(PromoCodeError):
    """Code promo expiré"""
    def __init__(self, code: str):
        self.code = code
        self.message = f"Le code promo '{code}' a expiré"
        super().__init__(self.message)


class PromoCodeInvalidError(PromoCodeError):
    """Code promo invalide"""
    def __init__(self, code: str):
        self.code = code
        self.message = f"Le code promo '{code}' est invalide ou n'existe pas"
        super().__init__(self.message)


class PromoCodeMaxUsesReachedError(PromoCodeError):
    """Code promo a atteint sa limite d'utilisation"""
    def __init__(self, code: str):
        self.code = code
        self.message = f"Le code promo '{code}' a atteint sa limite d'utilisation"
        super().__init__(self.message)


class GenerationError(CVLMBusinessError):
    """Erreur lors de la génération de contenu"""
    def __init__(self, generation_type: str, message: str):
        self.generation_type = generation_type
        self.message = f"Erreur génération {generation_type}: {message}"
        super().__init__(self.message)
