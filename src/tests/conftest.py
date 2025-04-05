"""Pytest configuration and shared fixtures."""
import os
import sys
from pathlib import Path
import pytest
from dotenv import load_dotenv

# Add the src directory to the Python path
src_dir = str(Path(__file__).resolve().parent.parent.parent)
sys.path.append(src_dir)

# Load environment variables
load_dotenv(os.path.join(src_dir, '.env'))

from src.database.postgres_vector_db import PostgreSQLVectorDB
from src.processing.rag_document import RAGDocument

@pytest.fixture(scope="session")
def vector_db():
    """Create a shared vector database connection for tests."""
    db = PostgreSQLVectorDB()
    return db

@pytest.fixture
def sample_document():
    """Create a sample RAG document for testing."""
    return RAGDocument(
        text="This is a sample document for testing.",
        metadata={
            "title": "Test Document",
            "author": "Test Author",
            "source": "Unit Test"
        }
    )

@pytest.fixture
def sample_documents():
    """Create a list of sample RAG documents for testing."""
    return [
        RAGDocument(
            text="First test document about artificial intelligence.",
            metadata={
                "title": "AI Basics",
                "author": "Test Author 1",
                "source": "Unit Test"
            }
        ),
        RAGDocument(
            text="Second test document about machine learning.",
            metadata={
                "title": "ML Fundamentals",
                "author": "Test Author 2",
                "source": "Unit Test"
            }
        ),
        RAGDocument(
            text="Third test document about neural networks.",
            metadata={
                "title": "Neural Networks",
                "author": "Test Author 3",
                "source": "Unit Test"
            }
        )
    ] 