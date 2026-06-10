import React, { useState } from 'react';
import { Map as MapIcon, Globe, Crosshair } from 'lucide-react';
import { motion } from 'framer-motion';

// Mock Camera Nodes for the map
const MAP_NODES = [
  { id: 1, x: 20, y: 30, status: 'LIVE', angle: 45, type: 'Dome' },
  { id: 2, x: 75, y: 15, status: 'WARNING', angle: 180, type: 'PTZ' },
  { id: 3, x: 85, y: 70, status: 'LIVE', angle: -45, type: 'Bullet' },
  { id: 4, x: 30, y: 80, status: 'OFFLINE', angle: 90, type: 'Dome' },
];

// Mock Trajectories for targets
const TARGET_TRAJECTORIES = [
  { id: 'T_101', path: [{x: 10, y: 50}, {x: 40, y: 50}, {x: 60, y: 20}], color: '#38bdf8' },
  { id: 'T_102', path: [{x: 90, y: 80}, {x: 70, y: 60}, {x: 50, y: 60}], color: '#f59e0b' },
];

export default function SpatialMapViewer({ mode = 'building' }) {
  const [hoveredNode, setHoveredNode] = useState(null);

  const title = mode === 'building' ? 'Building Digital Twin' : 'Geographic Overview';
  const Icon = mode === 'building' ? MapIcon : Globe;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '20px' }}>
      
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="glass-panel" style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', gap: '16px', flexShrink: 0 }}>
        <div style={{ width: 40, height: 40, background: 'var(--primary-subtle)', color: 'var(--primary)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Icon size={20} />
        </div>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.2rem', fontFamily: 'var(--font-display)', fontWeight: 600, color: 'var(--text-primary)' }}>
            {title}
          </h2>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
            Spatial mapping engine active. Tracking {TARGET_TRAJECTORIES.length} live vectors across {MAP_NODES.length} nodes.
          </div>
        </div>
      </div>

      {/* ── Map Canvas Container ───────────────────────────────── */}
      <div className="glass-panel" style={{ flex: 1, position: 'relative', overflow: 'hidden', background: '#050505', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        
        {/* Placeholder SVG Blueprint/Map */}
        <div style={{ position: 'relative', width: '80%', height: '80%', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px' }}>
          
          <svg width="100%" height="100%" style={{ position: 'absolute', top: 0, left: 0 }}>
            {/* Grid Lines */}
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="1"/>
            </pattern>
            <rect width="100%" height="100%" fill="url(#grid)" />

            {/* Mock Floorplan outlines */}
            {mode === 'building' && (
              <g stroke="var(--primary)" strokeWidth="2" fill="rgba(56, 189, 248, 0.05)" opacity="0.6">
                <rect x="10%" y="10%" width="30%" height="40%" />
                <rect x="45%" y="10%" width="45%" height="30%" />
                <rect x="20%" y="60%" width="60%" height="30%" />
                <path d="M 40% 50% L 45% 50% L 45% 60% L 40% 60% Z" fill="var(--primary)" opacity="0.2" /> {/* Doorway connector */}
              </g>
            )}

            {/* Trajectory Animations */}
            {TARGET_TRAJECTORIES.map((track, idx) => (
              <g key={idx}>
                {/* Trail Line */}
                <polyline 
                  points={track.path.map(p => `${p.x}%,${p.y}%`).join(' ')} 
                  fill="none" stroke={track.color} strokeWidth="2" strokeDasharray="4 4" opacity="0.5" 
                />
                {/* Moving Dot */}
                <motion.circle
                  r="4"
                  fill={track.color}
                  initial={{ cx: `${track.path[0].x}%`, cy: `${track.path[0].y}%` }}
                  animate={{ 
                    cx: track.path.map(p => `${p.x}%`), 
                    cy: track.path.map(p => `${p.y}%`) 
                  }}
                  transition={{ duration: 10, repeat: Infinity, ease: 'linear' }}
                />
              </g>
            ))}
          </svg>

          {/* Camera Nodes */}
          {MAP_NODES.map(node => {
            const isHovered = hoveredNode === node.id;
            const statusColor = node.status === 'LIVE' ? 'var(--success)' : (node.status === 'WARNING' ? 'var(--warning)' : 'var(--danger)');

            return (
              <div 
                key={node.id}
                style={{ position: 'absolute', left: `${node.x}%`, top: `${node.y}%` }}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
              >
                {/* View Cone (appears on hover) */}
                <AnimatePresence>
                  {isHovered && node.status !== 'OFFLINE' && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0 }}
                      animate={{ opacity: 0.15, scale: 1 }}
                      exit={{ opacity: 0, scale: 0 }}
                      style={{
                        position: 'absolute',
                        left: 0, top: 0,
                        width: '150px', height: '150px',
                        background: `radial-gradient(circle at 0 0, ${statusColor} 0%, transparent 70%)`,
                        transformOrigin: '0 0',
                        transform: `rotate(${node.angle}deg)`,
                        pointerEvents: 'none'
                      }}
                    />
                  )}
                </AnimatePresence>

                {/* Camera Marker */}
                <div style={{
                  position: 'absolute',
                  transform: 'translate(-50%, -50%)',
                  width: 14, height: 14,
                  borderRadius: '50%',
                  background: statusColor,
                  border: '2px solid #000',
                  cursor: 'pointer',
                  boxShadow: `0 0 10px ${statusColor}`,
                  zIndex: 10
                }} />

                {/* Tooltip */}
                <AnimatePresence>
                  {isHovered && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 10 }}
                      style={{
                        position: 'absolute',
                        bottom: '20px', left: '50%',
                        transform: 'translateX(-50%)',
                        background: 'rgba(0,0,0,0.8)',
                        backdropFilter: 'blur(4px)',
                        border: '1px solid var(--border-color)',
                        padding: '8px 12px',
                        borderRadius: '6px',
                        color: '#fff',
                        whiteSpace: 'nowrap',
                        zIndex: 20,
                        pointerEvents: 'none'
                      }}
                    >
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>CAM_{String(node.id).padStart(3, '0')}</div>
                      <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>{node.type} | {node.status}</div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}

        </div>

        {/* Floating Map Controls */}
        <div style={{ position: 'absolute', bottom: 20, right: 20, display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button style={{ width: 36, height: 36, background: 'rgba(255,255,255,0.1)', border: '1px solid var(--border-color)', color: '#fff', borderRadius: '6px', cursor: 'pointer' }}>+</button>
          <button style={{ width: 36, height: 36, background: 'rgba(255,255,255,0.1)', border: '1px solid var(--border-color)', color: '#fff', borderRadius: '6px', cursor: 'pointer' }}>-</button>
          <button style={{ width: 36, height: 36, background: 'var(--primary-subtle)', border: '1px solid var(--primary)', color: 'var(--primary)', borderRadius: '6px', cursor: 'pointer', marginTop: '8px' }}>
            <Crosshair size={16} style={{ margin: 'auto' }} />
          </button>
        </div>

      </div>

    </div>
  );
}
