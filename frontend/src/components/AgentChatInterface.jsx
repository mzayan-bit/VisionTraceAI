import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, Sparkles, User, Crosshair, ChevronDown, Mic } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import TypewriterMarkdown from './TypewriterMarkdown';

const COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4',
];

export default function AgentChatInterface({ onIntentChange, onTargetSelect }) {
  const [messages, setMessages] = useState([
    { 
      role: 'assistant', 
      content: 'Agent operational. Ready for tactical analysis.',
      intent: null 
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

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

    // Send only text content in history
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
      
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: data.response,
        intent: data.intent 
      }]);
      
      if (data.intent && onIntentChange) {
        onIntentChange(data.intent);
      }
    } catch (error) {
      console.error("Chat Error:", error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'System Error: Unable to process request due to a network or backend failure.',
        intent: null
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = (e) => {
    e.preventDefault();
    sendQuery(input);
  };

  return (
    <div style={{ 
      display: 'flex', flexDirection: 'column', height: '100%',
      background: 'var(--bg-surface)', borderLeft: '1px solid var(--border-color)'
    }}>
      
      {/* ── Chat Stream Area ────────────────────────────────────── */}
      <div style={{ flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        {messages.map((msg, idx) => {
          const isUser = msg.role === 'user';
          
          return (
            <motion.div 
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: isUser ? 'flex-end' : 'flex-start',
                width: '100%'
              }}
            >
              {/* Message Header */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: '8px',
                marginBottom: '6px',
                color: 'var(--text-secondary)',
                fontSize: '0.75rem',
                fontWeight: 600,
                letterSpacing: '0.5px'
              }}>
                {isUser ? (
                  <>OPERATOR <User size={12} /></>
                ) : (
                  <><Bot size={12} style={{ color: 'var(--text-accent)' }} /> AGENT_ALPHA</>
                )}
              </div>

              {/* Message Bubble */}
              <div style={{
                background: isUser ? 'var(--primary-subtle)' : 'var(--bg-card)',
                border: isUser ? '1px solid var(--border-accent)' : '1px solid var(--border-color)',
                color: isUser ? '#fff' : 'var(--text-primary)',
                padding: '12px 16px',
                borderRadius: isUser ? '12px 2px 12px 12px' : '2px 12px 12px 12px',
                maxWidth: '90%',
                boxShadow: isUser ? 'var(--shadow-glow)' : 'var(--shadow-elevation-1)',
                fontFamily: 'var(--font-body)',
                fontSize: '0.95rem',
                lineHeight: 1.6
              }}>
                {isUser ? (
                  msg.content
                ) : (
                  <TypewriterMarkdown content={msg.content} />
                )}
              </div>

              {/* AI Reasoning Dropdown (Mock for now) */}
              {!isUser && idx > 0 && (
                <div style={{
                  marginTop: '6px',
                  display: 'flex', alignItems: 'center', gap: '4px',
                  color: 'var(--text-muted)',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-mono)'
                }}>
                  <ChevronDown size={12} /> View AI Reasoning Trace
                </div>
              )}

              {/* Evidence Card */}
              {!isUser && msg.intent && msg.intent.target_id !== undefined && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 1 }} // Appear after typing simulation
                  onClick={() => onTargetSelect(msg.intent.target_id)}
                  style={{
                    marginTop: '12px',
                    background: 'var(--bg-base)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    padding: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)',
                    width: '100%',
                    maxWidth: '300px'
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.borderColor = 'var(--text-accent)';
                    e.currentTarget.style.background = 'var(--bg-surface-hover)';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.borderColor = 'var(--border-color)';
                    e.currentTarget.style.background = 'var(--bg-base)';
                  }}
                >
                  <div style={{
                    width: 40, height: 40, borderRadius: '4px',
                    background: COLORS[msg.intent.target_id % COLORS.length],
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#fff', fontWeight: 700, fontFamily: 'var(--font-mono)'
                  }}>
                    {msg.intent.target_id}
                  </div>
                  <div>
                    <div style={{ 
                      color: 'var(--text-accent)', fontSize: '0.75rem', fontWeight: 700, 
                      display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '2px' 
                    }}>
                      <Crosshair size={10} /> TRACK IDENTIFIED
                    </div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
                      Confidence: 98%
                    </div>
                  </div>
                </motion.div>
              )}
            </motion.div>
          );
        })}

        {isLoading && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            color: 'var(--text-accent)', fontFamily: 'var(--font-mono)', fontSize: '0.8rem'
          }}>
            <Sparkles size={14} style={{ animation: 'pulse 1s infinite' }} /> 
            Processing logical graph...
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* ── Interactive Input Area ──────────────────────────────── */}
      <div style={{ 
        padding: '20px', 
        background: 'var(--bg-base)',
        borderTop: '1px solid var(--border-color)'
      }}>
        <form onSubmit={handleSend} style={{ display: 'flex', gap: '10px', position: 'relative' }}>
          
          <div style={{ position: 'relative', flex: 1 }}>
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Command the AI agent..."
              disabled={isLoading}
              style={{
                width: '100%',
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '14px 40px 14px 16px', // space for mic
                color: 'var(--text-primary)',
                outline: 'none',
                fontFamily: 'var(--font-body)',
                fontSize: '0.95rem',
                transition: 'all var(--transition-fast)'
              }}
              onFocus={(e) => e.target.style.borderColor = 'var(--text-accent)'}
              onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
            />
            
            {/* Voice Entry Microphone */}
            <button
              type="button"
              onClick={() => setIsRecording(!isRecording)}
              style={{
                position: 'absolute',
                right: '8px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'transparent',
                border: 'none',
                color: isRecording ? '#ef4444' : 'var(--text-muted)',
                cursor: 'pointer',
                padding: '6px',
                borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                animation: isRecording ? 'audio-wave 1s infinite alternate' : 'none',
                boxShadow: isRecording ? '0 0 10px rgba(239, 68, 68, 0.4)' : 'none',
              }}
            >
              <Mic size={18} />
            </button>
          </div>

          <button type="submit" disabled={isLoading || !input.trim()} style={{
            background: 'var(--primary)',
            color: '#fff',
            border: 'none',
            borderRadius: '8px',
            padding: '0 20px',
            cursor: (isLoading || !input.trim()) ? 'not-allowed' : 'pointer',
            opacity: (isLoading || !input.trim()) ? 0.6 : 1,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: 'var(--shadow-glow)',
            transition: 'all var(--transition-fast)'
          }}>
            <Send size={18} />
          </button>
        </form>

        <style dangerouslySetInnerHTML={{__html: `
          @keyframes audio-wave {
            0% { box-shadow: 0 0 0 0px rgba(239, 68, 68, 0.4); }
            100% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
          }
        `}} />
      </div>

    </div>
  );
}
