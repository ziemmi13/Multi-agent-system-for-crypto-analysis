import os
import pathlib
import pandas as pd
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
root_dir = pathlib.Path(__file__).parent.parent.parent.parent

load_dotenv(root_dir / '.env')

# Initialize ChromaDB client and collection
CHROMA_DB_PATH = root_dir / "database" / "chroma_db"
CSV_PATH = root_dir / "database" / "cryptonews.csv"

# Initialize embedding function
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name='text-embedding-3-small'
)

# Initialize ChromaDB client
client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
collection = client.get_or_create_collection(name="cryptonews_collection")

# Load CSV data for retrieving cause and effect
_csv_data = None

def _load_csv_data():
    """Load CSV data once and cache it"""
    global _csv_data
    if _csv_data is None:
        _csv_data = pd.read_csv(CSV_PATH)
    return _csv_data

def search_similar_news(article_text: str, similarity_threshold: float = 0.3) -> str:
    """
    Search for similar news articles summaries in the RAG database.
    
    Args:
        article_text: The text content or title of the article to search for
        similarity_threshold: Maximum distance threshold (lower = more similar). 
                             Default 0.3 for very similar matches.
                             ChromaDB uses cosine distance (0 = identical, 1 = completely different)
    
    Returns:
        A formatted string with matching article information (summary, cause, effect, sentiment) if found, otherwise a message if no similar articles found.
    """
    try:
        # Generate embedding for the article text
        article_embedding = openai_ef([article_text])
        
        # Query ChromaDB for similar articles
        # n_results=5 to get top matches, we'll filter by threshold
        results = collection.query(
            query_embeddings=article_embedding,
            n_results=5
        )
        
        if not results['ids'] or len(results['ids'][0]) == 0:
            return "No similar articles summaries found in the database."
        
        # Load CSV data to get cause and effect
        csv_data = _load_csv_data()
        
        # Process results and filter by distance threshold
        matches = []
        distances = results['distances'][0] if results.get('distances') else []
        ids = results['ids'][0]
        metadatas = results['metadatas'][0] if results.get('metadatas') else []
        
        for i, (article_id, distance) in enumerate(zip(ids, distances)):
            # Filter by similarity threshold (distance <= threshold means similar)
            if distance <= similarity_threshold:
                # Get full data from CSV
                article_row = csv_data[csv_data['id'] == int(article_id)]
                
                if not article_row.empty:
                    row = article_row.iloc[0]
                    matches.append({
                        'id': article_id,
                        'distance': distance,
                        'summary': row.get('summary', 'N/A'),
                        'cause': row.get('cause', 'N/A'),
                        'effect': row.get('effect', 'N/A'),
                        'sentiment': row.get('sentiment', 'N/A'),
                        'datetime': row.get('datetime', 'N/A'),
                        'url': row.get('url', 'N/A')
                    })
        
        if not matches:
            return f"No similar articles found (closest match distance: {distances[0]:.4f}, threshold: {similarity_threshold})"
        
        # Format output
        output = []
        for match in matches:
            output.append(f"=== Similar Article Found (Distance: {match['distance']:.4f}) ===")
            output.append(f"Date: {match['datetime']}")
            output.append(f"\nSummary:\n{match['summary']}")
            output.append(f"\nCause:\n{match['cause']}")
            output.append(f"\nEffect:\n{match['effect']}")
            output.append(f"Sentiment: {match['sentiment']}")
            output.append("")  # Empty line between matches
        
        return "\n".join(output)
        
    except Exception as e:
        return f"Error searching similar news: {str(e)}"

