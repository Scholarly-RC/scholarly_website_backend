"""
DSPy RAG Chatbot Module with Pinecone Integration.

This module provides a RAG (Retrieval-Augmented Generation) chatbot
using DSPy and Pinecone vector database.
"""

import os
from typing import List, Optional

import dspy
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

# Load environment variables
load_dotenv()

# Initialize OpenAI client for query embeddings
_openai_client = None


def get_openai_client():
    """Get or create OpenAI client for generating query embeddings."""
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client



class PineconeRetriever(dspy.Retrieve):
    """
    Custom Pinecone retriever for DSPy.
    Retrieves relevant chunks from Pinecone based on query embedding.
    """
    
    def __init__(self, index_name: str, k: int = 5):
        super().__init__(k=k)
        self.index_name = index_name
        self.k = k
        
        # Initialize Pinecone
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")
        
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)
        
        # Get embedding model for queries (should match the one used for indexing)
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        
        # Get index dimension to determine if we need to reduce embedding dimensions
        try:
            index_info = self.pc.describe_index(index_name)
            self.index_dimension = index_info.dimension
        except Exception:
            # Default dimension if we can't get it
            self.index_dimension = 1536
    
    def forward(self, query_or_queries: str | List[str], k: Optional[int] = None) -> dspy.Prediction:
        """
        Retrieve relevant chunks from Pinecone.
        
        Args:
            query_or_queries: Single query string or list of query strings
            k: Number of results to return (overrides self.k if provided)
        
        Returns:
            dspy.Prediction with 'passages' field containing retrieved chunks
        """
        k = k or self.k
        
        # Handle single query or list of queries
        if isinstance(query_or_queries, str):
            queries = [query_or_queries]
        else:
            queries = query_or_queries
        
        all_passages = []
        
        for query in queries:
            # Generate embedding for the query
            try:
                openai_client = get_openai_client()
                
                # Generate embedding with appropriate dimension
                if self.index_dimension == 1024:
                    response = openai_client.embeddings.create(
                        model="text-embedding-3-small",
                        input=query,
                        dimensions=1024
                    )
                else:
                    response = openai_client.embeddings.create(
                        model=self.embedding_model,
                        input=query
                    )
                
                query_embedding = response.data[0].embedding
            except Exception as e:
                raise ValueError(f"Error generating query embedding: {e}")
            
            # Query Pinecone with the embedding vector
            try:
                results = self.index.query(
                    vector=query_embedding,
                    top_k=k,
                    include_metadata=True
                )
            except Exception as e:
                raise ValueError(f"Error querying Pinecone: {e}")
            
            # Extract passages from results
            for match in results.matches:
                if match.metadata and "text" in match.metadata:
                    all_passages.append(match.metadata["text"])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_passages = []
        for passage in all_passages:
            if passage not in seen:
                seen.add(passage)
                unique_passages.append(passage)
        
        return dspy.Prediction(passages=unique_passages[:k])


class RAGChatbot:
    """
    RAG Chatbot using DSPy for question answering.
    """
    
    def __init__(self, index_name: Optional[str] = None, k: int = 5):
        """
        Initialize the RAG Chatbot.
        
        Args:
            index_name: Pinecone index name (defaults to PINECONE_INDEX_NAME env var)
            k: Number of chunks to retrieve for context
        """
        self.index_name = index_name or os.getenv("PINECONE_INDEX_NAME")
        if not self.index_name:
            raise ValueError("PINECONE_INDEX_NAME must be provided or set as environment variable")
        
        self.k = k
        
        # Initialize DSPy with OpenAI LM
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Get LLM model from environment variable
        # Format should be "openai/model-name" for DSPy
        llm_model = os.getenv("OPENAI_LLM_MODEL", "openai/gpt-5-nano")
        
        # If model doesn't have "openai/" prefix, add it
        if not llm_model.startswith("openai/"):
            llm_model = f"openai/{llm_model}"
        
        # Configure DSPy with OpenAI
        lm = dspy.LM(llm_model, api_key=openai_api_key)
        dspy.configure(lm=lm)
        
        # Initialize retriever
        self.retriever = PineconeRetriever(index_name=self.index_name, k=k)
        
        # Define the signature for Q&A
        # Format: "input_fields -> output_fields"
        self.qa_signature = "question, context -> answer"
        
        # Create the RAG module: Retrieve + ChainOfThought
        self.rag_module = dspy.ChainOfThought(self.qa_signature)
    
    def query(self, question: str) -> dict:
        """
        Process a user question and return an answer.
        
        Args:
            question: The user's question
        
        Returns:
            Dictionary with 'answer' and optionally 'sources' (retrieved chunks)
        """
        # Retrieve relevant context
        retrieval_result = self.retriever(question)
        context = "\n\n".join(retrieval_result.passages)
        
        # Generate answer using DSPy
        prediction = self.rag_module(
            question=question,
            context=context
        )
        
        return {
            "answer": prediction.answer,
            "sources": retrieval_result.passages
        }


# Global chatbot instance (lazy initialization)
_chatbot_instance = None


def get_chatbot() -> RAGChatbot:
    """
    Get or create the global chatbot instance.
    This allows for singleton pattern to avoid reinitializing DSPy.
    """
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = RAGChatbot()
    return _chatbot_instance

