from abc import ABC, abstractmethod


class JobOfferFetcher(ABC):
    @abstractmethod
    def fetch(self, url:str):
        pass
