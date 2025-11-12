import os
from dotenv import load_dotenv
from openai import OpenAI

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

class LlmOpenAI:
    def __init__(self):
        # Récupérer la clé API depuis les variables d'environnement
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("La clé 'OPENAI_API_KEY' est manquante dans le fichier .env.")
        
        # Initialiser le client une seule fois
        self.client = OpenAI(api_key=self.api_key)

    def send_to_llm(self, prompt: str, instructions: str = None) -> str:
        """Envoie un prompt au modèle GPT-4o et renvoie la réponse."""
        response = self.client.responses.create(
            model="gpt-4o",
            instructions=instructions or "Tu es un assistant utile et poli.",
            input=prompt,
        )

        return response.output_text
