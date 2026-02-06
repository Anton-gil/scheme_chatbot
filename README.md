# Government Schemes RAG Chatbot

A modern, AI-powered chatbot for Tamil Nadu and All-India government schemes using Retrieval Augmented Generation (RAG) with the Gemini API.

## Features

- 🤖 **RAG-based System**: Uses ChromaDB vector database for semantic search across 816 government schemes
- 🎨 **Modern UI**: Beautiful React frontend with dark theme, glassmorphism, and smooth animations
- 💬 **Context-Aware Conversations**: Maintains conversation context for follow-up questions
- 📊 **Markdown Support**: Properly formatted responses with tables, lists, and rich text
- 💾 **Chat History**: SQLite-based persistent chat history with session management
- 🔍 **Semantic Search**: Advanced embedding-based search for relevant scheme retrieval
- ⚡ **Fast & Responsive**: Built with FastAPI backend and Vite-powered React frontend

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **ChromaDB**: Vector database for embeddings
- **Sentence Transformers**: all-MiniLM-L6-v2 for embeddings
- **Google Gemini API**: LLM for response generation
- **SQLite**: Chat history persistence

### Frontend
- **React**: UI framework
- **Vite**: Build tool and dev server
- **react-markdown**: Markdown rendering with table support
- **lucide-react**: Modern icon library

## Project Structure

```
Chatbot/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── rag.py               # RAG pipeline implementation
│   ├── database.py          # SQLite database operations
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── index.css        # Styles
│   │   └── main.jsx         # React entry point
│   ├── package.json         # NPM dependencies
│   └── vite.config.js       # Vite configuration
└── cleanedTamilNadu_statecentral_816scheme.json  # Schemes data
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Gemini API Key

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
SCHEMES_JSON_PATH=../../cleanedTamilNadu_statecentral_816scheme.json
```

4. Start the backend server:
```bash
python -m uvicorn main:app --port 8000
```

The backend will automatically:
- Load the embedding model
- Index the schemes into ChromaDB (first time only)
- Start the API server on http://localhost:8000

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at http://localhost:5173

## Usage

1. Open http://localhost:5173 in your browser
2. Click "New Chat" to start a conversation
3. Ask questions about government schemes, for example:
   - "What scholarships are available for students with disabilities?"
   - "Tell me about schemes for women entrepreneurs"
   - "What agricultural subsidies can farmers get?"
4. The chatbot will search the database and provide relevant, accurate information
5. Ask follow-up questions to get more details about specific schemes

## Key Features Explained

### RAG Pipeline
- **Embedding**: Converts scheme documents into vector embeddings using sentence-transformers
- **Retrieval**: Finds top-10 semantically similar schemes with distance-based filtering
- **Context-Aware Search**: Combines recent conversation context with current query for better relevance
- **Response Generation**: Uses Gemini API to generate human-like responses based on retrieved context

### Conversation Context
- Maintains chat history for each session
- Includes last 2 user queries in search to maintain topic continuity
- Prevents hallucination by strictly enforcing context-only responses
- Supports natural follow-up questions like "Where do I apply?" or "What documents are needed?"

### UI/UX
- Dark theme with purple accent colors
- Glassmorphism effects and smooth animations
- Responsive design for all screen sizes
- Typing indicators and loading states
- Session management with delete functionality
- Markdown tables with proper formatting

## API Endpoints

### Chat
- `POST /api/chat` - Send a message and get a response
- Body: `{ "query": "string", "session_id": "optional-uuid" }`

### Sessions
- `GET /api/sessions` - Get all chat sessions
- `POST /api/session` - Create a new session
- `DELETE /api/session/{session_id}` - Delete a session
- `GET /api/session/{session_id}/messages` - Get messages for a session

## Development Notes

- The ChromaDB index is persistent and will be reused across restarts
- Chat history is stored in `chat_history.db` SQLite database
- The `.env` file is excluded from version control for security
- Frontend uses Vite's proxy feature to forward API requests to the backend

## Future Improvements

- [ ] Add user authentication
- [ ] Support for multiple languages (Tamil, Hindi)
- [ ] Export chat history as PDF
- [ ] Advanced filtering (by department, scheme type, etc.)
- [ ] Voice input support
- [ ] Mobile app version

## License

MIT License

## Contributors

Built as part of Apploom internship project
