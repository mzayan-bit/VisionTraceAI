import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, Users, Activity, Bug, Sparkles } from 'lucide-react';

const ChatPanel = ({ onIntentChange, peopleCount, activityLevel, totalPeople }) => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'System active. Tracking environment.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [systemHealth, setSystemHealth] = useState(1.0);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Listen for quick actions from VideoPlayer
  useEffect(() => {
    const handleQuickAction = async (e) => {
      await sendQuery(e.detail);
    };
    window.addEventListener('ai-query', handleQuickAction);
    return () => window.removeEventListener('ai-query', handleQuickAction);
  }, [messages, isLoading]);

  const sendQuery = async (queryText) => {
    if (!queryText.trim() || isLoading) return;

    const history = messages.map(m => ({ role: m.role, content: m.content }));
    setMessages(prev => [...prev, { role: 'user', content: queryText }]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText, history: history })
      });

      if (!response.ok) throw new Error('Network response was not ok');
      
      const data = await response.json();
      
      if (data.system_health !== undefined) {
        setSystemHealth(data.system_health);
      }
      
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      
      if (data.intent && onIntentChange) {
        onIntentChange(data.intent);
      }
    } catch (error) {
      console.error("Chat Error:", error);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Unable to process request.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = (e) => {
    e.preventDefault();
    sendQuery(input);
  };

  // Get the most recent assistant message for the Summary Card
  const latestAssistantMsg = [...messages].reverse().find(m => m.role === 'assistant')?.content || '';

  return (
    <div className="intelligence-dashboard" style={{ 
      display: 'flex', flexDirection: 'column', height: '100%', 
      background: 'rgba(12, 14, 22, 0.4)', borderRadius: 'var(--radius-lg)', 
      border: '1px solid var(--border-color)', overflow: 'hidden' 
    }}>
      
      {/* 1. Live Metrics Board */}
      <div style={{
        padding: '1.5rem',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        display: 'flex', gap: '1rem', background: 'rgba(0,0,0,0.2)'
      }}>
        <div style={{ flex: 1, background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-md)', padding: '1rem', border: '1px solid rgba(255,255,255,0.05)' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 600, letterSpacing: '0.5px' }}>
            <Users size={14} /> LIVE / TOTAL
          </div>
          <div style={{ fontSize: '1.6rem', fontFamily: '"Outfit", sans-serif', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'baseline', gap: '0.4rem' }}>
            {peopleCount || 0}
            <span style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>/ {totalPeople || 0}</span>
          </div>
        </div>

        <div style={{ flex: 1, background: 'rgba(255,255,255,0.03)', borderRadius: 'var(--radius-md)', padding: '1rem', border: '1px solid rgba(255,255,255,0.05)' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 600, letterSpacing: '0.5px' }}>
            <Activity size={14} /> ACTIVITY HEAT
          </div>
          <div style={{ 
            fontSize: '1.2rem', fontFamily: '"Outfit", sans-serif', fontWeight: 600,
            color: activityLevel === 'High' ? 'var(--danger)' : activityLevel === 'Medium' ? 'var(--warning)' : 'var(--success)',
            marginTop: '0.6rem'
          }}>
            {activityLevel}
          </div>
        </div>
      </div>

      {/* Health Banner */}
      {systemHealth < 1.0 && (
        <div style={{
          background: 'rgba(245, 158, 11, 0.1)', borderBottom: '1px solid rgba(245, 158, 11, 0.2)',
          color: 'var(--warning)', padding: '0.5rem 1.5rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem'
        }}>
          <Bug size={14} />
          <strong>System Degraded:</strong> Partial connection. (Health: {Math.round(systemHealth * 100)}%)
        </div>
      )}

      {/* 2. AI Summary Card (Replaces Chat History) */}
      <div style={{ flex: 1, padding: '1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
        <div style={{ color: 'var(--text-accent)', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', fontWeight: 600, letterSpacing: '0.5px' }}>
          <Sparkles size={14} /> AI INSIGHT
        </div>
        
        <div style={{
          background: 'linear-gradient(145deg, rgba(56, 189, 248, 0.1) 0%, rgba(12, 14, 22, 0.4) 100%)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid rgba(56, 189, 248, 0.2)',
          padding: '1.5rem',
          boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
          minHeight: '150px'
        }}>
          {isLoading ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-accent)' }}>
              <span className="dot-pulse">Agent thinking...</span>
            </div>
          ) : (
            <div 
              className="assistant-html-content"
              style={{ color: '#e2e8f0', fontSize: '1rem', lineHeight: '1.6' }}
              dangerouslySetInnerHTML={{ __html: latestAssistantMsg }} 
            />
          )}
        </div>
        <div ref={messagesEndRef} />
      </div>

      {/* 3. Floating "Ask AI" Input */}
      <div style={{ padding: '1.5rem', background: 'linear-gradient(0deg, rgba(3,4,8,0.8) 0%, transparent 100%)' }}>
        <form onSubmit={handleSend} style={{ display: 'flex', gap: '0.5rem', position: 'relative' }}>
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask AI to investigate..."
            disabled={isLoading}
            style={{
              flex: 1,
              background: 'rgba(255, 255, 255, 0.08)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '30px',
              padding: '0.8rem 1.2rem',
              color: '#fff',
              outline: 'none',
              fontSize: '0.95rem',
              backdropFilter: 'blur(10px)',
              boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
            }}
          />
          <button type="submit" disabled={isLoading || !input.trim()} style={{
            background: 'var(--primary)',
            color: '#fff',
            border: 'none',
            borderRadius: '30px',
            padding: '0.8rem 1.2rem',
            cursor: (isLoading || !input.trim()) ? 'not-allowed' : 'pointer',
            opacity: (isLoading || !input.trim()) ? 0.6 : 1,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 4px 15px rgba(56, 189, 248, 0.4)'
          }}>
            <Send size={18} />
          </button>
        </form>
      </div>

    </div>
  );
};

export default ChatPanel;
