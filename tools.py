"""
Tools compatibility module.

This module provides utility functions that might be imported by other modules
in the Resume Parser application.
"""

import re
import os
import datetime
from pathlib import Path

# PDF processing utilities
def extract_text_from_pdf(pdf_bytes):
    """Extract text content from PDF bytes"""
    try:
        import PyPDF2
        from io import BytesIO
        
        pdf_file = BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text()
            
        return text
    except ImportError:
        print("PyPDF2 not installed. Please install with: pip install PyPDF2")
        return ""
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

# Text processing utilities
def clean_text(text):
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters
    text = re.sub(r'[^\w\s.,;:()"-]', '', text)
    return text.strip()

def normalize_dates(date_str):
    """Normalize date formats"""
    # Handle common date formats
    patterns = [
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', r'\3-\1-\2'),  # MM/DD/YYYY to YYYY-MM-DD
        (r'(\d{1,2})-(\d{1,2})-(\d{4})', r'\3-\1-\2'),  # MM-DD-YYYY to YYYY-MM-DD
    ]
    
    result = date_str
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)
    
    return result

# File management utilities
def ensure_directory(directory_path):
    """Ensure directory exists, create if it doesn't"""
    Path(directory_path).mkdir(parents=True, exist_ok=True)
    
def get_file_extension(filename):
    """Get file extension from filename"""
    return os.path.splitext(filename)[1].lower()

# Data formatting utilities
def format_phone_number(phone):
    """Format phone numbers consistently"""
    # Remove non-numeric characters
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone  # Return original if format not recognized

# Add any other utility functions that might be needed