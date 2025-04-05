import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor, execute_values
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from .rag_document import RAGDocument
import logging
from sentence_transformers import SentenceTransformer
import urllib.parse

# Load environment variables
load_dotenv()

class PostgreSQLVectorDB:
    def __init__(self, connection_string: Optional[str] = None):
        """Initialize PostgreSQL Vector Database connection.
        
        Args:
            connection_string: Optional database connection string. If not provided,
                             will be constructed from environment variables.
        """
        if not connection_string:
            connection_string = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        
        try:
            self.conn = psycopg2.connect(connection_string)
            self.cur = self.conn.cursor()
            logging.info("Successfully connected to PostgreSQL database")
        except Exception as e:
            logging.error(f"Failed to connect to database: {str(e)}")
            raise
        
        self.logger = logging.getLogger(__name__)
        self.connection_string = connection_string
        if not self.connection_string:
            raise ValueError("Database connection string not provided")
            
        # Parse connection string into parameters
        parsed = urllib.parse.urlparse(self.connection_string)
        self.conn_params = {
            'dbname': parsed.path[1:],  # Remove leading slash
            'user': parsed.username,
            'password': urllib.parse.unquote(parsed.password),
            'host': parsed.hostname,
            'port': parsed.port or 5432
        }
            
        # Initialize sentence transformer model
        self.logger.info("Initializing sentence transformer model...")
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.logger.info("Sentence transformer model initialized successfully")
            
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        with self.conn:
            with self.cur:
                # Create extension for vector operations
                self.cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # Create documents table if it doesn't exist
                self.cur.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id SERIAL PRIMARY KEY,
                        content TEXT NOT NULL,
                        embedding vector(384),
                        metadata JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create index for similarity search
                self.cur.execute("""
                    CREATE INDEX IF NOT EXISTS documents_embedding_idx 
                    ON documents 
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                """)
                
                self.conn.commit()
    
    def add_document(self, document: RAGDocument, embedding: np.ndarray):
        """Add a document to the database.
        
        Args:
            document: RAGDocument object containing text and metadata
            embedding: Vector embedding of the document text
        """
        with self.conn:
            with self.cur:
                self.cur.execute("""
                    INSERT INTO documents (content, embedding, metadata)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                """, (document.text, embedding.tolist(), document.metadata))
                conn.commit()
                return self.cur.fetchone()[0]
    
    def search(
        self,
        query: str,
        k: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[RAGDocument, float]]:
        """Search for similar documents."""
        try:
            # Generate query embedding
            self.logger.info(f"Generating embedding for query: {query}")
            query_embedding = self.model.encode(query)
            self.logger.info(f"Generated embedding shape: {query_embedding.shape}")
            
            with self.conn:
                with self.cur:
                    # Construct SQL query
                    sql = """
                        SELECT id, content, encrypted_content, metadata, 
                               1 - (embedding <=> %s::vector) as similarity
                        FROM documents
                    """
                    params = [query_embedding.tolist()]
                    
                    # Add metadata filter if provided
                    if metadata_filter:
                        filter_sql, filter_params = self._format_metadata_filter(metadata_filter)
                        sql += " WHERE " + filter_sql
                        params.extend(filter_params)
                    
                    # Add similarity threshold and limit
                    sql += """
                        ORDER BY similarity DESC
                        LIMIT %s;
                    """
                    params.append(k)
                    
                    # Execute query
                    self.logger.info(f"Executing vector similarity search query")
                    self.logger.info(f"SQL: {sql}")
                    self.logger.info(f"Parameters: {params}")
                    
                    self.cur.execute(sql, params)
                    results = self.cur.fetchall()
                    
                    self.logger.info(f"Found {len(results)} results")
                    
                    # Format results
                    documents = []
                    for row in results:
                        doc_id, content, encrypted_content, metadata, similarity = row
                        self.logger.info(f"Document {doc_id} similarity: {similarity}")
                        self.logger.info(f"Document metadata: {metadata}")
                        
                        doc = RAGDocument(
                            text=content,
                            metadata=metadata
                        )
                        documents.append((doc, float(similarity)))
                    
                    return documents
                    
        except Exception as e:
            self.logger.error(f"Error in vector search: {str(e)}")
            self.logger.error(f"Error type: {type(e)}")
            self.logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")
            raise ValueError(f"Error searching documents: {str(e)}")
    
    def delete_document(self, document_id: int):
        """Delete a document from the database.
        
        Args:
            document_id: ID of the document to delete
        """
        with self.conn:
            with self.cur:
                self.cur.execute("DELETE FROM documents WHERE id = %s;", (document_id,))
                self.conn.commit()
    
    def get_document(self, document_id: int) -> Optional[RAGDocument]:
        """Retrieve a document by ID.
        
        Args:
            document_id: ID of the document to retrieve
            
        Returns:
            RAGDocument object if found, None otherwise
        """
        with self.conn:
            with self.cur(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT content, metadata
                    FROM documents
                    WHERE id = %s;
                """, (document_id,))
                
                row = cur.fetchone()
                if row:
                    return RAGDocument(
                        text=row['content'],
                        metadata=row['metadata']
                    )
                return None 