from domain.ports.job_offer_fetcher import JobOfferFetcher
import requests
from bs4 import BeautifulSoup

class WelcomeToTheJungleFetcher(JobOfferFetcher):
    def fetch(self, url: str) -> str:  # ← Changé de fetch_job_offer à fetch
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Ajouter des puces avant chaque <li>
        for li in soup.find_all('li'):
            li.insert_before('\n• ')
        
        # Récupérer UNIQUEMENT les sections job-section-description et job-section-experience
        sections = soup.find_all('div', {'data-testid': ['job-section-description', 'job-section-experience']})
        
        return '\n\n'.join(s.get_text(separator='\n', strip=True) for s in sections)