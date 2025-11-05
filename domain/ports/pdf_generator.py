from abc import ABC,abstractmethod

class PdfGenerator(ABC):

    @abstractmethod
    def create_pdf(self,text,output_path):
        pass
    
