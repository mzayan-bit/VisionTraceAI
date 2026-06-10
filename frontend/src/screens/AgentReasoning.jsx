import React, { useState, useRef } from 'react';
import { GitBranch, Database, FileCode, CheckCircle2, Search, BrainCircuit, Maximize } from 'lucide-react';
import { motion, useMotionValue, useTransform } from 'framer-motion';

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

export default function AgentReasoning() {
  const [zoom, setZoom] = useState(1);
  const containerRef = useRef(null);

  // Pan state using Framer Motion
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

  return (
    <div style={{ display: 'flex', height: '100%', gap: '24px' }}>
      
      {/* ── Main Graph Viewport ─────────────────────────────────── */}
      <div 
        className="glass-panel" 
        style={{ 
          flex: 1, 
          position: 'relative', 
          overflow: 'hidden',
          background: '#030303',
          cursor: 'grab'
        }}
        onWheel={handleWheel}
      >
        {/* Grid Background */}
        <div style={{
          position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
          backgroundImage: 'radial-gradient(rgba(255,255,255,0.1) 1px, transparent 1px)',
          backgroundSize: '30px 30px',
          opacity: 0.5,
          pointerEvents: 'none'
        }} />

        {/* Toolbar */}
        <div style={{ position: 'absolute', top: 20, left: 20, zIndex: 10, display: 'flex', gap: '12px' }}>
          <div style={{ padding: '8px 16px', background: 'rgba(0,0,0,0.6)', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px', backdropFilter: 'blur(4px)' }}>
            <GitBranch size={16} color="var(--primary)" /> Agent Reasoning Flow
          </div>
          <div style={{ padding: '8px 16px', background: 'rgba(0,0,0,0.6)', border: '1px solid var(--border-color)', borderRadius: '6px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '8px', backdropFilter: 'blur(4px)' }}>
            <Maximize size={14} /> Zoom: {Math.round(zoom * 100)}%
          </div>
        </div>

        {/* Draggable Canvas */}
        <motion.div
          drag
          dragConstraints={containerRef}
          style={{ x, y, width: '100%', height: '100%', scale: zoom, transformOrigin: 'top left' }}
        >
          {/* Edges (SVG) */}
          <svg style={{ position: 'absolute', top: 0, left: 0, width: '2000px', height: '2000px', pointerEvents: 'none' }}>
            <defs>
              <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="var(--primary)" />
              </marker>
            </defs>
            {GRAPH_EDGES.map((edge, i) => {
              const fromNode = GRAPH_NODES.find(n => n.id === edge.from);
              const toNode = GRAPH_NODES.find(n => n.id === edge.to);
              // Calculate simple bezier curve connecting centers
              const pathStr = `M ${fromNode.x + 200} ${fromNode.y + 40} C ${fromNode.x + 250} ${fromNode.y + 40}, ${toNode.x - 50} ${toNode.y + 40}, ${toNode.x} ${toNode.y + 40}`;
              return (
                <motion.path 
                  key={i} 
                  d={pathStr} 
                  stroke="var(--primary)" 
                  strokeWidth="2" 
                  fill="none" 
                  opacity="0.5"
                  markerEnd="url(#arrowhead)"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 1.5, delay: i * 0.5 }}
                />
              );
            })}
          </svg>

          {/* Nodes */}
          {GRAPH_NODES.map(node => (
            <motion.div
              key={node.id}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              style={{
                position: 'absolute',
                left: node.x, top: node.y,
                width: 200, padding: '16px',
                background: node.status === 'active' ? 'rgba(56, 189, 248, 0.1)' : 'var(--bg-surface)',
                border: `1px solid ${node.status === 'active' ? 'var(--primary)' : 'var(--border-color)'}`,
                borderRadius: '8px',
                color: '#fff',
                boxShadow: node.status === 'active' ? '0 0 20px rgba(56, 189, 248, 0.2)' : 'none',
                cursor: 'pointer'
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

      {/* ── Vector Memory Context Sidebar ──────────────────────── */}
      <div style={{ width: '320px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div className="glass-panel" style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ margin: '0 0 16px 0', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1.1rem' }}>
            <Database size={18} color="var(--primary)" /> Memory Diagnostics
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '24px' }}>
            Real-time inspection of visual embedding vectors and cached scene states.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto' }}>
            {[
              { dim: '512-d', type: 'SigLIP Embedding', match: '98%', id: 'idx_992a4' },
              { dim: '256-d', type: 'CLIP Context', match: '84%', id: 'idx_81bc2' },
              { dim: 'JSON', type: 'Redis Timeline', match: 'exact', id: 'key_scene_log' }
            ].map(mem => (
              <div key={mem.id} style={{ padding: '12px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--primary)', fontFamily: 'var(--font-mono)' }}>{mem.dim}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--success)' }}>{mem.match}</span>
                </div>
                <div style={{ color: '#fff', fontSize: '0.9rem', fontWeight: 500 }}>{mem.type}</div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>UUID: {mem.id}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

    </div>
  );
}
