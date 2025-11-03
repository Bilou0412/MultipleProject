from abc import ABC, abstractmethod


class UserEntries(ABC):
    def __init__(self, path):
        self.path = path
        self.row_data = None

    @abstractmethod
    def get_row_data(self):
        pass


class JobOpening(UserEntries):
    def __init__(self, path):
        super().__init__(path)

    def get_row_data(self):
        try:
            with open(self.path, "r") as f:
                self.row_data = f.read()
        except Exception as e:
            print(f"ERROR : {e}")


class Cv(UserEntries):
    def __init__(self, path):
        super().__init__(path)

    def get_row_data(self):
        try:
            with open(self.path, "r") as f:
                self.row_data = f.read()
        except Exception as e:
            print(f"ERROR : {e}")


class Lm(UserEntries):
    def __init__(self):
        print()
