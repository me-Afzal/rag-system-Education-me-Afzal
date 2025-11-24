"""
Document processing module for extracting text from various file formats
"""
import pdfplumber
import docx
import tempfile
import os
import gc
from typing import Tuple
import streamlit as st


def extract_text_from_pdf_with_ocr(file, max_pages: int = 20) -> str:
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
            pages_to_process = min(total_pages, max_pages)
            
            if total_pages > max_pages:
                st.info(f"PDF has {total_pages} pages. Processing first {max_pages} pages.")
            else:
                st.info(f"Processing {pages_to_process} pages...")
            
            # Create progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for page_num, page in enumerate(pdf.pages[:pages_to_process], 1):
                try:
                    # Update progress
                    status_text.text(f"Processing page {page_num}/{pages_to_process}...")
                    progress_bar.progress(page_num / pages_to_process)
                    
                    # Try extracting text normally
                    page_text = page.extract_text()
                    
                    # If we got enough text, use it
                    if page_text and len(page_text.strip()) > 100:
                        text += page_text + "\n"
                        st.write(f"Page {page_num}/{pages_to_process}: Text-based extraction ({len(page_text)} chars)")
                    else:
                        # Use OCR for image-based pages
                        st.info(f"Page {page_num}/{pages_to_process}: Using OCR (scanned image)")
                        
                        try:
                            ocr_text = extract_with_ocr(tmp_file_path, page_num)
                            if ocr_text:
                                text += ocr_text + "\n"
                                st.info(f"OCR completed ({len(ocr_text)} chars)")
                            else:
                                st.warning(f"Page {page_num}: OCR returned no text")
                        
                        except Exception as ocr_error:
                            st.error(f"Page {page_num} OCR failed: {str(ocr_error)}")
                            # Continue with next page instead of crashing
                            continue
                    
                    # Force garbage collection after each page to free memory
                    gc.collect()
                
                except Exception as page_error:
                    st.error(f"Error on page {page_num}: {str(page_error)}")
                    # Continue with next pages
                    continue
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
        
        # Cleanup temp file
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        
        final_text = text.strip()
        
        if final_text:
            st.success(f"Extraction complete! Total: {len(final_text)} characters")
        else:
            st.error("No text extracted from PDF")
        
        # Final cleanup
        gc.collect()
        
        return final_text
    
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        
        with st.expander("Show error details"):
            import traceback
            st.code(traceback.format_exc())
        
        # Cleanup on error
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        
        gc.collect()
        return ""


def extract_with_ocr(pdf_path: str, page_num: int) -> str:
    """Extract text using EasyOCR with memory optimization"""
    doc = None
    img = None
    img_array = None
    
    try:
        import easyocr
        import fitz  # PyMuPDF
        import numpy as np
        from PIL import Image
        
        # Initialize reader once (cached in session)
        if 'ocr_reader' not in st.session_state:
            with st.spinner("Loading OCR model (first time only, ~2 minutes)..."):
                st.session_state.ocr_reader = easyocr.Reader(['en'], gpu=False)
            st.success("OCR model loaded!")
        
        reader = st.session_state.ocr_reader
        
        # Open PDF and convert page to image
        doc = fitz.open(pdf_path)
        page = doc[page_num - 1]
        
        # Render at REDUCED quality to save memory (1.5x instead of 2x)
        mat = fitz.Matrix(1.5, 1.5)  # REDUCED from 2x to 1.5x
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # RESIZE large images to save memory
        max_dimension = 2000  # Max width or height
        if max(img.size) > max_dimension:
            ratio = max_dimension / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            st.write(f"Resized image to {new_size} for memory efficiency")
        
        # Convert to numpy array
        img_array = np.array(img)
        
        # Perform OCR with timeout protection
        with st.spinner(f"Running OCR on page {page_num}..."):
            results = reader.readtext(img_array, detail=0, paragraph=True)
        
        text = '\n'.join(results)
        
        # Cleanup
        del img_array, img, pix
        doc.close()
        gc.collect()
        
        return text
    
    except ImportError as e:
        st.error(f"Missing library: {e}")
        st.info("Install: pip install easyocr PyMuPDF")
        return ""
    
    except MemoryError:
        st.error(f"Out of memory on page {page_num}. Try reducing max_pages or skip this page.")
        return ""
    
    except Exception as e:
        st.error(f"OCR Error on page {page_num}: {str(e)}")
        
        with st.expander("Show OCR error details"):
            import traceback
            st.code(traceback.format_exc())
        
        return ""
    
    finally:
        # Ensure cleanup even on error
        try:
            if doc:
                doc.close()
            if img_array is not None:
                del img_array
            if img is not None:
                del img
            gc.collect()
        except:
            pass


def extract_text_from_pdf(file, max_pages: int = 20) -> str:
    """Extract text from PDF (wrapper function)"""
    return extract_text_from_pdf_with_ocr(file, max_pages=max_pages)


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
        
        st.success(f"Extracted {len(text)} characters from DOCX")
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
        text = file.read().decode('utf-8')
        st.success(f"Extracted {len(text)} characters from TXT")
        return text
    
    except UnicodeDecodeError:
        try:
            file.seek(0)
            text = file.read().decode('latin-1')
            st.success(f"Extracted {len(text)} characters from TXT (Latin-1)")
            return text
        except Exception as e:
            st.error(f"Error extracting TXT: {str(e)}")
            return ""


def extract_text_from_file(file, max_pages: int = 20) -> Tuple[str, str]:
    """
    Extract text based on file extension
    
    Args:
        file: Uploaded file object
        max_pages: Maximum pages to process for PDFs (default: 20)
        
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
        text = extract_text_from_pdf(file, max_pages=max_pages)
    elif file_extension == 'docx':
        text = extract_text_from_docx(file)
    elif file_extension == 'txt':
        text = extract_text_from_txt(file)
    else:
        st.warning(f"Unsupported file type: .{file_extension}")
    
    return text, filename