"""Initialize the database with sample content."""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any

from ..processing.rag_document import RAGDocument
from ..database.postgres_vector_db import PostgreSQLVectorDB

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_initial_content() -> List[Dict[str, Any]]:
    """Return list of initial documents to load."""
    return [
        {
            "text": "Piaget's theory of cognitive development suggests that children move through four different stages of mental development. His theory focuses on understanding how children acquire knowledge and on understanding the nature of intelligence. Piaget's stages are: 1) Sensorimotor stage (0-2 years), 2) Preoperational stage (2-7 years), 3) Concrete operational stage (7-11 years), and 4) Formal operational stage (11 years and older).",
            "metadata": {
                "title": "Theory of Cognitive Development",
                "author": "Jean Piaget",
                "source": "Piaget's Psychology of Intelligence",
                "year": "1947",
                "type": "book_excerpt",
                "category": "developmental_psychology"
            }
        },
        {
            "text": "The concept of schema is central to Piaget's theory. A schema is a cognitive framework or concept that helps organize and interpret information. Schemas can be modified through: 1) Assimilation - fitting new information into existing schemas, and 2) Accommodation - changing existing schemas to accommodate new information.",
            "metadata": {
                "title": "Schemas in Cognitive Development",
                "author": "Jean Piaget",
                "source": "Piaget's Psychology of Intelligence",
                "year": "1947",
                "type": "book_excerpt",
                "category": "developmental_psychology"
            }
        }
    ]

def init_database_content() -> None:
    """Initialize the database with content."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize database connection
        connection_string = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        vector_db = PostgreSQLVectorDB(connection_string=connection_string)
        
        # Get initial content
        content = load_initial_content()
        
        # Create RAG documents
        documents = []
        for item in content:
            doc = RAGDocument(text=item["text"], metadata=item["metadata"])
            documents.append(doc)
        
        # Add documents to database
        logger.info("Adding initial content to database...")
        doc_ids = vector_db.add_documents(documents)
        
        logger.info(f"Successfully added {len(doc_ids)} documents to database")
        
        # Verify content was added
        for doc_id in doc_ids:
            doc = vector_db.get_document(doc_id)
            if doc:
                logger.info(f"Verified document {doc_id}: {doc.metadata.get('title')}")
            else:
                logger.warning(f"Could not verify document {doc_id}")
                
    except Exception as e:
        logger.error(f"Error initializing database content: {str(e)}")
        raise

if __name__ == "__main__":
    init_database_content() 