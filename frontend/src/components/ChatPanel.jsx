import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, BrainCircuit, Bug } from 'lucide-react';

const ChatPanel = ({ onIntentChange }) => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am the VisionTraceAI Agent. Ask me about the current video stream, detections, or system status.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [reasoning, setReasoning] = useState(null);
  const [isDebugMode, setIsDebugMode] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, reasoning]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input;
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setInput('');
    setIsLoading(true);
    setReasoning(null);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage })
      });

      if (!response.ok) throw new Error('Network response was not ok');
      
      const data = await response.json();
      
      setMessages(prev => [...prev, { role: 'assistant', content: data.final_answer }]);
      
      if (data.intent || data.raw_results) {
        setReasoning({
          intent: data.intent,
          time: data.processing_time_sec,
          results: data.raw_results
        });
        if (onIntentChange) {
          onIntentChange(data.intent);
        }
      }
    } catch (error) {
      console.error("Chat Error:", error);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error communicating with the agent backend.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-panel glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%', maxHeight: '500px', flex: 1 }}>
      <div className="status-header" style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center' }}>
        <Bot size={20} />
        <h3 style={{ margin: 0, marginLeft: '0.5rem' }}>AI Assistant</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginLeft: 'auto' }}>
          {reasoning && (
            <button 
              onClick={() => setIsDebugMode(!isDebugMode)}
              title="Show Evidence Drawer"
              style={{
                background: isDebugMode ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
                border: `1px solid ${isDebugMode ? 'var(--text-accent)' : 'var(--border-color)'}`,
                color: isDebugMode ? 'var(--text-accent)' : 'var(--text-secondary)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.25rem 0.5rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.25rem',
                fontSize: '0.8rem',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <BrainCircuit size={14} />
              Evidence Drawer {isDebugMode ? '▲' : '▼'}
            </button>
          )}
        </div>
      </div>
      
      <div className="chat-messages" style={{ flex: 1, overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-bubble ${msg.role}`} style={{
            display: 'flex', gap: '0.75rem', 
            flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
            alignItems: 'flex-start'
          }}>
            <div className="chat-avatar" style={{ 
              width: '32px', height: '32px', borderRadius: '50%', 
              background: msg.role === 'user' ? 'var(--primary)' : '#8b5cf6',
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
            }}>
              {msg.role === 'user' ? <User size={16} color="#fff" /> : <Bot size={16} color="#fff" />}
            </div>
            <div className="chat-content" style={{
              background: msg.role === 'user' ? 'rgba(59, 130, 246, 0.15)' : 'rgba(255, 255, 255, 0.05)',
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-md)',
              border: `1px solid ${msg.role === 'user' ? 'rgba(59, 130, 246, 0.3)' : 'transparent'}`,
              color: 'var(--text-primary)',
              fontSize: '0.9rem',
              lineHeight: '1.4',
              maxWidth: '80%'
            }}>
              {msg.role === 'user' ? (
                msg.content
              ) : (
                <div 
                  className="assistant-html-content"
                  dangerouslySetInnerHTML={{ __html: msg.content }} 
                />
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="chat-bubble assistant" style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
            <div className="chat-avatar" style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#8b5cf6', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <Bot size={16} color="#fff" />
            </div>
            <div className="chat-content" style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
               <span className="dot-pulse">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {isDebugMode && reasoning && (
        <div className="ai-reasoning-panel" style={{
          padding: '1rem',
          background: 'rgba(15, 17, 26, 0.8)',
          backdropFilter: 'blur(10px)',
          borderTop: '1px solid rgba(56, 189, 248, 0.2)',
          borderBottom: '1px solid rgba(56, 189, 248, 0.2)',
          fontSize: '0.85rem',
          color: 'var(--text-secondary)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: 'var(--text-accent)' }}>
            <BrainCircuit size={16} /> <strong>Raw Evidence & Embeddings</strong>
          </div>
          <div style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', maxHeight: '200px', overflowY: 'auto' }}>
            <div style={{ marginBottom: '0.5rem' }}><strong>Intent Parsed:</strong> {reasoning.intent?.intent}</div>
            {reasoning.results && reasoning.results.map((r, i) => (
              <div key={i} style={{ paddingLeft: '0.75rem', borderLeft: '2px solid rgba(56, 189, 248, 0.5)', margin: '0.5rem 0', background: 'rgba(255,255,255,0.02)', padding: '0.5rem' }}>
                <span style={{ color: '#bae6fd' }}>Tool: {r.tool}</span>
                {Array.isArray(r.result) && r.result.length > 0 && (
                   <div style={{ marginTop: '0.25rem' }}>
                     {r.result.map((item, j) => (
                       <div key={j} style={{ marginLeft: '0.5rem', color: '#94a3b8' }}>
                         • Track ID: {item.track_id || 'N/A'} | Conf: {(item.confidence_score || item.confidence || 0).toFixed(3)}
                         {item.camera_id && ` | Cam: ${item.camera_id}`}
                       </div>
                     ))}
                   </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="chat-input-area" style={{ padding: '1rem', borderTop: '1px solid var(--border-color)' }}>
        <form onSubmit={handleSend} style={{ display: 'flex', gap: '0.5rem' }}>
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask VisionTraceAI..."
            disabled={isLoading}
            style={{
              flex: 1,
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              padding: '0.5rem 1rem',
              color: 'var(--text-primary)',
              outline: 'none'
            }}
          />
          <button type="submit" disabled={isLoading || !input.trim()} style={{
            background: 'var(--primary)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            padding: '0.5rem 1rem',
            cursor: (isLoading || !input.trim()) ? 'not-allowed' : 'pointer',
            opacity: (isLoading || !input.trim()) ? 0.6 : 1,
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatPanel;
