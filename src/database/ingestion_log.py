"""Track and manage ingested documents."""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the processed directory path
PROCESSED_DIR = Path("/Volumes/NVME_Expansion/musartao/data/books/Processed")

class IngestionLog:
    """Manage the log of ingested documents."""
    
    def __init__(self):
        """Initialize the ingestion log."""
        if not PROCESSED_DIR.exists():
            raise FileNotFoundError(f"Processed directory not found: {PROCESSED_DIR}")
            
        self.log_file = PROCESSED_DIR / "ingested_documents.json"
        self.report_file = PROCESSED_DIR / "ingestion_report.md"
        self._ensure_log_file()
    
    def _ensure_log_file(self) -> None:
        """Create log file if it doesn't exist."""
        if not self.log_file.exists():
            self._save_log({
                "last_updated": datetime.now().isoformat(),
                "documents": []
            })
    
    def _load_log(self) -> Dict:
        """Load the current log file."""
        try:
            with open(self.log_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error reading {self.log_file}. Creating new log.")
            return {
                "last_updated": datetime.now().isoformat(),
                "documents": []
            }
    
    def _save_log(self, log_data: Dict) -> None:
        """Save the log file."""
        with open(self.log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    def add_document(self, 
                    filename: str, 
                    doc_id: int, 
                    metadata: Dict,
                    file_hash: Optional[str] = None,
                    processed_path: Optional[str] = None) -> None:
        """Add a document to the ingestion log.
        
        Args:
            filename: Original filename
            doc_id: Database document ID
            metadata: Document metadata
            file_hash: SHA-256 hash of the file (optional)
            processed_path: Path to the processed file in PROCESSED_DIR (optional)
        """
        log_data = self._load_log()
        
        # Add new document
        doc_entry = {
            "filename": filename,
            "doc_id": doc_id,
            "ingestion_date": datetime.now().isoformat(),
            "metadata": metadata,
            "file_hash": file_hash,
            "processed_path": processed_path
        }
        log_data["documents"].append(doc_entry)
        log_data["last_updated"] = datetime.now().isoformat()
        
        self._save_log(log_data)
        logger.info(f"Added document to ingestion log: {filename}")
    
    def get_all_documents(self) -> List[Dict]:
        """Get list of all ingested documents."""
        log_data = self._load_log()
        return log_data["documents"]
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict]:
        """Get document entry by database ID."""
        for doc in self.get_all_documents():
            if doc["doc_id"] == doc_id:
                return doc
        return None
    
    def get_document_by_filename(self, filename: str) -> Optional[Dict]:
        """Get document entry by original filename."""
        for doc in self.get_all_documents():
            if doc["filename"] == filename:
                return doc
        return None
    
    def generate_report(self) -> str:
        """Generate a human-readable report of ingested documents."""
        docs = self.get_all_documents()
        
        report = ["# Ingested Documents Report", ""]
        report.append(f"Total Documents: {len(docs)}")
        report.append(f"Last Updated: {self._load_log()['last_updated']}")
        report.append(f"\nProcessed Directory: {PROCESSED_DIR}")
        report.append("\n## Documents:")
        
        # Group documents by type
        docs_by_type = {}
        for doc in docs:
            doc_type = doc['metadata'].get('type', 'unknown')
            if doc_type not in docs_by_type:
                docs_by_type[doc_type] = []
            docs_by_type[doc_type].append(doc)
        
        # Generate report by document type
        for doc_type, type_docs in sorted(docs_by_type.items()):
            report.append(f"\n### {doc_type.upper()}")
            for doc in sorted(type_docs, key=lambda x: x['metadata'].get('title', '')):
                report.extend([
                    f"\n#### {doc['metadata'].get('title', doc['filename'])}",
                    f"- Original File: {doc['filename']}",
                    f"- Document ID: {doc['doc_id']}",
                    f"- Ingestion Date: {doc['ingestion_date']}",
                    f"- Author: {doc['metadata'].get('author', 'N/A')}",
                    f"- Source: {doc['metadata'].get('source', 'N/A')}",
                    f"- Processed Path: {doc.get('processed_path', 'N/A')}"
                ])
        
        return "\n".join(report)
    
    def save_report(self) -> None:
        """Generate and save a report to the processed directory."""
        report = self.generate_report()
        
        with open(self.report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"Saved ingestion report to {self.report_file}")

# Create global instance
ingestion_log = IngestionLog() 