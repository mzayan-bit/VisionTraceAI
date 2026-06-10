import React, { useState, useEffect, useRef } from 'react';
import { X, Cpu, Database, Server, Activity, Terminal } from 'lucide-react';
import ChatPanel from './ChatPanel';

const AgentDashboard = ({ onClose, latestFrame, totalPeople, runtimePeople }) => {
  const [healthData, setHealthData] = useState(null);
  const [logs, setLogs] = useState([]);
  const logsEndRef = useRef(null);

  // Poll system health every 2 seconds
  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/metrics');
        if (response.ok) {
          const data = await response.json();
          setHealthData(data);
          
          // Add a log entry for telemetry
          const timeStr = new Date().toLocaleTimeString();
          setLogs(prev => {
            const newLogs = [...prev, `[${timeStr}] SYSTEM METRICS: FPS=${data.metrics.system_fps}, Latency=${data.metrics.pipeline_latency_ms}ms, Vectors=${data.metrics.qdrant_total_vectors}`];
            return newLogs.length > 50 ? newLogs.slice(-50) : newLogs;
          });
        }
      } catch (error) {
        console.error("Failed to fetch health data", error);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 2000);
    return () => clearInterval(interval);
  }, []);

  // Listen to WebSocket agent events for logs
  useEffect(() => {
    const handleAgentLog = (e) => {
      const timeStr = new Date().toLocaleTimeString();
      setLogs(prev => {
        const newLogs = [...prev, `[${timeStr}] AGENT ACTION: ${e.detail}`];
        return newLogs.length > 50 ? newLogs.slice(-50) : newLogs;
      });
    };
    window.addEventListener('ai-log', handleAgentLog);
    return () => window.removeEventListener('ai-log', handleAgentLog);
  }, []);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(5, 6, 10, 0.95)',
      backdropFilter: 'blur(20px)',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column',
      color: '#fff',
      animation: 'fade-in 0.3s ease-out'
    }}>
      {/* Header */}
      <div style={{
        padding: '1.5rem 2rem',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'linear-gradient(90deg, rgba(139, 92, 246, 0.1) 0%, transparent 100%)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            background: 'linear-gradient(135deg, #8b5cf6, #ec4899)',
            padding: '0.6rem',
            borderRadius: '12px',
            boxShadow: '0 0 20px rgba(236, 72, 153, 0.4)'
          }}>
            <Cpu size={24} color="#fff" />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.5rem', fontFamily: '"Outfit", sans-serif', fontWeight: 600, letterSpacing: '1px' }}>Agent Command Center</h2>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.2rem' }}>Advanced System Telemetry & Logic Tracking</div>
          </div>
        </div>
        <button 
          onClick={onClose}
          style={{
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.1)',
            color: '#fff',
            width: '40px', height: '40px',
            borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
          onMouseOver={e => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
          onMouseOut={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
        >
          <X size={20} />
        </button>
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden', padding: '1.5rem', gap: '1.5rem' }}>
        
        {/* Left Column: Stats & Logs */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Telemetry Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '16px', padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#38bdf8', marginBottom: '1rem', fontSize: '0.9rem', fontWeight: 600 }}>
                <Activity size={18} /> PIPELINE PERFORMANCE
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                <div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '0.2rem' }}>Processing FPS</div>
                  <div style={{ fontSize: '1.8rem', fontFamily: '"Outfit", sans-serif', fontWeight: 600 }}>{healthData?.metrics?.system_fps || 0}</div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '0.2rem' }}>Latency</div>
                  <div style={{ fontSize: '1.8rem', fontFamily: '"Outfit", sans-serif', fontWeight: 600, color: (healthData?.metrics?.pipeline_latency_ms > 200) ? 'var(--warning)' : 'var(--success)' }}>
                    {healthData?.metrics?.pipeline_latency_ms || 0} <span style={{ fontSize: '1rem' }}>ms</span>
                  </div>
                </div>
              </div>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '16px', padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#10b981', marginBottom: '1rem', fontSize: '0.9rem', fontWeight: 600 }}>
                <Database size={18} /> GLOBAL SCENE MEMORY
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                <div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '0.2rem' }}>Semantic Vectors (Qdrant)</div>
                  <div style={{ fontSize: '1.8rem', fontFamily: '"Outfit", sans-serif', fontWeight: 600 }}>{healthData?.metrics?.qdrant_total_vectors || 0}</div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '0.2rem' }}>Temporal Logs (Redis)</div>
                  <div style={{ fontSize: '1.8rem', fontFamily: '"Outfit", sans-serif', fontWeight: 600 }}>{healthData?.metrics?.redis_total_keys || 0}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Process Logs Terminal */}
          <div style={{ 
            flex: 1, 
            background: '#050505', 
            border: '1px solid rgba(255,255,255,0.1)', 
            borderRadius: '16px', 
            display: 'flex', 
            flexDirection: 'column',
            overflow: 'hidden'
          }}>
            <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255,255,255,0.02)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <Terminal size={14} /> SYSTEM TRACE LOGS
            </div>
            <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', fontFamily: '"Fira Code", monospace', fontSize: '0.85rem', lineHeight: 1.6, color: '#a1a1aa' }}>
              {logs.map((log, i) => (
                <div key={i} style={{ marginBottom: '0.5rem' }}>
                  <span style={{ color: '#3b82f6' }}>{log.split('] ')[0]}]</span> 
                  <span style={{ color: log.includes('AGENT ACTION') ? '#d946ef' : '#e2e8f0', marginLeft: '0.5rem' }}>
                    {log.split('] ')[1]}
                  </span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>

        </div>

        {/* Right Column: Embedded Chat Interface */}
        <div style={{ width: '450px', display: 'flex', flexDirection: 'column' }}>
          <ChatPanel 
            peopleCount={runtimePeople} 
            totalPeople={totalPeople}
            activityLevel={runtimePeople >= 4 ? 'High' : runtimePeople >= 2 ? 'Medium' : 'Low'}
          />
        </div>

      </div>
    </div>
  );
};

export default AgentDashboard;
