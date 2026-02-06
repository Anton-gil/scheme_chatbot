import json
import os
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Paths
CHROMA_PATH = Path(__file__).parent / "chroma_db"
SCHEMES_PATH = Path(__file__).parent / os.getenv("SCHEMES_JSON_PATH", "../../cleanedTamilNadu_statecentral_816scheme.json")

# Initialize embedding model
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("Embedding model loaded!")


class SentenceTransformerEmbedding(EmbeddingFunction):
    """Custom embedding function for ChromaDB using SentenceTransformers."""
    
    def __init__(self, model):
        self._model = model
    
    def __call__(self, input: Documents) -> Embeddings:
        embeddings = self._model.encode(input, convert_to_numpy=True)
        return embeddings.tolist()
    
    def name(self) -> str:
        return "sentence-transformer-all-MiniLM-L6-v2"


# Initialize ChromaDB with persistent storage
chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))

# Create custom embedding function
embed_fn = SentenceTransformerEmbedding(embedding_model)

# Get or create collection
collection = chroma_client.get_or_create_collection(
    name="government_schemes",
    metadata={"hnsw:space": "cosine"},
    embedding_function=embed_fn
)


def load_and_index_schemes():
    """Load schemes from JSON and index them in ChromaDB."""
    # Check if already indexed
    if collection.count() > 0:
        print(f"Schemes already indexed. Found {collection.count()} documents.")
        return
    
    print("Loading and indexing schemes...")
    
    with open(SCHEMES_PATH, 'r', encoding='utf-8') as f:
        schemes = json.load(f)
    
    documents = []
    metadatas = []
    ids = []
    
    for i, scheme in enumerate(schemes):
        # Create a comprehensive text document for each scheme
        doc_parts = []
        
        scheme_name = scheme.get("Scheme Name", "Unknown Scheme")
        department = scheme.get("Department", "Unknown Department")
        
        doc_parts.append(f"Scheme Name: {scheme_name}")
        doc_parts.append(f"Department: {department}")
        
        if scheme.get("Details"):
            doc_parts.append(f"Details: {scheme['Details']}")
        
        if scheme.get("Benefits"):
            benefits = scheme["Benefits"]
            if isinstance(benefits, list):
                doc_parts.append(f"Benefits: {'; '.join(str(b) for b in benefits)}")
            else:
                doc_parts.append(f"Benefits: {benefits}")
        
        if scheme.get("Eligibility"):
            eligibility = scheme["Eligibility"]
            if isinstance(eligibility, list):
                doc_parts.append(f"Eligibility: {'; '.join(str(e) for e in eligibility)}")
            else:
                doc_parts.append(f"Eligibility: {eligibility}")
        
        if scheme.get("Application Process"):
            app_process = scheme["Application Process"]
            if isinstance(app_process, dict):
                mode = app_process.get("Mode", "")
                steps = app_process.get("Steps", [])
                if isinstance(steps, list):
                    steps_text = " ".join(str(s) for s in steps)
                else:
                    steps_text = str(steps)
                doc_parts.append(f"Application Process: Mode - {mode}. Steps: {steps_text}")
            else:
                doc_parts.append(f"Application Process: {app_process}")
        
        if scheme.get("Documents Required"):
            docs_req = scheme["Documents Required"]
            if isinstance(docs_req, list):
                doc_parts.append(f"Documents Required: {'; '.join(str(d) for d in docs_req)}")
            else:
                doc_parts.append(f"Documents Required: {docs_req}")
        
        full_doc = "\n".join(doc_parts)
        
        documents.append(full_doc)
        metadatas.append({
            "scheme_name": scheme_name,
            "department": department,
            "index": i
        })
        ids.append(f"scheme_{i}")
    
    # Add to collection in batches
    batch_size = 50
    for i in range(0, len(documents), batch_size):
        end_idx = min(i + batch_size, len(documents))
        collection.add(
            documents=documents[i:end_idx],
            metadatas=metadatas[i:end_idx],
            ids=ids[i:end_idx]
        )
        print(f"Indexed {end_idx}/{len(documents)} schemes...")
    
    print(f"Successfully indexed {len(documents)} schemes!")


