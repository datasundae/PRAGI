#!/usr/bin/env python3
import os
from pathlib import Path
from src.database.postgres_vector_db import PostgreSQLVectorDB
from src.processing.ingest_documents import ingest_documents

def main():
    # Initialize the database
    db = PostgreSQLVectorDB()
    
    # Path to our specific PDF
    pdf_path = "/Volumes/NVME_Expansion/musartao/data/books/Processed/Peter Drucker - The Discipline of Innovation.pdf"
    
    # Define metadata
    metadata = {
        "title": "The Discipline of Innovation",
        "author": "Peter Drucker",
        "source": "Audio Transcription",
        "file_type": "pdf",
        "original_format": "m4b",
        "processed_date": "2024-04-05",
        "language": "en"
    }
    
    # Process the single PDF
    try:
        doc_ids = ingest_documents(pdf_path, db, metadata=metadata)
        print(f"Successfully processed document. Document ID: {doc_ids}")
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")

if __name__ == "__main__":
    main() 