"""
Document processing module for extracting text from various file formats
"""
import pdfplumber
import docx
import tempfile
import os
from typing import Tuple
import streamlit as st


def extract_text_from_pdf_with_ocr(file) -> str:
    """Extract text from PDF with OCR support for scanned documents"""
    text = ""
    tmp_file_path = None
    
    try:
        file.seek(0)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.read())
            tmp_file_path = tmp_file.name
        
        # Try regular text extraction first
        with pdfplumber.open(tmp_file_path) as pdf:
            total_pages = len(pdf.pages)
            st.info(f"Processing {total_pages} pages...")
            
            for page_num, page in enumerate(pdf.pages, 1):
                # Try extracting text normally
                page_text = page.extract_text()
                
                # If we got enough text, use it
                if page_text and len(page_text.strip()) > 100:
                    text += page_text + "\n"
                    st.write(f"✓ Page {page_num}/{total_pages}: Text-based extraction")
                else:
                    # Use OCR for image-based pages
                    st.warning(f"⚠ Page {page_num}/{total_pages}: Using OCR (scanned image)")
                    ocr_text = extract_with_ocr(tmp_file_path, page_num)
                    text += ocr_text + "\n"
        
        # Cleanup
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        
        final_text = text.strip()
        st.success(f"Total extracted: {len(final_text)} characters")
        
        return final_text
    
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        
        # Cleanup on error
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        
        return ""


def extract_with_ocr(pdf_path: str, page_num: int) -> str:
    """Extract text using EasyOCR"""
    try:
        import easyocr
        import fitz  # PyMuPDF
        import numpy as np
        from PIL import Image
        
        # Initialize reader once (cached in session)
        if 'ocr_reader' not in st.session_state:
            st.info("🔄 Loading OCR model (first time only, ~2 minutes)...")
            st.session_state.ocr_reader = easyocr.Reader(['en'], gpu=False)
            st.success("OCR model loaded!")
        
        reader = st.session_state.ocr_reader
        
        # Open PDF and convert page to image
        doc = fitz.open(pdf_path)
        page = doc[page_num - 1]
        
        # Render at high quality
        mat = fitz.Matrix(2, 2)  # 2x zoom
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to numpy array for EasyOCR
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_array = np.array(img)
        
        # Perform OCR
        results = reader.readtext(img_array, detail=0, paragraph=True)
        text = '\n'.join(results)
        
        doc.close()
        
        st.write(f"  ✓ OCR extracted {len(text)} characters")
        return text
    
    except ImportError as e:
        st.error(f"Missing library: {e}")
        st.info("Install: pip install easyocr PyMuPDF")
        return ""
    
    except Exception as e:
        st.error(f"OCR Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return ""

def extract_text_from_pdf(file) -> str:
    """Extract text from PDF (wrapper function)"""
    return extract_text_from_pdf_with_ocr(file)


def extract_text_from_docx(file) -> str:
    """Extract text from DOCX file"""
    tmp_file_path = None
    
    try:
        file.seek(0)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            tmp_file.write(file.read())
            tmp_file_path = tmp_file.name
        
        doc = docx.Document(tmp_file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs)
        
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        
        return text
    
    except Exception as e:
        st.error(f"Error extracting DOCX: {str(e)}")
        
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        
        return ""


def extract_text_from_txt(file) -> str:
    """Extract text from TXT file"""
    try:
        file.seek(0)
        return file.read().decode('utf-8')
    except UnicodeDecodeError:
        try:
            file.seek(0)
            return file.read().decode('latin-1')
        except Exception as e:
            st.error(f"Error extracting TXT: {str(e)}")
            return ""


def extract_text_from_file(file) -> Tuple[str, str]:
    """
    Extract text based on file extension
    
    Args:
        file: Uploaded file object
        
    Returns:
        Tuple of (extracted_text, filename)
    """
    filename = file.name
    file_extension = filename.split('.')[-1].lower()
    
    st.write(f"📄 Processing: **{filename}**")
    
    try:
        file.seek(0)
    except:
        pass
    
    text = ""
    
    if file_extension == 'pdf':
        text = extract_text_from_pdf(file)
    elif file_extension == 'docx':
        text = extract_text_from_docx(file)
    elif file_extension == 'txt':
        text = extract_text_from_txt(file)
    else:
        st.warning(f"Unsupported file type: .{file_extension}")
    
    return text, filename