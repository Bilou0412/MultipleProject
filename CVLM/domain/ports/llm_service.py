from abc import ABC, abstractmethod


class LlmService(ABC):
    @abstractmethod
    def send_to_llm(self, prompt):
        pass
