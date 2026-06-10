import React, { useState, useEffect, useRef } from 'react';
import { Cpu, Database, Activity, Terminal, GitBranch, Search, BrainCircuit, CheckCircle2, FileCode, Maximize, MessageSquare } from 'lucide-react';
import AgentChatInterface from '../components/AgentChatInterface';
import { motion, useMotionValue } from 'framer-motion';

const GRAPH_NODES = [
  { id: 'n1', type: 'input', label: 'Query Parsing Engine', status: 'done', x: 50, y: 150 },
  { id: 'n2', type: 'memory', label: 'Check Redis Timelines', status: 'done', x: 300, y: 50 },
  { id: 'n3', type: 'vector', label: 'Qdrant Vector Match', status: 'active', x: 300, y: 250 },
  { id: 'n4', type: 'synth', label: 'Synthesize Context', status: 'pending', x: 550, y: 150 },
];

const GRAPH_EDGES = [
  { from: 'n1', to: 'n2' },
  { from: 'n1', to: 'n3' },
  { from: 'n2', to: 'n4' },
  { from: 'n3', to: 'n4' },
];

export default function AgentCommandCenter({ 
  latestFrame, 
  totalPeople, 
  runtimePeople,
  onTargetSelect 
}) {
  const [activeTab, setActiveTab] = useState('chat');
  const [healthData, setHealthData] = useState(null);
  const [logs, setLogs] = useState([]);
  const logsEndRef = useRef(null);

  // Pan state using Framer Motion
  const [zoom, setZoom] = useState(1);
  const containerRef = useRef(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const handleWheel = (e) => {
    e.preventDefault();
    if (e.deltaY > 0) {
      setZoom(z => Math.max(z - 0.1, 0.5));
    } else {
      setZoom(z => Math.min(z + 0.1, 2));
    }
  };

  const getNodeIcon = (type) => {
    switch(type) {
      case 'input': return <FileCode size={20} />;
      case 'memory': return <Database size={20} />;
      case 'vector': return <Search size={20} />;
      case 'synth': return <BrainCircuit size={20} />;
      default: return <GitBranch size={20} />;
    }
  };

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
        justifyContent: 'space-between',
        gap: '16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
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

        {/* ── Tabs ── */}
        <div style={{ display: 'flex', gap: '8px', background: 'rgba(0,0,0,0.5)', padding: '6px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          {[
            { id: 'chat', label: 'Chat Interface', icon: MessageSquare },
            { id: 'reasoning', label: 'Reasoning Graph', icon: GitBranch },
            { id: 'memory', label: 'Memory Logs', icon: Database },
          ].map(t => {
            const Icon = t.icon;
            const isActive = activeTab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                style={{
                  background: isActive ? 'var(--primary-subtle)' : 'transparent',
                  color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '8px',
                  display: 'flex', alignItems: 'center', gap: '8px',
                  cursor: 'pointer',
                  fontWeight: isActive ? 600 : 500,
                  transition: 'all var(--transition-fast)'
                }}
              >
                <Icon size={16} /> {t.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Main Layout ─────────────────────────────────────────── */}
      <div style={{ display: 'flex', flex: 1, gap: '20px', minHeight: 0 }}>
        
        {/* Left Column: Telemetry & Logs (Always visible) */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '20px', minWidth: 0, maxWidth: '400px' }}>
          
          {/* Telemetry Cards */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Pipeline Performance */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-accent)', marginBottom: '16px', fontSize: '0.85rem', fontWeight: 600, letterSpacing: '1px' }}>
                <Activity size={16} /> PIPELINE PERFORMANCE
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                <div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '4px' }}>Processing FPS</div>
                  <div style={{ fontSize: '1.5rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {healthData?.metrics?.system_fps || 0}
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '4px' }}>Latency</div>
                  <div style={{ fontSize: '1.5rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: (healthData?.metrics?.pipeline_latency_ms > 200) ? 'var(--warning)' : 'var(--success)' }}>
                    {healthData?.metrics?.pipeline_latency_ms || 0} <span style={{ fontSize: '1rem' }}>ms</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Global Scene Memory */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--success)', marginBottom: '16px', fontSize: '0.85rem', fontWeight: 600, letterSpacing: '1px' }}>
                <Database size={16} /> GLOBAL SCENE MEMORY
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
                <div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '4px' }}>Semantic Vectors</div>
                  <div style={{ fontSize: '1.5rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {healthData?.metrics?.qdrant_total_vectors || 0}
                  </div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '4px' }}>Temporal Logs</div>
                  <div style={{ fontSize: '1.5rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>
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

        {/* Right Column: Tab Content */}
        <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          
          {activeTab === 'chat' && (
            <AgentChatInterface onTargetSelect={onTargetSelect} />
          )}

          {activeTab === 'reasoning' && (
            <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden', background: '#030303', cursor: 'grab' }} onWheel={handleWheel}>
              <div style={{
                position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
                backgroundImage: 'radial-gradient(rgba(255,255,255,0.1) 1px, transparent 1px)',
                backgroundSize: '30px 30px', opacity: 0.5, pointerEvents: 'none'
              }} />
              <div style={{ position: 'absolute', top: 20, left: 20, zIndex: 10, display: 'flex', gap: '12px' }}>
                <div style={{ padding: '8px 16px', background: 'rgba(0,0,0,0.6)', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px', backdropFilter: 'blur(4px)' }}>
                  <GitBranch size={16} color="var(--primary)" /> Agent Reasoning Flow
                </div>
                <div style={{ padding: '8px 16px', background: 'rgba(0,0,0,0.6)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '8px', backdropFilter: 'blur(4px)' }}>
                  <Maximize size={14} /> Zoom: {Math.round(zoom * 100)}%
                </div>
              </div>
              <motion.div drag dragConstraints={containerRef} style={{ x, y, width: '100%', height: '100%', scale: zoom, transformOrigin: 'top left' }}>
                <svg style={{ position: 'absolute', top: 0, left: 0, width: '2000px', height: '2000px', pointerEvents: 'none' }}>
                  <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                      <polygon points="0 0, 10 3.5, 0 7" fill="var(--primary)" />
                    </marker>
                  </defs>
                  {GRAPH_EDGES.map((edge, i) => {
                    const fromNode = GRAPH_NODES.find(n => n.id === edge.from);
                    const toNode = GRAPH_NODES.find(n => n.id === edge.to);
                    const pathStr = `M ${fromNode.x + 200} ${fromNode.y + 40} C ${fromNode.x + 250} ${fromNode.y + 40}, ${toNode.x - 50} ${toNode.y + 40}, ${toNode.x} ${toNode.y + 40}`;
                    return <motion.path key={i} d={pathStr} stroke="var(--primary)" strokeWidth="2" fill="none" opacity="0.5" markerEnd="url(#arrowhead)" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.5, delay: i * 0.5 }} />;
                  })}
                </svg>
                {GRAPH_NODES.map(node => (
                  <motion.div
                    key={node.id}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    style={{
                      position: 'absolute', left: node.x, top: node.y, width: 200, padding: '16px',
                      background: node.status === 'active' ? 'rgba(56, 189, 248, 0.1)' : 'var(--bg-surface)',
                      border: `1px solid ${node.status === 'active' ? 'var(--primary)' : 'var(--border-color)'}`,
                      borderRadius: '8px', color: '#fff',
                      boxShadow: node.status === 'active' ? '0 0 20px rgba(56, 189, 248, 0.2)' : 'none', cursor: 'pointer'
                    }}
                    whileHover={{ scale: 1.05 }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <div style={{ width: 32, height: 32, borderRadius: '6px', background: 'var(--primary-subtle)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {getNodeIcon(node.type)}
                      </div>
                      {node.status === 'done' && <CheckCircle2 size={16} color="var(--success)" />}
                      {node.status === 'active' && <motion.div animate={{ opacity: [1, 0.5, 1] }} transition={{ repeat: Infinity }} style={{ width: 10, height: 10, borderRadius: '50%', background: 'var(--primary)', boxShadow: '0 0 10px var(--primary)' }} />}
                      {node.status === 'pending' && <div style={{ width: 10, height: 10, borderRadius: '50%', border: '2px solid var(--text-muted)' }} />}
                    </div>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: '0.9rem', fontWeight: 600 }}>{node.label}</div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '4px', textTransform: 'uppercase' }}>Status: {node.status}</div>
                  </motion.div>
                ))}
              </motion.div>
            </div>
          )}

          {activeTab === 'memory' && (
            <div style={{ padding: '32px', height: '100%', overflowY: 'auto' }}>
              <h3 style={{ margin: '0 0 16px 0', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1.2rem' }}>
                <Database size={20} color="var(--primary)" /> Vector Memory Diagnostics
              </h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '32px' }}>
                Real-time inspection of visual embedding vectors and cached scene states.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
                {[
                  { dim: '512-d', type: 'SigLIP Embedding', match: '98%', id: 'idx_992a4', detail: 'Identified Red Jacket' },
                  { dim: '256-d', type: 'CLIP Context', match: '84%', id: 'idx_81bc2', detail: 'General scene activity' },
                  { dim: 'JSON', type: 'Redis Timeline', match: 'exact', id: 'key_scene_log', detail: 'Cache hit for recent history' },
                  { dim: '768-d', type: 'YOLO-Pose Layout', match: '91%', id: 'idx_771f9', detail: 'Skeletal geometry match' },
                ].map(mem => (
                  <div key={mem.id} style={{ padding: '20px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--primary)', fontFamily: 'var(--font-mono)' }}>{mem.dim}</span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--success)', fontWeight: 600 }}>{mem.match} MATCH</span>
                    </div>
                    <div style={{ color: '#fff', fontSize: '1.1rem', fontWeight: 600, marginBottom: '4px' }}>{mem.type}</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '16px' }}>{mem.detail}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)', padding: '8px', background: 'rgba(0,0,0,0.5)', borderRadius: '4px' }}>UUID: {mem.id}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
