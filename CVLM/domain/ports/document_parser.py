from abc import ABC,abstractmethod

class DocumentParser(ABC):
    
    @abstractmethod
    def parse_document(self,input_path:str):
        pass