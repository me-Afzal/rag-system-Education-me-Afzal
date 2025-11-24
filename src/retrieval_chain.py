"""
Retrieval chain configuration and management
"""
from langchain.chains.qa_with_sources.retrieval import RetrievalQAWithSourcesChain
from typing import Optional, Dict, Any


class RetrievalChainManager:
    """Manages retrieval chain configuration"""
    
    def __init__(self, vector_db, llm):
        self.vector_db = vector_db
        self.llm = llm
        self.k = 6  # Number of documents to retrieve
        
    def create_chain(self) -> RetrievalQAWithSourcesChain:
        """
        Create retrieval QA chain
        
        Returns:
            RetrievalQAWithSourcesChain instance
        """
        retriever = self.vector_db.as_retriever(search_kwargs={"k": self.k})
        
        chain = RetrievalQAWithSourcesChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            return_source_documents=True
        )
        
        return chain
    
    def get_answer(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get answer for a query
        
        Args:
            query: User question
            
        Returns:
            Dictionary with answer and sources
        """
        try:
            chain = self.create_chain()
            result = chain.invoke({'question': query})
            return result
        except Exception as e:
            return None