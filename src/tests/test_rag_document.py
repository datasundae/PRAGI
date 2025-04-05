"""Test suite for RAG document functionality."""
import pytest
from src.processing.rag_document import RAGDocument

def test_rag_document_creation():
    """Test basic RAG document creation."""
    doc = RAGDocument(
        text="Test content",
        metadata={"title": "Test"}
    )
    assert doc.text == "Test content"
    assert doc.metadata["title"] == "Test"

def test_rag_document_metadata_types():
    """Test that metadata handles different types correctly."""
    metadata = {
        "string": "test",
        "integer": 42,
        "float": 3.14,
        "list": ["a", "b", "c"],
        "nested": {"key": "value"}
    }
    doc = RAGDocument(text="Test", metadata=metadata)
    assert doc.metadata == metadata

def test_rag_document_empty_metadata():
    """Test RAG document creation with empty metadata."""
    doc = RAGDocument(text="Test")
    assert isinstance(doc.metadata, dict)
    assert len(doc.metadata) == 0

def test_rag_document_invalid_text():
    """Test RAG document creation with invalid text."""
    with pytest.raises(ValueError):
        RAGDocument(text=None)
    
    with pytest.raises(ValueError):
        RAGDocument(text="")
    
    with pytest.raises(ValueError):
        RAGDocument(text=" ")

def test_rag_document_invalid_metadata():
    """Test RAG document creation with invalid metadata."""
    with pytest.raises(ValueError):
        RAGDocument(text="Test", metadata="not a dict")
    
    with pytest.raises(ValueError):
        RAGDocument(text="Test", metadata=[1, 2, 3])

def test_rag_document_metadata_immutability():
    """Test that metadata cannot be modified after creation."""
    metadata = {"key": "value"}
    doc = RAGDocument(text="Test", metadata=metadata)
    
    # Original metadata should be a copy
    metadata["key"] = "new value"
    assert doc.metadata["key"] == "value"
    
    # Metadata should be read-only
    with pytest.raises(AttributeError):
        doc.metadata = {"new": "metadata"}

def test_rag_document_text_immutability():
    """Test that text cannot be modified after creation."""
    doc = RAGDocument(text="Test")
    with pytest.raises(AttributeError):
        doc.text = "New text"

def test_rag_document_str_representation():
    """Test string representation of RAG document."""
    doc = RAGDocument(
        text="Test content",
        metadata={"title": "Test"}
    )
    str_rep = str(doc)
    assert "Test content" in str_rep
    assert "title" in str_rep
    assert "Test" in str_rep

def test_rag_document_equality():
    """Test RAG document equality comparison."""
    doc1 = RAGDocument(
        text="Test content",
        metadata={"title": "Test"}
    )
    doc2 = RAGDocument(
        text="Test content",
        metadata={"title": "Test"}
    )
    doc3 = RAGDocument(
        text="Different content",
        metadata={"title": "Test"}
    )
    
    assert doc1 == doc2
    assert doc1 != doc3
    assert doc1 != "not a document"

def test_rag_document_hash():
    """Test RAG document can be used in sets and as dict keys."""
    doc1 = RAGDocument(
        text="Test content",
        metadata={"title": "Test"}
    )
    doc2 = RAGDocument(
        text="Test content",
        metadata={"title": "Test"}
    )
    
    # Same documents should have same hash
    assert hash(doc1) == hash(doc2)
    
    # Can be used in sets
    doc_set = {doc1, doc2}
    assert len(doc_set) == 1  # Only one unique document 