def search_schemes(query: str, n_results: int = 5):
    """Search for relevant schemes based on query."""
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results


def generate_response(query: str, chat_history: list = None):
    """Generate a response using RAG with Gemini."""
    
    # Build search query with context from chat history
    search_query = query
    if chat_history and len(chat_history) > 0:
        # Include last 2 user messages for context
        recent_user_queries = [msg["content"] for msg in chat_history[-4:] if msg["role"] == "user"]
        if recent_user_queries:
            # Combine recent queries with current query for better search
            search_query = " ".join(recent_user_queries[-2:]) + " " + query
    
    # Search for more schemes to ensure we get relevant ones
    search_results = search_schemes(search_query, n_results=10)

    
    # Build context from search results with relevance filtering
    context_parts = []
    if search_results and search_results['documents'] and search_results['distances']:
        documents = search_results['documents'][0]
        distances = search_results['distances'][0]
        
        # Only include results with good relevance (low distance)
        # Lower distance = more relevant
        for i, (doc, distance) in enumerate(zip(documents, distances)):
            # Only include if distance is reasonable (< 1.5 is usually good)
            if distance < 1.5:
                context_parts.append(f"--- Relevant Scheme {i+1} (Relevance: {1.0 - distance:.2f}) ---\n{doc}")
    
    # If no relevant results, inform the AI
    if not context_parts:
        context = "No highly relevant schemes found in the database for this query."
    else:
        context = "\n\n".join(context_parts)
    
    
    # Build the prompt
    system_prompt = """You are a helpful assistant specializing in Indian government schemes, particularly for Tamil Nadu and all-India schemes. 
Your role is to provide accurate, detailed information about government schemes based ONLY on the context provided below.

CRITICAL RULES:
1. ONLY use information from the context provided below - DO NOT make up or add information
2. If the answer is not in the context, clearly state "I don't have information about this in the provided schemes database"
3. Be specific and cite exact scheme names from the context
4. When providing details, copy them accurately from the context (eligibility, benefits, application process)
5. Format your response in clear, well-structured markdown with tables where appropriate
6. If multiple relevant schemes are found, compare them to help the user choose
7. MAINTAIN CONVERSATION CONTEXT: If the user asks a follow-up question (like "where do I apply?" or "what documents needed?"), answer about the SAME schemes discussed in the previous messages, NOT about different schemes

Context from relevant government schemes:
"""

    # Add conversation context note if there's chat history
    context_note = ""
    if chat_history and len(chat_history) > 0:
        context_note = "\n\nNOTE: This is a follow-up question in an ongoing conversation. Make sure to answer about the schemes already being discussed, not new unrelated schemes."
    
    full_prompt = f"{system_prompt}\n\n{context}\n\n---\n\nUser Question: {query}{context_note}\n\nPlease answer based ONLY on the schemes provided in the context above."
    
    # Build conversation history for Gemini
    messages = []
    
    if chat_history:
        for msg in chat_history[-6:]:  # Keep last 6 messages for context
            role = "user" if msg["role"] == "user" else "model"
            messages.append({"role": role, "parts": [msg["content"]]})
    
    # Add current query with context
    messages.append({"role": "user", "parts": [full_prompt]})
    
    # Generate response using Gemini
    model = genai.GenerativeModel('models/gemini-flash-latest')
    
    try:
        if len(messages) == 1:
            response = model.generate_content(full_prompt)
        else:
            chat = model.start_chat(history=messages[:-1])
            response = chat.send_message(full_prompt)
        
        return response.text
    except Exception as e:
        return f"I apologize, but I encountered an error while processing your request: {str(e)}"


# Index schemes on module load
load_and_index_schemes()
