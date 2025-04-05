"""Initialize the database with sample content."""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any

from ..processing.rag_document import RAGDocument
from ..database.postgres_vector_db import PostgreSQLVectorDB
from ..database.ingestion_log import ingestion_log

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
                "category": "developmental_psychology",
                "filename": "piaget_cognitive_development.txt"
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
                "category": "developmental_psychology",
                "filename": "piaget_schemas.txt"
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
        
        # Create RAG documents and add to database
        for item in content:
            doc = RAGDocument(text=item["text"], metadata=item["metadata"])
            
            # Add to vector database
            doc_ids = vector_db.add_documents([doc])
            if not doc_ids:
                logger.error(f"Failed to add document: {item['metadata']['title']}")
                continue
                
            doc_id = doc_ids[0]
            
            # Create processed file path
            filename = item["metadata"]["filename"]
            processed_path = os.path.join("initial_content", filename)
            
            # Add to ingestion log
            ingestion_log.add_document(
                filename=filename,
                doc_id=doc_id,
                metadata=item["metadata"],
                processed_path=processed_path
            )
            
            logger.info(f"Added document: {item['metadata']['title']} (ID: {doc_id})")
        
        # Generate and save ingestion report
        ingestion_log.save_report()
        logger.info("Database initialization complete")
                
    except Exception as e:
        logger.error(f"Error initializing database content: {str(e)}")
        raise

if __name__ == "__main__":
    init_database_content() 