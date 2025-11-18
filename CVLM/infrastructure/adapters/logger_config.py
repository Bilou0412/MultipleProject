"""
Configuration centralisée du logging pour l'application CVLM
"""
import logging
import sys
from typing import Optional

def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Configure et retourne un logger avec un format standardisé
    
    Args:
        name: Nom du logger (généralement __name__ du module)
        level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)
    
    # Éviter la duplication de handlers
    if logger.handlers:
        return logger
    
    # Niveau de log depuis env ou par défaut INFO
    import os
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Format avec timestamp, niveau, nom du module et message
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
