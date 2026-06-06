import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, BrainCircuit } from 'lucide-react';

const ChatPanel = ({ onIntentChange }) => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am the VisionTraceAI Agent. Ask me about the current video stream, detections, or system status.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [reasoning, setReasoning] = useState(null);
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
      <div className="status-header" style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)' }}>
        <Bot size={20} />
        <h3>AI Assistant</h3>
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
              {msg.content}
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

      {reasoning && (
        <div className="ai-reasoning-panel" style={{
          padding: '0.75rem 1rem',
          background: 'rgba(139, 92, 246, 0.1)',
          borderTop: '1px solid rgba(139, 92, 246, 0.2)',
          borderBottom: '1px solid rgba(139, 92, 246, 0.2)',
          fontSize: '0.8rem',
          color: 'var(--text-secondary)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem', color: '#a78bfa' }}>
            <BrainCircuit size={14} /> <strong>Agent Reasoning ({reasoning.time?.toFixed(2)}s)</strong>
          </div>
          <div style={{ fontFamily: 'monospace' }}>Intent: {JSON.stringify(reasoning.intent)}</div>
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
