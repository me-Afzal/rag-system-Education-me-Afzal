"""
Vector store creation and management using FAISS
"""
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from typing import List, Tuple, Optional
import streamlit as st
from src.document_processor import extract_text_from_file


class VectorStoreManager:
    """Manages vector database creation and operations"""
    
    def __init__(self, embedder):
        self.embedder = embedder
        self.chunk_size = 700
        self.chunk_overlap = 50
        
    def create_chunks(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of chunked documents
        """
        splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", " "],
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        chunks = splitter.split_documents(documents)
        return chunks
    
    def create_vector_database(
        self, 
        documents: List[Document], 
        progress_bar=None, 
        status_text=None
    ) -> Tuple[Optional[FAISS], int]:
        """
        Create FAISS vector database with embeddings
        
        Args:
            documents: List of Document objects
            progress_bar: Streamlit progress bar (optional)
            status_text: Streamlit text placeholder (optional)
            
        Returns:
            Tuple of (vector_db, num_chunks)
        """
        try:
            # Update progress
            if status_text:
                status_text.text("Chunking documents...")
            if progress_bar:
                progress_bar.progress(0.4)
            
            # Create chunks
            chunks = self.create_chunks(documents)
            
            if not chunks:
                st.error("No text chunks created from documents")
                return None, 0
            
            # Update progress
            if status_text:
                status_text.text(f"Creating embeddings for {len(chunks)} chunks...")
            if progress_bar:
                progress_bar.progress(0.6)
            
            # Update progress
            if status_text:
                status_text.text("Building vector database...")
            if progress_bar:
                progress_bar.progress(0.8)
            
            # Create FAISS vector database
            vector_db = FAISS.from_documents(chunks, embedding=self.embedder)
            
            # Complete
            if status_text:
                status_text.text("Complete!")
            if progress_bar:
                progress_bar.progress(1.0)
            
            return vector_db, len(chunks)
        
        except Exception as e:
            st.error(f"Error creating vector database: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return None, 0
    
    def process_files(
        self, 
        uploaded_files, 
        progress_bar=None, 
        status_text=None,
        max_pages: int = 20
    ) -> List[Document]:
        """
        Process uploaded files and create Document objects
        
        Args:
            uploaded_files: List of uploaded file objects
            progress_bar: Streamlit progress bar (optional)
            status_text: Streamlit text placeholder (optional)
            max_pages: Maximum pages to process per PDF (default: 20)
            
        Returns:
            List of Document objects
        """
        documents = []
        total_files = len(uploaded_files)
        
        for idx, file in enumerate(uploaded_files):
            progress = (idx + 1) / total_files * 0.3
            
            if status_text:
                status_text.text(f"Extracting text from {file.name}...")
            if progress_bar:
                progress_bar.progress(progress)
            
            # Use the imported function directly
            text, filename = extract_text_from_file(file)
            
            # Debug output
            if text.strip():
                st.write(f"✓ {filename}: Extracted {len(text)} characters")
                doc = Document(
                    page_content=text,
                    metadata={"source": filename}
                )
                documents.append(doc)
            else:
                st.warning(f"{filename}: No text extracted (0 characters)")
        
        return documents