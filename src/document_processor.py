"""
Document processing module for extracting text from various file formats
"""
import pdfplumber
import docx
import tempfile
import os
from typing import Tuple
import streamlit as st


def extract_text_from_pdf(file) -> str:
    """Extract text from PDF using pdfplumber"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.read())
            tmp_file_path = tmp_file.name
        
        text = ""
        with pdfplumber.open(tmp_file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        os.unlink(tmp_file_path)
        return text
    except Exception as e:
        st.error(f"Error extracting PDF '{file.name}': {str(e)}")
        return ""


def extract_text_from_docx(file) -> str:
    """Extract text from DOCX file"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            tmp_file.write(file.read())
            tmp_file_path = tmp_file.name
        
        doc = docx.Document(tmp_file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
        
        os.unlink(tmp_file_path)
        return text
    except Exception as e:
        st.error(f"Error extracting DOCX '{file.name}': {str(e)}")
        return ""


def extract_text_from_txt(file) -> str:
    """Extract text from TXT file"""
    try:
        return file.read().decode('utf-8')
    except UnicodeDecodeError:
        try:
            file.seek(0)
            return file.read().decode('latin-1')
        except Exception as e:
            st.error(f"Error extracting TXT '{file.name}': {str(e)}")
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
    
    if file_extension == 'pdf':
        return extract_text_from_pdf(file), filename
    elif file_extension == 'docx':
        return extract_text_from_docx(file), filename
    elif file_extension == 'txt':
        return extract_text_from_txt(file), filename
    else:
        st.warning(f"Unsupported file type: {file_extension}")
        return "", filename