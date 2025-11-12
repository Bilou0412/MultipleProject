# infrastructure/adapters/open_ai.py
import os
from dotenv import load_dotenv
from google import genai

# Charger les variables d'environnement
load_dotenv()

class LlmGemini:
    def __init__(self):
        # Récupérer la clé API depuis les variables d'environnement
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY non trouvée dans le fichier .env")
    
    def send_to_llm(self, prompt: str) -> str:
        # Initialiser le client avec la clé API
        client = genai.Client(api_key=self.api_key)
        
        # Envoyer le prompt au modèle
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',  # ou le modèle que tu veux utiliser
            contents=prompt
        )
        
        return response.text