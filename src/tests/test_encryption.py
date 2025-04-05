"""Test the database encryption functionality."""
import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv

# Add the src directory to the Python path
src_dir = str(Path(__file__).resolve().parent.parent.parent)
sys.path.append(src_dir)

# Load environment variables before importing database modules
load_dotenv(os.path.join(src_dir, '.env'))

from src.database.postgres_vector_db import PostgreSQLVectorDB
from src.processing.rag_document import RAGDocument

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_encryption():
    """Test that encryption and decryption work correctly with the new key."""
    try:
        # Initialize the database connection
        db = PostgreSQLVectorDB()
        
        # Test data
        test_text = "This is a test document for encryption verification."
        test_metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "source": "Encryption Test"
        }
        test_doc = RAGDocument(text=test_text, metadata=test_metadata)
        
        # Try to add the document (this will encrypt it)
        logger.info("Adding test document to database...")
        doc_ids = db.add_documents([test_doc])
        
        if not doc_ids:
            logger.error("Failed to add test document")
            return False
            
        doc_id = doc_ids[0]
        logger.info(f"Test document added with ID: {doc_id}")
        
        # Try to retrieve and verify the document
        logger.info("Searching for the test document...")
        results = db.search("test document encryption verification")
        
        if not results:
            logger.error("Failed to retrieve test document")
            return False
            
        # Check the first result
        retrieved_doc, similarity = results[0]
        logger.info(f"Retrieved document with similarity score: {similarity}")
        logger.info(f"Retrieved text: {retrieved_doc.text}")
        logger.info(f"Retrieved metadata: {retrieved_doc.metadata}")
        
        # Verify the content matches
        if test_text not in retrieved_doc.text:
            logger.error("Retrieved text doesn't match original text")
            return False
            
        if test_metadata["title"] != retrieved_doc.metadata.get("title"):
            logger.error("Retrieved metadata doesn't match original metadata")
            return False
            
        logger.info("Encryption test passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error during encryption test: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_encryption()
    if not success:
        logger.error("Encryption test failed!")
        sys.exit(1)
    logger.info("All tests passed!") 