#!/usr/bin/env python3
import os
from pathlib import Path

def get_unprocessed_m4b_files():
    """Find M4B files that haven't been processed into PDFs yet."""
    # Define directories
    audio_dir = Path("/Volumes/NVME_Expansion/musartao/data/books/AudioIngest")
    processed_dir = Path("/Volumes/NVME_Expansion/musartao/data/books/Processed")
    
    # Get all M4B files
    m4b_files = list(audio_dir.glob("*.m4b"))
    print(f"Found {len(m4b_files)} M4B files in total")
    
    # Get all existing PDFs
    pdf_files = list(processed_dir.glob("*.pdf"))
    existing_pdf_names = {pdf.stem for pdf in pdf_files}
    print(f"Found {len(existing_pdf_names)} existing PDFs")
    
    # Find unprocessed M4B files
    unprocessed_m4b = []
    for m4b in m4b_files:
        base_name = m4b.stem
        if base_name not in existing_pdf_names:
            unprocessed_m4b.append(m4b)
    
    print(f"\nFound {len(unprocessed_m4b)} unprocessed M4B files:")
    for m4b in unprocessed_m4b:
        print(f"- {m4b.name}")
    
    return unprocessed_m4b

def main():
    unprocessed = get_unprocessed_m4b_files()
    
    # Save the list to a file
    output_file = "unprocessed_m4b_files.txt"
    with open(output_file, "w") as f:
        for m4b in unprocessed:
            f.write(f"{m4b}\n")
    
    print(f"\nList of unprocessed files saved to {output_file}")

if __name__ == "__main__":
    main() 