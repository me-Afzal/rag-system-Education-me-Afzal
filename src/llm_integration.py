"""
LLM integration and configuration
"""
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st


class LLMManager:
    """Manages LLM configuration and initialization"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash-lite"):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = 0.3
        
    def get_llm(self) -> ChatGoogleGenerativeAI:
        """
        Initialize and return LLM instance
        
        Returns:
            ChatGoogleGenerativeAI instance
        """
        llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=self.temperature
        )
        return llm


def load_api_key() -> str:
    """
    Load API key from Streamlit secrets
    
    Returns:
        API key string
    """
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception as e:
        st.error("ERROR: GEMINI_API_KEY not found in .streamlit/secrets.toml")
        st.info("Please create .streamlit/secrets.toml and add: GEMINI_API_KEY = 'your-api-key'")
        st.stop()