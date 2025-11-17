"""
Exemples de tests pour la nouvelle architecture
Ces tests montrent comment l'architecture Clean facilite les tests
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from domain.entities.user import User
from domain.entities.cv import Cv
from domain.entities.motivational_letter import MotivationalLetter
from domain.use_cases.analyze_cv_and_offer import AnalyseCvOffer


class TestUserEntity:
    """Tests de l'entité User"""
    
    def test_user_creation(self):
        """Test création d'un utilisateur"""
        user = User(
            id="user-123",
            email="test@example.com",
            google_id="google-456",
            name="Test User"
        )
        
        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert user.google_id == "google-456"
        assert user.name == "Test User"
        assert isinstance(user.created_at, datetime)
    
    def test_user_timestamps_auto_generated(self):
        """Test que les timestamps sont générés automatiquement"""
        user = User(
            id=None,
            email="test@example.com",
            google_id="google-456",
            name="Test User"
        )
        
        assert user.created_at is not None
        assert user.updated_at is not None


class TestCvEntity:
    """Tests de l'entité CV"""
    
    def test_cv_creation_with_metadata(self):
        """Test création CV avec métadonnées"""
        cv = Cv(raw_text="CV content here")
        cv.id = "cv-123"
        cv.user_id = "user-456"
        cv.filename = "my_cv.pdf"
        cv.file_path = "cvs/cv-123.pdf"
        cv.file_size = 1024
        
        assert cv.raw_text == "CV content here"
        assert cv.id == "cv-123"
        assert cv.user_id == "user-456"
        assert cv.file_size == 1024


class TestAnalyseCvOfferUseCase:
    """Tests du use case AnalyseCvOffer avec mocks"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Crée des mocks pour toutes les dépendances"""
        return {
            'job_offer_fetcher': Mock(),
            'document_parser': Mock(),
            'llm': Mock(),
            'pdf_generator': Mock(),
            'cv_repository': Mock(),
            'letter_repository': Mock(),
            'file_storage': Mock()
        }
    
    def test_execute_without_persistence(self, mock_dependencies):
        """Test génération sans persistance (comportement original)"""
        # Arrange
        mock_dependencies['document_parser'].parse_document.return_value = "CV text"
        mock_dependencies['job_offer_fetcher'].fetch.return_value = "Job offer text"
        mock_dependencies['llm'].send_to_llm.return_value = "Generated letter"
        mock_dependencies['pdf_generator'].create_pdf.return_value = "/path/to/letter.pdf"
        
        use_case = AnalyseCvOffer(**mock_dependencies)
        
        # Act
        result = use_case.execute(
            cv_path="cv.pdf",
            jo_path="https://job-url.com",
            use_scraper=True,
            persist=False
        )
        
        # Assert
        assert result == "/path/to/letter.pdf"
        mock_dependencies['document_parser'].parse_document.assert_called_once_with(input_path="cv.pdf")
        mock_dependencies['job_offer_fetcher'].fetch.assert_called_once_with(url="https://job-url.com")
        mock_dependencies['llm'].send_to_llm.assert_called_once()
        mock_dependencies['pdf_generator'].create_pdf.assert_called_once()
        
        # Vérifier que les repositories ne sont PAS appelés
        mock_dependencies['cv_repository'].create.assert_not_called()
        mock_dependencies['letter_repository'].create.assert_not_called()
    
    def test_execute_with_persistence(self, mock_dependencies):
        """Test génération avec persistance en DB"""
        # Arrange
        mock_dependencies['document_parser'].parse_document.return_value = "CV text"
        mock_dependencies['job_offer_fetcher'].fetch.return_value = "Job offer text"
        mock_dependencies['llm'].send_to_llm.return_value = "Generated letter"
        mock_dependencies['pdf_generator'].create_pdf.return_value = "/tmp/letter.pdf"
        mock_dependencies['file_storage'].save_file.return_value = "letters/letter-123.pdf"
        
        # Mock du repository qui retourne une lettre avec ID
        saved_letter = MotivationalLetter("Generated letter")
        saved_letter.id = "letter-123"
        mock_dependencies['letter_repository'].create.return_value = saved_letter
        
        use_case = AnalyseCvOffer(**mock_dependencies)
        
        # Act
        pdf_path, letter_id = use_case.execute(
            cv_path="cv.pdf",
            jo_path="https://job-url.com",
            use_scraper=True,
            user_id="user-789",
            cv_id="cv-456",
            persist=True
        )
        
        # Assert
        assert pdf_path == "/tmp/letter.pdf"
        assert letter_id == "letter-123"
        
        # Vérifier que le repository est appelé
        mock_dependencies['letter_repository'].create.assert_called_once()
        mock_dependencies['file_storage'].save_file.assert_called_once()
    
    def test_execute_with_existing_cv_id(self, mock_dependencies):
        """Test utilisation d'un CV existant en DB (évite re-parsing)"""
        # Arrange
        existing_cv = Cv(raw_text="Cached CV text")
        existing_cv.id = "cv-123"
        mock_dependencies['cv_repository'].get_by_id.return_value = existing_cv
        
        mock_dependencies['job_offer_fetcher'].fetch.return_value = "Job offer text"
        mock_dependencies['llm'].send_to_llm.return_value = "Generated letter"
        mock_dependencies['pdf_generator'].create_pdf.return_value = "/path/to/letter.pdf"
        
        use_case = AnalyseCvOffer(**mock_dependencies)
        
        # Act
        result = use_case.execute(
            cv_id="cv-123",  # Utilise un CV existant
            jo_path="https://job-url.com",
            use_scraper=True,
            persist=False
        )
        
        # Assert
        mock_dependencies['cv_repository'].get_by_id.assert_called_once_with("cv-123")
        
        # Le parser ne doit PAS être appelé (CV déjà en DB)
        mock_dependencies['document_parser'].parse_document.assert_not_called()
        
        assert result == "/path/to/letter.pdf"


