from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import database
import rag

app = FastAPI(title="Government Schemes Chatbot API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


class SessionCreate(BaseModel):
    title: Optional[str] = "New Chat"


class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: str


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: str


@app.get("/")
async def root():
    return {"message": "Government Schemes Chatbot API", "status": "running"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message and get a response."""
    session_id = request.session_id
    
    # Create new session if not provided
    if not session_id:
        session_id = database.create_session()
    
    # Get chat history for context
    history = database.get_session_messages(session_id)
    chat_history = [{"role": msg["role"], "content": msg["content"]} for msg in history]
    
    # Save user message
    database.add_message(session_id, "user", request.query)
    
    # Generate response using RAG
    response = rag.generate_response(request.query, chat_history)
    
    # Save assistant response
    database.add_message(session_id, "assistant", response)
    
    # Update session title based on first message
    if len(history) == 0:
        # Use first few words of query as title
        title = request.query[:50] + "..." if len(request.query) > 50 else request.query
        database.update_session_title(session_id, title)
    
    return ChatResponse(response=response, session_id=session_id)


@app.post("/api/session", response_model=SessionResponse)
async def create_session(request: SessionCreate):
    """Create a new chat session."""
    session_id = database.create_session(request.title)
    sessions = database.get_all_sessions()
    session = next((s for s in sessions if s["id"] == session_id), None)
    if session:
        return SessionResponse(**session)
    raise HTTPException(status_code=500, detail="Failed to create session")


@app.get("/api/sessions", response_model=List[SessionResponse])
async def get_sessions():
    """Get all chat sessions."""
    sessions = database.get_all_sessions()
    return [SessionResponse(**s) for s in sessions]


@app.get("/api/session/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: str):
    """Get all messages for a session."""
    messages = database.get_session_messages(session_id)
    return [MessageResponse(**m) for m in messages]


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session."""
    database.delete_session(session_id)
    return {"message": "Session deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
