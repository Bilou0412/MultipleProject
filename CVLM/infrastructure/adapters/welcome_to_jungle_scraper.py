from domain.ports.job_offer_fetcher import JobOfferFetcher
import requests


class WelcomeToJungleScraper(JobOfferFetcher):
    def fetch(self, url):
        return ("dev de vinci")
