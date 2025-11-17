from dataclasses import dataclass


@dataclass
class JobOffer:
    """
    Représente une offre d'emploi avec son contenu textuel
    """
    raw_text: str = ""
