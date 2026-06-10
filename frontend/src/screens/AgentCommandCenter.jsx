import React, { useState, useEffect, useRef } from 'react';
import { Cpu, Database, Activity, Terminal } from 'lucide-react';
import AgentChatInterface from '../components/AgentChatInterface';

export default function AgentCommandCenter({ 
  latestFrame, 
  totalPeople, 
  runtimePeople,
  onTargetSelect 
}) {
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
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* ── Header ──────────────────────────────────────────────── */}
      <div className="glass-panel" style={{
        padding: '20px',
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
      }}>
        <div style={{
          width: 48, height: 48, borderRadius: 'var(--radius-md)',
          background: 'var(--primary-subtle)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--primary)',
          boxShadow: 'var(--shadow-glow)'
        }}>
          <Cpu size={24} />
        </div>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.5rem', fontFamily: 'var(--font-display)', fontWeight: 600, color: 'var(--text-primary)' }}>
            Agent Command Center
          </h2>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
            Advanced System Telemetry & Logic Tracking
          </div>
        </div>
      </div>

      {/* ── Main Layout ─────────────────────────────────────────── */}
      <div style={{ display: 'flex', flex: 1, gap: '20px', minHeight: 0 }}>
        
        {/* Left Column: Telemetry & Logs */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '20px', minWidth: 0 }}>
          
          {/* Telemetry Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px' }}>
            {/* Pipeline Performance */}
            <div className="glass-panel hover-lift" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-accent)', marginBottom: '16px', fontSize: '0.85rem', fontWeight: 600, letterSpacing: '1px' }}>
                <Activity size={16} /> PIPELINE PERFORMANCE
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                <div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '4px' }}>Processing FPS</div>
                  <div style={{ fontSize: '2rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {healthData?.metrics?.system_fps || 0}
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '4px' }}>Latency</div>
                  <div style={{ fontSize: '2rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: (healthData?.metrics?.pipeline_latency_ms > 200) ? 'var(--warning)' : 'var(--success)' }}>
                    {healthData?.metrics?.pipeline_latency_ms || 0} <span style={{ fontSize: '1rem' }}>ms</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Global Scene Memory */}
            <div className="glass-panel hover-lift" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--success)', marginBottom: '16px', fontSize: '0.85rem', fontWeight: 600, letterSpacing: '1px' }}>
                <Database size={16} /> GLOBAL SCENE MEMORY
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                <div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '4px' }}>Semantic Vectors</div>
                  <div style={{ fontSize: '2rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {healthData?.metrics?.qdrant_total_vectors || 0}
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '4px' }}>Temporal Logs</div>
                  <div style={{ fontSize: '2rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {healthData?.metrics?.redis_total_keys || 0}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Process Logs Terminal */}
          <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <div style={{ 
              padding: '16px 20px', 
              borderBottom: '1px solid var(--border-color)', 
              display: 'flex', alignItems: 'center', gap: '8px', 
              background: 'var(--bg-surface-hover)', 
              fontSize: '0.85rem', color: 'var(--text-secondary)',
              borderTopLeftRadius: 'var(--radius-lg)',
              borderTopRightRadius: 'var(--radius-lg)'
            }}>
              <Terminal size={14} /> SYSTEM TRACE LOGS
            </div>
            <div style={{ 
              flex: 1, overflowY: 'auto', padding: '20px', 
              fontFamily: 'var(--font-mono)', fontSize: '0.85rem', lineHeight: 1.6, 
              color: 'var(--text-muted)' 
            }}>
              {logs.map((log, i) => (
                <div key={i} style={{ marginBottom: '8px' }}>
                  <span style={{ color: 'var(--text-accent)' }}>{log.split('] ')[0]}]</span> 
                  <span style={{ color: log.includes('AGENT ACTION') ? 'var(--primary)' : 'var(--text-primary)', marginLeft: '8px' }}>
                    {log.split('] ')[1]}
                  </span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>

        </div>

        {/* Right Column: Chat Interface */}
        <div className="glass-panel" style={{ width: '450px', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <AgentChatInterface onTargetSelect={onTargetSelect} />
        </div>

      </div>
    </div>
  );
}
