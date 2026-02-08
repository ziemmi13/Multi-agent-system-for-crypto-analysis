import os
import pathlib
import pandas as pd
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from dotenv import load_dotenv

# Global cache for CSV data
_csv_data = None

# Determine directory paths
ROOT_DIR = pathlib.Path(__file__).parents[3]

current_dir = pathlib.Path(__file__).parent
CHROMA_DB_DIR = current_dir / "database" / "chroma_db"
CSV_PATH = current_dir / "database" / "cryptonews.csv"

load_dotenv(ROOT_DIR / '.env')

# Initialize embedding function
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name='text-embedding-3-small'
)

# Initialize ChromaDB client
client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
collection = client.get_or_create_collection(name="cryptonews_collection")

# Load CSV data and cache it
def _load_csv_data():
    """Load CSV data once and cache it"""
    global _csv_data
    if _csv_data is None:
        _csv_data = pd.read_csv(CSV_PATH)
    return _csv_data

def search_similar_news(article_headline: str, article_summary: str, similarity_threshold: float=0.1) -> str:
    """
    Search for similar news articles summaries in the RAG database.
    
    Args:
        article_headline: The headline of the article
        article_summary: The summary of the article to search for
        similarity_threshold: Minimum similarity score to consider a match (0.0 to 1.0)
    
    Returns:
        A formatted string with matching article information (headline, summary, cause, effect, sentiment) if found, 
        otherwise empty string if no matches.
    """
    try:
        # Generate embedding for the article text
        article_embedding = openai_ef([article_summary])
        
        # Query ChromaDB for similar articles
        results = collection.query(
            query_embeddings=article_embedding,
            n_results=5
        )

        if not results['ids'] or len(results['ids'][0]) == 0:
            return ""
        
        # Load CSV data to get cause, effect, headline, etc.
        csv_data = _load_csv_data()
        
        # Process results and filter by similarity threshold
        matches = []
        distances = results['distances'][0] if results.get('distances') else []
        ids = results['ids'][0]
        
        for article_id, distance in zip(ids, distances):
            # Convert distance to similarity (similarity = 1 - distance for cosine)
            similarity = max(0.0, 1.0 - distance)
            
            # Filter by similarity threshold
            if similarity >= similarity_threshold:
                # Get full data from CSV using int(article_id)
                try:
                    article_row = csv_data[csv_data['id'] == int(article_id)]
                except (ValueError, TypeError):
                    continue
                
                if not article_row.empty:
                    row = article_row.iloc[0]
                    matches.append({
                        'url': row.get('url', 'N/A'),
                        'summary': row.get('summary', 'N/A'),
                        'cause': row.get('cause', 'N/A'),
                        'effect': row.get('effect', 'N/A'),
                        'sentiment': row.get('sentiment', 'N/A'),
                        'similarity': similarity,
                    })
        
        if not matches:
            return ""
        
        # Format output: compact list of matching articles
        output = []
        for match in matches:
            output.append(f"**Similar Article Found ({match['similarity']*100:.0f}% match):**")
            output.append(f"Original Headline: {article_headline}")
            output.append(f"- URL: {match['url']}")
            output.append(f"- Summary: {match['summary']}")
            output.append(f"- Cause: {match['cause']}")
            output.append(f"- Effect: {match['effect']}")
            output.append(f"- Sentiment: {match['sentiment']}")
            output.append("")
        
        return "\n".join(output).strip()
        
    except Exception as e:
        return f"Error searching similar news: {str(e)}"
