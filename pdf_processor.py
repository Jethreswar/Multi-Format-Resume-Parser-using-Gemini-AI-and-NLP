"""
PDF Processor Module with updated PyMuPDF compatibility
"""

import io
import sys

def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF using PyMuPDF with proper import"""
    text = ""
    
    # Try PyMuPDF first
    try:
        # Standard import for PyMuPDF
        import fitz
        
        with io.BytesIO(pdf_bytes) as pdf_stream:
            # Different PyMuPDF versions have different APIs
            try:
                # Version 1.18.x approach
                doc = fitz.open(stream=pdf_stream, filetype="pdf")
            except (TypeError, AttributeError):
                try:
                    # Direct buffer approach for newer versions
                    doc = fitz.open(stream=pdf_stream)
                except (TypeError, AttributeError):
                    # Last resort for very new versions
                    doc = fitz.Document(stream=pdf_stream, filetype="pdf")
            
            text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                text += page.get_text()
            return text
    except Exception as e:
        print(f"PyMuPDF error: {str(e)}", file=sys.stderr)
    
    # Fallback to PyPDF2
    try:
        import PyPDF2
        with io.BytesIO(pdf_bytes) as pdf_stream:
            reader = PyPDF2.PdfReader(pdf_stream)
            text = ""
            for page_num in range(len(reader.pages)):
                text += reader.pages[page_num].extract_text() or ""
            if text.strip():
                return text
    except Exception as e:
        print(f"PyPDF2 error: {str(e)}", file=sys.stderr)
    
    # Last resort: pdfplumber
    try:
        import pdfplumber
        with io.BytesIO(pdf_bytes) as pdf_stream:
            with pdfplumber.open(pdf_stream) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                if text.strip():
                    return text
    except Exception as e:
        print(f"pdfplumber error: {str(e)}", file=sys.stderr)
    
    if not text.strip():
        raise ValueError("Could not extract text from PDF using any available method")
    
    return text


def get_pdf_metadata(pdf_bytes):
    """Extract metadata from PDF"""
    try:
        import fitz  # PyMuPDF
        with io.BytesIO(pdf_bytes) as pdf_stream:
            try:
                # Try different methods for compatibility
                doc = fitz.open(stream=pdf_stream, filetype="pdf")
            except (AttributeError, TypeError):
                try:
                    doc = fitz.Document(stream=pdf_stream, filetype="pdf")
                except AttributeError:
                    doc = fitz.open(stream=pdf_stream)
            return doc.metadata
    except Exception as e:
        print(f"PyMuPDF metadata error: {e}")
        # Fallback to PyPDF2
        try:
            import PyPDF2
            with io.BytesIO(pdf_bytes) as pdf_stream:
                reader = PyPDF2.PdfReader(pdf_stream)
                return reader.metadata
        except Exception:
            return {}