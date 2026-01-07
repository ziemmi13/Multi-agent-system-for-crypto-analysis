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

# Determine Chroma DB path: prefer project-level `database/chroma_db` if present,
# otherwise fall back to `root_agent/database/chroma_db`.
project_root = pathlib.Path(__file__).resolve().parents[4]
agent_root = root_dir
project_db = project_root / "database" / "chroma_db"
agent_db = agent_root / "database" / "chroma_db"

if (project_db / "chroma.sqlite3").exists():
    CHROMA_DB_PATH = project_db
elif (agent_db / "chroma.sqlite3").exists():
    CHROMA_DB_PATH = agent_db
else:
    CHROMA_DB_PATH = project_db  # fallback - will create if missing

# CSV path: prefer project-level CSV
project_csv = project_root / "database" / "cryptonews.csv"
agent_csv = agent_root / "database" / "cryptonews.csv"
CSV_PATH = project_csv if project_csv.exists() else agent_csv

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

def search_similar_news(article_headline: str, article_summary: str, similarity_threshold: float = 0.7) -> str:
    """
    Search for similar news articles summaries in the RAG database.
    
    Args:
        article_headline: The headline of the article
        article_summary: The summary of the article to search for
        similarity_threshold: Similarity threshold (0-1, higher = more similar). Default 0.7.
    
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
                        'headline': row.get('headline', row.get('title', 'N/A')),
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
            output.append(f"- Headline: {match['headline']}")
            output.append(f"- Summary: {match['summary']}")
            output.append(f"- Cause: {match['cause']}")
            output.append(f"- Effect: {match['effect']}")
            output.append(f"- Sentiment: {match['sentiment']}")
            output.append("")
        
        return "\n".join(output).strip()
        
    except Exception as e:
        return f"Error searching similar news: {str(e)}"

