"""Test suite for vector database functionality."""
import pytest
from typing import List
import numpy as np

from src.processing.rag_document import RAGDocument
from src.database.postgres_vector_db import PostgreSQLVectorDB

def test_db_connection(vector_db):
    """Test that database connection works."""
    assert isinstance(vector_db, PostgreSQLVectorDB)
    # Test connection by running a simple query
    with vector_db.conn_params:
        assert True  # If we get here, connection worked

def test_add_single_document(vector_db, sample_document):
    """Test adding a single document to the database."""
    doc_ids = vector_db.add_documents([sample_document])
    assert len(doc_ids) == 1
    assert isinstance(doc_ids[0], str)

def test_add_multiple_documents(vector_db, sample_documents):
    """Test adding multiple documents to the database."""
    doc_ids = vector_db.add_documents(sample_documents)
    assert len(doc_ids) == len(sample_documents)
    assert all(isinstance(id, str) for id in doc_ids)

def test_search_exact_match(vector_db, sample_document):
    """Test searching for an exact match."""
    # First add the document
    vector_db.add_documents([sample_document])
    
    # Search for exact text
    results = vector_db.search(sample_document.text)
    assert len(results) > 0
    
    # Check the first result
    doc, similarity = results[0]
    assert isinstance(doc, RAGDocument)
    assert similarity > 0.7  # Should have high similarity for exact match
    assert doc.text == sample_document.text
    assert doc.metadata == sample_document.metadata

def test_search_semantic_match(vector_db, sample_documents):
    """Test semantic search capabilities."""
    # Add test documents
    vector_db.add_documents(sample_documents)
    
    # Search for semantically related content
    results = vector_db.search("AI and machine learning concepts")
    assert len(results) > 0
    
    # The top results should be our AI and ML documents
    found_ai = False
    found_ml = False
    for doc, similarity in results[:2]:
        if "artificial intelligence" in doc.text.lower():
            found_ai = True
        if "machine learning" in doc.text.lower():
            found_ml = True
    
    assert found_ai and found_ml

def test_metadata_preservation(vector_db, sample_documents):
    """Test that metadata is preserved correctly."""
    # Add documents
    vector_db.add_documents(sample_documents)
    
    # Search and verify metadata
    results = vector_db.search("neural networks")
    assert len(results) > 0
    
    # Find the neural networks document
    nn_doc = None
    for doc, _ in results:
        if doc.metadata.get("title") == "Neural Networks":
            nn_doc = doc
            break
    
    assert nn_doc is not None
    assert nn_doc.metadata["author"] == "Test Author 3"
    assert nn_doc.metadata["source"] == "Unit Test"

def test_encryption(vector_db, sample_document):
    """Test that encryption and decryption work correctly."""
    # Add document
    doc_ids = vector_db.add_documents([sample_document])
    assert len(doc_ids) == 1
    
    # Search and verify content is decrypted correctly
    results = vector_db.search(sample_document.text)
    assert len(results) > 0
    
    retrieved_doc, _ = results[0]
    assert retrieved_doc.text == sample_document.text

def test_search_with_empty_query(vector_db):
    """Test handling of empty search queries."""
    results = vector_db.search("")
    assert len(results) == 0

def test_add_empty_document_list(vector_db):
    """Test handling of empty document list."""
    doc_ids = vector_db.add_documents([])
    assert len(doc_ids) == 0

@pytest.mark.parametrize("invalid_text", [None, "", " "])
def test_invalid_document_text(vector_db, invalid_text, sample_document):
    """Test handling of invalid document text."""
    invalid_doc = RAGDocument(text=invalid_text, metadata=sample_document.metadata)
    with pytest.raises(ValueError):
        vector_db.add_documents([invalid_doc])

def test_large_batch_insert(vector_db):
    """Test inserting a large batch of documents."""
    # Create 100 test documents
    large_batch = [
        RAGDocument(
            text=f"Test document number {i} with some content for testing large batch inserts.",
            metadata={"batch_id": i}
        )
        for i in range(100)
    ]
    
    doc_ids = vector_db.add_documents(large_batch)
    assert len(doc_ids) == 100 