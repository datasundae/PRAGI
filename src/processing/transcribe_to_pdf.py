import whisper
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from pathlib import Path
import torch
from tqdm import tqdm
import time
import multiprocessing
import argparse
import textwrap
import re
import soundfile as sf
import numpy as np

def transcribe_audio(audio_path):
    """Transcribe audio file using Whisper"""
    # Check if CUDA is available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Load model
    print("Loading Whisper model...")
    model = whisper.load_model("tiny", device=device)
    
    # Transcribe
    print("Transcribing audio...")
    result = model.transcribe(
        audio_path,
        language="en",
        fp16=False,  # Use FP32 for CPU
        beam_size=1,  # Reduce beam size for faster processing
        best_of=1,  # Reduce number of candidates
        temperature=0.0  # Use greedy decoding for faster processing
    )
    
    return result["text"]

def create_pdf(text, output_path):
    """Create PDF from transcription text"""
    # Normalize text
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    
    # Create PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # Set margins (20mm on all sides)
    width, height = A4
    margin = 20 * 2.83465  # Convert mm to points (1mm = 2.83465 points)
    
    # Set font and size
    c.setFont("Helvetica", 12)
    
    # Calculate text width and height
    text_width = width - 2 * margin
    line_height = 14  # Approximate line height in points
    
    # Process text in chunks
    paragraphs = text.split('\n\n')
    y = height - margin - line_height
    
    print("Creating PDF...")
    for paragraph in paragraphs:
        # Split paragraph into words
        words = paragraph.split()
        current_line = []
        current_width = 0
        
        for word in words:
            word_width = c.stringWidth(word + ' ', "Helvetica", 12)
            if current_width + word_width <= text_width:
                current_line.append(word)
                current_width += word_width
            else:
                # Write current line
                c.drawString(margin, y, ' '.join(current_line))
                y -= line_height
                
                # Check if we need a new page
                if y < margin + line_height:
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y = height - margin - line_height
                
                current_line = [word]
                current_width = word_width
        
        # Write remaining words
        if current_line:
            c.drawString(margin, y, ' '.join(current_line))
            y -= line_height
        
        # Add paragraph spacing
        y -= line_height
        
        # Check if we need a new page
        if y < margin + line_height:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = height - margin - line_height
    
    c.save()
    print(f"PDF saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Transcribe audio to text and create PDF")
    parser.add_argument("--mode", choices=["transcribe", "pdf", "both"], default="both",
                      help="Operation mode: transcribe (audio to text), pdf (text to PDF), or both")
    parser.add_argument("--audio", required=True,
                      help="Path to input audio file")
    parser.add_argument("--output-dir", required=True,
                      help="Path to output directory")
    parser.add_argument("--output-name", default="transcription",
                      help="Base name for output files (without extension)")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    if args.mode in ["transcribe", "both"]:
        print("Transcribing audio...")
        text = transcribe_audio(args.audio)
        # Save transcription
        text_file = os.path.join(args.output_dir, f"{args.output_name}.txt")
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Transcription saved to: {text_file}")
    
    if args.mode in ["pdf", "both"]:
        print("Creating PDF...")
        text_file = os.path.join(args.output_dir, f"{args.output_name}.txt")
        if not os.path.exists(text_file):
            print("Error: Transcription file not found. Please run transcription first.")
            return
        
        pdf_file = create_pdf(text, os.path.join(args.output_dir, f"{args.output_name}.pdf"))
        # Rename the PDF file to use the specified output name
        new_pdf_file = os.path.join(args.output_dir, f"{args.output_name}.pdf")
        os.rename(pdf_file, new_pdf_file)
        print(f"PDF saved to: {new_pdf_file}")

if __name__ == "__main__":
    main() 