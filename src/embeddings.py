"""
Embedding model initialization and management
"""
from langchain_community.embeddings import HuggingFaceEmbeddings
import streamlit as st


class EmbeddingManager:
    """Manages embedding model initialization and caching"""
    
    _instance = None
    _embedder = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingManager, cls).__new__(cls)
        return cls._instance
    
    def get_embedder(self):
        """Get or create embedder instance"""
        if self._embedder is None:
            with st.spinner("Loading embedding model..."):
                self._embedder = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    model_kwargs={'device': 'cpu'}
                )
        return self._embedder
    
    @staticmethod
    def initialize_embedder():
        """Initialize embedder in session state"""
        if 'embedder' not in st.session_state:
            manager = EmbeddingManager()
            st.session_state.embedder = manager.get_embedder()
        return st.session_state.embedder