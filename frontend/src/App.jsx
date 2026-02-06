import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
    MessageSquare,
    Plus,
    Trash2,
    Send,
    User,
    Bot,
    Landmark,
    FileText,
    Users,
    IndianRupee
} from 'lucide-react';

const API_BASE = '/api';

function App() {
    const [sessions, setSessions] = useState([]);
    const [currentSessionId, setCurrentSessionId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const textareaRef = useRef(null);

    // Fetch sessions on mount
    useEffect(() => {
        fetchSessions();
    }, []);

    // Fetch messages when session changes
    useEffect(() => {
        if (currentSessionId) {
            fetchMessages(currentSessionId);
        } else {
            setMessages([]);
        }
    }, [currentSessionId]);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
        }
    }, [input]);

    const fetchSessions = async () => {
        try {
            const res = await fetch(`${API_BASE}/sessions`);
            const data = await res.json();
            setSessions(data);
        } catch (error) {
            console.error('Failed to fetch sessions:', error);
        }
    };

    const fetchMessages = async (sessionId) => {
        try {
            const res = await fetch(`${API_BASE}/session/${sessionId}/messages`);
            const data = await res.json();
            setMessages(data);
        } catch (error) {
            console.error('Failed to fetch messages:', error);
        }
    };

    const createNewSession = () => {
        setCurrentSessionId(null);
        setMessages([]);
    };

    const deleteSession = async (sessionId, e) => {
        e.stopPropagation();
        try {
            await fetch(`${API_BASE}/session/${sessionId}`, { method: 'DELETE' });
            setSessions(sessions.filter(s => s.id !== sessionId));
            if (currentSessionId === sessionId) {
                setCurrentSessionId(null);
                setMessages([]);
            }
        } catch (error) {
            console.error('Failed to delete session:', error);
        }
    };

    const sendMessage = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = input.trim();
        setInput('');
        setIsLoading(true);

        // Add user message immediately
        const tempUserMsg = { role: 'user', content: userMessage };
        setMessages(prev => [...prev, tempUserMsg]);

        try {
            const res = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: userMessage,
                    session_id: currentSessionId
                })
            });

            const data = await res.json();

            // Update session ID if new
            if (!currentSessionId) {
                setCurrentSessionId(data.session_id);
                fetchSessions();
            }

            // Add assistant response
            setMessages(prev => [
                ...prev.filter(m => m !== tempUserMsg),
                { role: 'user', content: userMessage },
                { role: 'assistant', content: data.response }
            ]);
        } catch (error) {
            console.error('Failed to send message:', error);
            setMessages(prev => [
                ...prev,
                { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const handleSuggestionClick = (text) => {
        setInput(text);
        textareaRef.current?.focus();
    };

    const suggestions = [
        {
            title: "Scholarships for Students",
            text: "What scholarships are available for students with disabilities in Tamil Nadu?"
        },
        {
            title: "Women Entrepreneurs",
            text: "Tell me about government schemes for women entrepreneurs in India"
        },
        {
            title: "Skill Development",
            text: "What is PM Kaushal Vikas Yojana and how can I apply?"
        },
        {
            title: "Agricultural Support",
            text: "What schemes are available for farmers and agricultural workers?"
        }
    ];

    return (
        <div className="app">
            {/* Sidebar */}
            <aside className="sidebar">
                <div className="sidebar-header">
                    <div className="logo">
                        <div className="logo-icon">
                            <Landmark />
                        </div>
                        <span className="logo-text">Schemes Assistant</span>
                    </div>
                    <button className="new-chat-btn" onClick={createNewSession}>
                        <Plus size={18} />
                        New Chat
                    </button>
                </div>

                <div className="sessions-list">
                    <div className="sessions-title">Chat History</div>
                    {sessions.map(session => (
                        <div
                            key={session.id}
                            className={`session-item ${currentSessionId === session.id ? 'active' : ''}`}
                            onClick={() => setCurrentSessionId(session.id)}
                        >
                            <MessageSquare size={16} className="session-icon" />
                            <span className="session-title">{session.title}</span>
                            <button
                                className="session-delete"
                                onClick={(e) => deleteSession(session.id, e)}
                            >
                                <Trash2 size={14} />
                            </button>
                        </div>
                    ))}
                </div>
            </aside>

            {/* Main Content */}
            <main className="main-content">
                <header className="chat-header">
                    <h1 className="chat-title">
                        {currentSessionId
                            ? sessions.find(s => s.id === currentSessionId)?.title || 'Chat'
                            : 'New Conversation'
                        }
                    </h1>
                    <span className="header-badge">Powered by Gemini</span>
                </header>

                {messages.length === 0 && !isLoading ? (
                    <div className="welcome-screen">
                        <div className="welcome-icon">
                            <Landmark />
                        </div>
                        <h2 className="welcome-title">Government Schemes Assistant</h2>
                        <p className="welcome-subtitle">
                            I can help you find information about Tamil Nadu and All India government schemes.
                            Ask me about eligibility, benefits, application process, and more!
                        </p>
                        <div className="suggestions">
                            {suggestions.map((suggestion, i) => (
                                <div
                                    key={i}
                                    className="suggestion-card"
                                    onClick={() => handleSuggestionClick(suggestion.text)}
                                >
                                    <h4>{suggestion.title}</h4>
                                    <p>{suggestion.text}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="messages-container">
                        {messages.map((msg, i) => (
                            <div key={i} className={`message ${msg.role}`}>
                                <div className="message-avatar">
                                    {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                                </div>
                                <div className="message-content">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className="message assistant">
                                <div className="message-avatar">
                                    <Bot size={18} />
                                </div>
                                <div className="message-content">
                                    <div className="typing-indicator">
                                        <span></span>
                                        <span></span>
                                        <span></span>
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                )}

                <div className="input-area">
                    <div className="input-container">
                        <div className="input-wrapper">
                            <textarea
                                ref={textareaRef}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Ask about government schemes..."
                                rows={1}
                                disabled={isLoading}
                            />
                        </div>
                        <button
                            className="send-btn"
                            onClick={sendMessage}
                            disabled={!input.trim() || isLoading}
                        >
                            <Send />
                        </button>
                    </div>
                    <p className="input-hint">Press Enter to send, Shift+Enter for new line</p>
                </div>
            </main>
        </div>
    );
}

export default App;
