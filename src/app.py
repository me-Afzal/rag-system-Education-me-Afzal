"""
Main Streamlit application
"""
import sys
import os
import streamlit as st
import time
from typing import Optional

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Import custom modules
from src.embeddings import EmbeddingManager
from src.vector_store import VectorStoreManager
from src.llm_integration import LLMManager, load_api_key
from src.retrieval_chain import RetrievalChainManager


# Page Configuration
st.set_page_config(
    page_title="DocQuery",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Dark Theme CSS
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #1e1e1e;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #2d2d30;
        padding: 2rem 1rem;
    }
    
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Main Header */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #ffffff !important;
        margin-bottom: 2rem;
        padding: 1.5rem;
        border-radius: 8px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }

    .sub-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #ffffff !important;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 1px solid #444;
        padding-bottom: 0.5rem;
    }

    /* Answer Card */
    .answer-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        font-size: 1.1rem;
        line-height: 1.6;
        color: #212529;
    }

    /* Question Card */
    .question-card {
        background: #3a3a3c;
        border: 1px solid #4a4a4c;
        border-radius: 8px;
        padding: 1.2rem;
        margin: 1rem 0;
        color: #ffffff;
    }

    /* Buttons */
    .stButton > button {
        background: #000;
        color: white !important;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        width: 100%;
        margin: 0.5rem 0;
        transition: all 0.3s;
    }

    .stButton > button:hover {
        background: #333;
    }

    /* File Item */
    .file-item {
        background: #3a3a3c;
        border-left: 3px solid #000;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
        border-radius: 0 4px 4px 0;
        color: #ffffff;
        font-size: 0.9rem;
    }

    /* Status Box */
    .status-box {
        background: #1a1a1a;
        border: 1px solid #444;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #ffffff;
    }
    
    .status-box h3 {
        color: #ffffff !important;
        margin-top: 0;
    }
    
    .status-box p, .status-box ol, .status-box li {
        color: #ffffff !important;
    }

    .status-box-dark {
        background: #3a3a3c;
        border: 1px solid #4a4a4c;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #ffffff;
    }

    /* Text Input */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #3a3a3c;
        color: #ffffff;
        border: 1px solid #4a4a4c;
        border-radius: 4px;
    }

    /* File Uploader */
    [data-testid="stFileUploader"] {
        background-color: #3a3a3c;
        border: 2px dashed #666;
        border-radius: 8px;
        padding: 1rem;
    }

    [data-testid="stFileUploader"] * {
        color: #ffffff !important;
    }

    /* Progress Bar */
    .stProgress > div > div {
        background-color: #000;
    }

    /* Divider */
    hr {
        border-color: #444;
        margin: 2rem 0;
    }

    /* Headers in main content */
    .main h1, .main h2, .main h3 {
        color: #ffffff !important;
    }

    /* Info/Warning/Success boxes */
    .stAlert {
        background-color: #3a3a3c;
        color: #ffffff;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize all session state variables"""
    if 'vector_db' not in st.session_state:
        st.session_state.vector_db = None
    if 'uploaded_files_list' not in st.session_state:
        st.session_state.uploaded_files_list = []
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'processed' not in st.session_state:
        st.session_state.processed = False
    if 'num_chunks' not in st.session_state:
        st.session_state.num_chunks = 0
    if 'embedder' not in st.session_state:
        EmbeddingManager.initialize_embedder()


def render_sidebar(api_key: str):
    """Render sidebar with document management"""
    with st.sidebar:
        st.markdown("## Document Management")
        st.markdown("### Upload Documents")
        
        uploaded_files = st.file_uploader(
            "Upload PDF, DOCX, or TXT files",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            st.markdown("### Selected Files")
            for file in uploaded_files:
                file_size = len(file.getvalue()) / 1024
                st.markdown(
                    f'<div class="file-item">{file.name} ({file_size:.1f} KB)</div>', 
                    unsafe_allow_html=True
                )
            
            if not st.session_state.processed:
                if st.button("Process Documents"):
                    process_documents(uploaded_files, api_key)
        
        render_system_status()


def process_documents(uploaded_files, api_key: str):
    """Process uploaded documents"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Initialize managers
    vector_manager = VectorStoreManager(st.session_state.embedder)
    
    # Process files
    documents = vector_manager.process_files(
        uploaded_files, 
        progress_bar, 
        status_text
    )
    
    if documents:
        # Create vector database
        vector_db, num_chunks = vector_manager.create_vector_database(
            documents, 
            progress_bar, 
            status_text
        )
        
        if vector_db and num_chunks > 0:
            st.session_state.vector_db = vector_db
            st.session_state.uploaded_files_list = [f.name for f in uploaded_files]
            st.session_state.processed = True
            st.session_state.num_chunks = num_chunks
            
            st.success(f"Processed {len(documents)} document(s) into {num_chunks} chunks!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Failed to create vector database")
    else:
        st.error("No valid documents found")


def render_system_status():
    """Render system status section"""
    st.markdown("---")
    st.markdown("### System Status")
    
    if st.session_state.processed:
        st.markdown(f"""
        <div class="status-box-dark">
            <strong>Status:</strong> Ready<br>
            <strong>Documents:</strong> {len(st.session_state.uploaded_files_list)}<br>
            <strong>Text Chunks:</strong> {st.session_state.num_chunks}<br>
            <strong>Vector DB:</strong> Active
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Clear All"):
            clear_session_state()
    else:
        st.markdown("""
        <div class="status-box-dark">
            <strong>Status:</strong> Waiting<br>
            Upload and process documents to begin
        </div>
        """, unsafe_allow_html=True)


def clear_session_state():
    """Clear all session state"""
    st.session_state.vector_db = None
    st.session_state.uploaded_files_list = []
    st.session_state.chat_history = []
    st.session_state.processed = False
    st.session_state.num_chunks = 0
    st.rerun()


def render_main_content(api_key: str):
    """Render main content area"""
    st.markdown('<h1 class="main-header">DocQuery</h1>', unsafe_allow_html=True)
    
    if st.session_state.processed:
        render_chat_interface(api_key)
    else:
        render_empty_state()


def render_chat_interface(api_key: str):
    """Render chat interface"""
    st.markdown('<h2 class="sub-header">Ask Questions</h2>', unsafe_allow_html=True)
    st.markdown("Enter your question:")
    
    query = st.text_area(
        "question_input",
        placeholder="Type your question about the documents here...",
        height=100,
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        send_btn = st.button("Send Query", type="primary")
    with col2:
        if len(st.session_state.chat_history) > 0:
            if st.button("Clear History"):
                st.session_state.chat_history = []
                st.rerun()
    
    if send_btn and query.strip():
        handle_query(query, api_key)
    
    render_chat_history()


def handle_query(query: str, api_key: str):
    """Handle user query"""
    with st.spinner("Generating answer..."):
        # Initialize LLM and retrieval chain
        llm_manager = LLMManager(api_key)
        llm = llm_manager.get_llm()
        
        retrieval_manager = RetrievalChainManager(st.session_state.vector_db, llm)
        result = retrieval_manager.get_answer(query)
        
        if result:
            answer = result.get('answer', 'No answer generated')
            sources = result.get('sources', 'N/A')
            
            st.session_state.chat_history.append({
                'question': query,
                'answer': answer,
                'sources': sources
            })
            
            st.rerun()


def render_chat_history():
    """Render chat history"""
    if len(st.session_state.chat_history) > 0:
        st.markdown("---")
        
        for idx, chat in enumerate(reversed(st.session_state.chat_history)):
            # Question
            st.markdown(f"""
            <div class="question-card">
                <strong>Question {len(st.session_state.chat_history) - idx}:</strong><br>
                {chat['question']}
            </div>
            """, unsafe_allow_html=True)
            
            # Answer
            st.markdown('<h2 class="sub-header">Answer</h2>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="answer-card">
                {chat['answer']}<br><br>
                <strong>Sources:</strong> {chat['sources']}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")


def render_empty_state():
    """Render empty state"""
    st.markdown('<h2 class="sub-header">Getting Started</h2>', unsafe_allow_html=True)
    st.markdown("""
    <div class="status-box">
        <h3>Welcome to DocQuery</h3>
        <p>To get started:</p>
        <ol>
            <li>Upload your documents (PDF, DOCX, or TXT) using the sidebar</li>
            <li>Click "Process Documents" to analyze them</li>
            <li>Ask questions about your documents</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application entry point"""
    # Load API key
    api_key = load_api_key()
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar(api_key)
    
    # Render main content
    render_main_content(api_key)


if __name__ == "__main__":
    main()