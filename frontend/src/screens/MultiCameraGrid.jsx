import React, { useState } from 'react';
import { LayoutGrid, Grid3x3, Grid, Layers, PlaySquare } from 'lucide-react';
import MinimalVideoNode from '../components/MinimalVideoNode';

const GRID_MODES = [
  { id: '2x2', icon: LayoutGrid, count: 4, cols: 2 },
  { id: '3x3', icon: Grid3x3, count: 9, cols: 3 },
  { id: '4x4', icon: Grid, count: 16, cols: 4 },
  { id: '8x8', icon: Layers, count: 64, cols: 8 },
];

export default function MultiCameraGrid() {
  const [activeMode, setActiveMode] = useState(GRID_MODES[0]);
  const [fullscreenNode, setFullscreenNode] = useState(null);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '20px' }}>
      
      {/* ── Header Controls ────────────────────────────────────── */}
      <div className="glass-panel" style={{ 
        display: 'flex', justifyContent: 'space-between', alignItems: 'center', 
        padding: '12px 24px', flexShrink: 0 
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: 36, height: 36, background: 'var(--primary-subtle)', color: 'var(--primary)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <LayoutGrid size={18} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.2rem', fontFamily: 'var(--font-display)', fontWeight: 600, color: 'var(--text-primary)' }}>
              Multi-Stream Matrix
            </h2>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', background: 'rgba(0,0,0,0.2)', padding: '6px', borderRadius: 'var(--radius-md)' }}>
          {GRID_MODES.map(mode => {
            const Icon = mode.icon;
            const isActive = activeMode.id === mode.id;
            return (
              <button
                key={mode.id}
                onClick={() => { setActiveMode(mode); setFullscreenNode(null); }}
                style={{
                  background: isActive ? 'var(--primary)' : 'transparent',
                  color: isActive ? '#fff' : 'var(--text-secondary)',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '6px',
                  display: 'flex', alignItems: 'center', gap: '8px',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  transition: 'all var(--transition-fast)'
                }}
              >
                <Icon size={16} /> {mode.id}
              </button>
            );
          })}
          
          <div style={{ width: 1, background: 'var(--border-color)', margin: '0 8px' }} />
          
          <button style={{
            background: 'rgba(255,255,255,0.05)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-color)',
            padding: '8px 16px',
            borderRadius: '6px',
            display: 'flex', alignItems: 'center', gap: '8px',
            cursor: 'pointer',
            fontFamily: 'var(--font-body)',
            fontSize: '0.8rem',
            fontWeight: 500,
          }}>
            <PlaySquare size={16} /> Sync Timelines
          </button>
        </div>
      </div>

      {/* ── CSS Grid Engine ────────────────────────────────────── */}
      <div style={{ 
        flex: 1, 
        overflow: 'hidden',
        position: 'relative',
        background: '#000',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-color)'
      }}>
        {fullscreenNode ? (
          <div style={{ width: '100%', height: '100%' }}>
            <MinimalVideoNode 
              cameraId={fullscreenNode} 
              title={`CAM_${String(fullscreenNode + 1).padStart(3, '0')}`}
              onClickFullscreen={() => setFullscreenNode(null)}
            />
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${activeMode.cols}, 1fr)`,
            gridTemplateRows: `repeat(${activeMode.cols}, 1fr)`,
            gap: '2px',
            width: '100%',
            height: '100%',
            background: 'var(--border-color)', // acts as grid lines
          }}>
            {Array.from({ length: activeMode.count }).map((_, i) => (
              <MinimalVideoNode 
                key={i} 
                cameraId={i} 
                title={`CAM_${String(i + 1).padStart(3, '0')}`}
                onClickFullscreen={() => setFullscreenNode(i)}
              />
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
