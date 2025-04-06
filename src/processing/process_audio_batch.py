#!/usr/bin/env python3
import os
from pathlib import Path
from transcribe_to_pdf import transcribe_audio, create_pdf
import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np
from tqdm import tqdm
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SimpleVectorDB:
    def __init__(self):
        """Initialize database connection."""
        self.conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    def add_document(self, text, metadata=None):
        """Add a document to the vector database."""
        # Create embedding
        embedding = self.model.encode(text)
        
        # Convert metadata to JSON if provided
        metadata_json = json.dumps(metadata) if metadata else None
        
        # Insert into database
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (content, embedding, metadata)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (text, embedding.tolist(), metadata_json)
            )
            doc_id = cur.fetchone()[0]
            self.conn.commit()
            return doc_id

def process_audio_book(audio_file_path, db):
    """Process a single audio book file and ingest it into the vector database."""
    print(f"\nProcessing: {os.path.basename(audio_file_path)}")
    
    # Get the base name without extension
    base_name = os.path.splitext(os.path.basename(audio_file_path))[0]
    
    # Define output paths
    output_dir = "/Volumes/NVME_Expansion/musartao/data/books/Processed"
    os.makedirs(output_dir, exist_ok=True)
    
    pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
    
    # Transcribe audio to text
    print("Transcribing audio...")
    transcription = transcribe_audio(audio_file_path)
    
    # Create PDF from transcription
    print("Creating PDF...")
    create_pdf(transcription, pdf_path)
    
    print(f"PDF saved to: {pdf_path}")
    
    # Extract metadata from filename
    parts = base_name.split('_')[0]  # Remove _ep6 suffix
    title_parts = []
    current_word = []
    
    for char in parts:
        if char.isupper() and current_word:
            title_parts.append(''.join(current_word))
            current_word = [char]
        else:
            current_word.append(char)
    if current_word:
        title_parts.append(''.join(current_word))
    
    title = ' '.join(title_parts)
    
    # Prepare metadata for vector database
    metadata = {
        "title": title,
        "source": "Audio Transcription",
        "file_type": "pdf",
        "original_format": "m4b",
        "processed_date": "2024-04-05",
        "language": "en"
    }
    
    # Ingest into vector database
    print("Ingesting into vector database...")
    try:
        doc_id = db.add_document(transcription, metadata=metadata)
        print(f"Successfully ingested document. Document ID: {doc_id}")
    except Exception as e:
        print(f"Error ingesting document: {str(e)}")
        return None
    
    print(f"Completed processing: {base_name}")
    return pdf_path, doc_id

def main():
    # Initialize the database
    db = SimpleVectorDB()
    
    # Get list of unprocessed files
    with open("unprocessed_m4b_files.txt", "r") as f:
        unprocessed_files = [line.strip() for line in f]
    
    print(f"Found {len(unprocessed_files)} files to process")
    
    # Process each file
    for audio_file in unprocessed_files:
        if os.path.exists(audio_file):
            result = process_audio_book(audio_file, db)
            if result:
                pdf_path, doc_id = result
                print(f"Successfully processed {os.path.basename(audio_file)}")
                print(f"PDF saved at: {pdf_path}")
                print(f"Document ID in vector DB: {doc_id}")
            else:
                print(f"Failed to process {os.path.basename(audio_file)}")
        else:
            print(f"File not found: {audio_file}")

if __name__ == "__main__":
    main() 