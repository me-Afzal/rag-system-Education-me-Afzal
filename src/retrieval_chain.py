"""
Retrieval chain configuration and management
"""
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.prompts import PromptTemplate
from typing import Optional, Dict, Any
import streamlit as st


class RetrievalChainManager:
    """Manages retrieval chain configuration"""
    
    def __init__(self, vector_db, llm):
        self.vector_db = vector_db
        self.llm = llm
        self.k = 6  # Number of documents to retrieve
        
    def create_chain(self) -> RetrievalQA:
        """
        Create retrieval QA chain
        
        Returns:
            RetrievalQA instance
        """
        # Create retriever
        retriever = self.vector_db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.k}
        )
        
        # Custom prompt template for clean answers WITHOUT inline citations
        prompt_template = """You are a helpful AI assistant answering questions based on provided context.

Use the following pieces of context to answer the question at the end. 
Provide a clear, detailed, and well-structured answer.

Important instructions:
- If you don't know the answer, say "I don't have enough information to answer this question."
- DO NOT include source citations or document names in your answer
- Answer in a natural, conversational tone
- Be comprehensive but concise

Context:
{context}

Question: {question}

Answer:"""

        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Create chain using RetrievalQA
        chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )
        
        return chain
    
    def get_answer(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get answer for a query
        
        Args:
            query: User question
            
        Returns:
            Dictionary with answer and sources (sources listed separately)
        """
        try:
            chain = self.create_chain()
            
            # Invoke chain
            result = chain.invoke({'query': query})
            
            # Extract answer
            answer = result.get('result', 'No answer generated')
            
            # Extract and format sources
            source_docs = result.get('source_documents', [])
            sources = self._format_sources(source_docs)
            
            # Return formatted result
            return {
                'answer': answer,
                'sources': sources,
                'source_documents': source_docs
            }
            
        except Exception as e:
            st.error(f"Error generating answer: {str(e)}")
            
            # Show detailed error in expander
            with st.expander("Show error details"):
                import traceback
                st.code(traceback.format_exc())
            
            return None
    
    def _format_sources(self, source_docs) -> str:
        """
        Format source documents into readable citation string
        
        Args:
            source_docs: List of source documents
            
        Returns:
            Formatted string like "Document1.pdf, Document2.pdf"
        """
        if not source_docs:
            return "No sources found"
        
        # Extract unique source filenames
        sources = set()
        for doc in source_docs:
            source = doc.metadata.get('source', 'Unknown')
            sources.add(source)
        
        # Return sorted, comma-separated list
        if len(sources) == 1:
            return list(sources)[0]
        else:
            return ", ".join(sorted(sources))