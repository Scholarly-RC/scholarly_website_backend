"""
Script to process PDF and store chunks in Pinecone vector database.

This script:
1. Extracts text from the scholarly-data.pdf file
2. Chunks the text into 1000-character chunks with 200-character overlap
3. Generates embeddings using OpenAI
4. Stores chunks in Pinecone with metadata

Note: While Pinecone provides embedding capabilities for querying, 
embeddings must be generated (using OpenAI) for initial indexing.

Environment variables required:
- PINECONE_API_KEY
- PINECONE_INDEX_NAME
- OPENAI_API_KEY (for generating embeddings)
- PINECONE_ENVIRONMENT (optional, defaults to "us-east-1")
- PINECONE_EMBEDDING_DIMENSION (optional, defaults to 1536)
- OPENAI_EMBEDDING_MODEL (optional, defaults to "text-embedding-3-small")
"""

import os
import sys
from pathlib import Path
from typing import List, Dict

import pdfplumber
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

# Load environment variables
load_dotenv()

# Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Get paths
BASE_DIR = Path(__file__).resolve().parent.parent
PDF_PATH = BASE_DIR / "data" / "scholarly-data.pdf"


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from PDF file."""
    print(f"Extracting text from {pdf_path}...")
    text = ""
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n\n--- Page {page_num} ---\n\n{page_text}"
                print(f"Processed page {page_num}...")
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        sys.exit(1)
    
    print(f"Extracted {len(text)} characters from PDF")
    return text


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict[str, any]]:
    """Split text into chunks with overlap."""
    print(f"Chunking text into {chunk_size}-character chunks with {overlap}-character overlap...")
    
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]
        
        # Find the last space or newline to avoid cutting words
        if end < len(text):
            last_space = chunk_text.rfind(' ')
            last_newline = chunk_text.rfind('\n')
            cut_point = max(last_space, last_newline)
            if cut_point > chunk_size * 0.5:  # Only adjust if we're not cutting too much
                chunk_text = chunk_text[:cut_point]
                end = start + cut_point
        
        if chunk_text.strip():  # Only add non-empty chunks
            chunks.append({
                "text": chunk_text.strip(),
                "chunk_index": chunk_index,
                "start": start,
                "end": min(end, len(text))
            })
            chunk_index += 1
        
        # Move start position with overlap
        start = end - overlap
        if start >= len(text):
            break
    
    print(f"Created {len(chunks)} chunks")
    return chunks


def get_embedding_model_for_dimension(dimension: int) -> str:
    """
    Get the appropriate OpenAI embedding model for a given dimension.
    Returns the model name that produces embeddings of the specified dimension.
    """
    # OpenAI embedding model dimensions:
    # text-embedding-ada-002: 1536
    # text-embedding-3-small: 1536 (default)
    # text-embedding-3-large: 3072
    
    # For non-standard dimensions, we'll need to use a model that can be dimension-reduced
    # or let the user specify
    if dimension == 1536:
        return "text-embedding-3-small"
    elif dimension == 3072:
        return "text-embedding-3-large"
    elif dimension == 1024:
        # 1024 is not a standard OpenAI dimension, might be Pinecone's model
        # Use text-embedding-3-small and reduce dimensions
        return "text-embedding-3-small"
    else:
        # Default to text-embedding-3-small
        return "text-embedding-3-small"


def generate_embeddings(texts: List[str], client: OpenAI, dimension: int) -> List[List[float]]:
    """Generate embeddings for a list of texts using OpenAI."""
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL")
    
    # If model not specified, choose based on dimension
    if not embedding_model:
        embedding_model = get_embedding_model_for_dimension(dimension)
    
    print(f"Generating embeddings for {len(texts)} chunks using OpenAI ({embedding_model})...")
    print(f"Target dimension: {dimension}")
    
    embeddings = []
    batch_size = 100  # Process in batches to avoid rate limits
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            # For dimension 1024, we can use text-embedding-3-small with dimension parameter
            if dimension == 1024:
                response = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=batch,
                    dimensions=1024
                )
            else:
                response = client.embeddings.create(
                    model=embedding_model,
                    input=batch
                )
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
            print(f"Generated embeddings for batch {i // batch_size + 1} ({len(batch_embeddings)} chunks)")
        except Exception as e:
            print(f"Error generating embeddings for batch {i // batch_size + 1}: {e}")
            sys.exit(1)
    
    return embeddings


def store_in_pinecone(chunks: List[Dict], embeddings: List[List[float]], index_name: str, dimension: int):
    """Store chunks in Pinecone. Uses embeddings if provided, otherwise uses text-based upsert."""
    print(f"Storing {len(chunks)} chunks in Pinecone index '{index_name}'...")
    
    # Initialize Pinecone
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("Error: PINECONE_API_KEY environment variable not set")
        sys.exit(1)
    
    pc = Pinecone(api_key=api_key)
    
    # Verify embedding dimensions match index dimension
    if embeddings:
        embedding_dim = len(embeddings[0]) if embeddings else 0
        if embedding_dim != dimension:
            print(f"Error: Embedding dimension ({embedding_dim}) does not match index dimension ({dimension})")
            sys.exit(1)
    
    # Check if index exists, create if not
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    
    if index_name not in existing_indexes:
        print(f"Index '{index_name}' does not exist. Creating it...")
        # Get dimension from environment or use default
        # If using Pinecone's embedding, dimension depends on the model
        dimension = int(os.getenv("PINECONE_EMBEDDING_DIMENSION", "1536"))
        try:
            from pinecone import ServerlessSpec
            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
                )
            )
        except ImportError:
            # Fallback for newer API versions
            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine"
            )
        print(f"Index '{index_name}' created successfully with dimension {dimension}")
    else:
        # Get the dimension of the existing index
        index_info = pc.describe_index(index_name)
        dimension = index_info.dimension
        print(f"Using existing index '{index_name}' with dimension {dimension}")
    
    # Connect to index
    index = pc.Index(index_name)
    
    # If embeddings are provided, use vector-based upsert
    if embeddings and len(embeddings) == len(chunks):
        # Prepare vectors for upsert
        vectors_to_upsert = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_id = f"chunk_{chunk['chunk_index']}"
            metadata = {
                "text": chunk["text"],
                "chunk_index": chunk["chunk_index"],
                "start": chunk["start"],
                "end": chunk["end"],
                "source": "scholarly-data.pdf"
            }
            
            vectors_to_upsert.append({
                "id": vector_id,
                "values": embedding,
                "metadata": metadata
            })
        
        # Upsert in batches
        batch_size = 100
        for i in range(0, len(vectors_to_upsert), batch_size):
            batch = vectors_to_upsert[i:i + batch_size]
            try:
                index.upsert(vectors=batch)
                print(f"Upserted batch {i // batch_size + 1} ({len(batch)} vectors)")
            except Exception as e:
                print(f"Error upserting batch {i // batch_size + 1}: {e}")
                sys.exit(1)
    else:
        # If no embeddings were provided, we cannot proceed
        # Pinecone requires vectors for upsert
        print("Error: No embeddings provided.")
        print("Embeddings must be generated before storing in Pinecone.")
        sys.exit(1)
    
    print(f"Successfully stored {len(chunks)} chunks in Pinecone")


def main():
    """Main execution function."""
    print("=" * 60)
    print("PDF to Pinecone Processing Script")
    print("=" * 60)
    
    # Validate environment variables
    required_vars = ["PINECONE_API_KEY", "PINECONE_INDEX_NAME", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Validate PDF file exists
    if not PDF_PATH.exists():
        print(f"Error: PDF file not found at {PDF_PATH}")
        sys.exit(1)
    
    # Initialize OpenAI client for embeddings
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Step 1: Extract text from PDF
    text = extract_text_from_pdf(PDF_PATH)
    
    if not text.strip():
        print("Error: No text extracted from PDF")
        sys.exit(1)
    
    # Step 2: Chunk the text
    chunks = chunk_text(text)
    
    if not chunks:
        print("Error: No chunks created from text")
        sys.exit(1)
    
    # Get index dimension (check existing index or use default)
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = os.getenv("PINECONE_INDEX_NAME")
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    
    if index_name in existing_indexes:
        index_info = pc.describe_index(index_name)
        dimension = index_info.dimension
        print(f"Found existing index '{index_name}' with dimension {dimension}")
    else:
        dimension = int(os.getenv("PINECONE_EMBEDDING_DIMENSION", "1536"))
        print(f"Will create index '{index_name}' with dimension {dimension}")
    
    # Step 3: Generate embeddings using OpenAI (matching index dimension)
    chunk_texts = [chunk["text"] for chunk in chunks]
    embeddings = generate_embeddings(chunk_texts, openai_client, dimension)
    
    if len(embeddings) != len(chunks):
        print(f"Error: Mismatch between chunks ({len(chunks)}) and embeddings ({len(embeddings)})")
        sys.exit(1)
    
    # Verify embedding dimensions
    if embeddings:
        embedding_dim = len(embeddings[0])
        if embedding_dim != dimension:
            print(f"Error: Generated embedding dimension ({embedding_dim}) does not match index dimension ({dimension})")
            sys.exit(1)
        print(f"Verified: Embeddings have dimension {embedding_dim} (matches index)")
    
    # Step 4: Store in Pinecone
    store_in_pinecone(chunks, embeddings, index_name, dimension)
    
    print("=" * 60)
    print("Processing completed successfully!")
    print(f"Total chunks processed: {len(chunks)}")
    print("=" * 60)


if __name__ == "__main__":
    main()