class TestUserRepository:
    """Tests du repository User (avec vraie DB ou mock)"""
    
    @pytest.fixture
    def user_repository(self):
        """
        Dans un vrai test, on utiliserait soit :
        1. Une DB de test (PostgreSQL test)
        2. Un mock complet
        """
        from domain.ports.user_repository import UserRepository
        
        # Mock repository pour l'exemple
        mock_repo = Mock(spec=UserRepository)
        return mock_repo
    
    def test_create_user(self, user_repository):
        """Test création d'un utilisateur"""
        # Arrange
        new_user = User(
            id=None,
            email="new@example.com",
            google_id="google-789",
            name="New User"
        )
        
        created_user = User(
            id="user-123",
            email="new@example.com",
            google_id="google-789",
            name="New User"
        )
        user_repository.create.return_value = created_user
        
        # Act
        result = user_repository.create(new_user)
        
        # Assert
        assert result.id == "user-123"
        assert result.email == "new@example.com"
    
    def test_get_by_email(self, user_repository):
        """Test récupération par email"""
        # Arrange
        expected_user = User(
            id="user-456",
            email="test@example.com",
            google_id="google-123",
            name="Test User"
        )
        user_repository.get_by_email.return_value = expected_user
        
        # Act
        result = user_repository.get_by_email("test@example.com")
        
        # Assert
        assert result.id == "user-456"
        assert result.email == "test@example.com"


class TestFileStorage:
    """Tests du FileStorage"""
    
    @pytest.fixture
    def file_storage(self):
        """Mock du file storage"""
        from domain.ports.file_storage import FileStorage
        return Mock(spec=FileStorage)
    
    def test_save_file(self, file_storage):
        """Test sauvegarde d'un fichier"""
        # Arrange
        file_content = b"PDF content here"
        filename = "test.pdf"
        file_storage.save_file.return_value = "cvs/test.pdf"
        
        # Act
        path = file_storage.save_file(file_content, filename, "cvs")
        
        # Assert
        assert path == "cvs/test.pdf"
        file_storage.save_file.assert_called_once_with(file_content, filename, "cvs")
    
    def test_file_exists(self, file_storage):
        """Test vérification existence fichier"""
        # Arrange
        file_storage.file_exists.return_value = True
        
        # Act
        exists = file_storage.file_exists("cvs/test.pdf")
        
        # Assert
        assert exists is True
        file_storage.file_exists.assert_called_once_with("cvs/test.pdf")


# Pour lancer les tests:
# pytest tests/test_examples.py -v
# pytest tests/test_examples.py::TestAnalyseCvOfferUseCase::test_execute_without_persistence -v
