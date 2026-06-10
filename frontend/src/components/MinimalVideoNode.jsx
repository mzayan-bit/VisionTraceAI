import React, { useState } from 'react';
import { Maximize2, Lock, Unlock } from 'lucide-react';

export default function MinimalVideoNode({ 
  cameraId, 
  title, 
  status = 'LIVE', 
  fps = 30, 
  onClickFullscreen 
}) {
  const [isHovered, setIsHovered] = useState(false);
  const [isLocked, setIsLocked] = useState(false);

  // Determine color based on status
  const statusColor = status === 'OFFLINE' ? '#ef4444' : (status === 'WARNING' ? '#f59e0b' : '#10b981');

  return (
    <div 
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        backgroundColor: '#0a0a0a',
        border: `1px solid ${isHovered ? 'var(--primary)' : 'var(--border-color)'}`,
        borderRadius: 'var(--radius-sm)',
        overflow: 'hidden',
        transition: 'border-color var(--transition-fast)'
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* ── Mock Video Canvas ──────────────────────────────── */}
      <div style={{
        position: 'absolute',
        top: 0, left: 0, width: '100%', height: '100%',
        background: 'linear-gradient(45deg, #111 0%, #050505 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        {/* Animated noise pattern or grid to simulate a raw feed */}
        <div style={{
          width: '100%', height: '100%',
          backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
          backgroundSize: '20px 20px',
          opacity: 0.5
        }} />
      </div>

      {/* ── Top Meta Bar ───────────────────────────────────── */}
      <div style={{
        position: 'absolute',
        top: 0, left: 0, width: '100%',
        padding: '6px 8px',
        background: 'linear-gradient(to bottom, rgba(0,0,0,0.8), transparent)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        pointerEvents: 'none'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{
            width: 6, height: 6, borderRadius: '50%',
            background: statusColor,
            boxShadow: `0 0 8px ${statusColor}`
          }} />
          <span style={{ 
            fontFamily: 'var(--font-mono)', fontSize: '0.65rem', 
            fontWeight: 700, color: '#fff', letterSpacing: '0.5px' 
          }}>
            {title}
          </span>
        </div>
        <div style={{ 
          fontFamily: 'var(--font-mono)', fontSize: '0.65rem', 
          color: 'var(--text-muted)' 
        }}>
          {fps} FPS
        </div>
      </div>

      {/* ── Hover Controls ─────────────────────────────────── */}
      <div style={{
        position: 'absolute',
        bottom: 0, left: 0, width: '100%',
        padding: '8px',
        background: 'linear-gradient(to top, rgba(0,0,0,0.9), transparent)',
        display: 'flex',
        justifyContent: 'flex-end',
        gap: '6px',
        opacity: isHovered ? 1 : 0,
        transition: 'opacity var(--transition-fast)',
      }}>
        <button
          onClick={() => setIsLocked(!isLocked)}
          title="Lock Context"
          style={{
            background: isLocked ? 'rgba(239, 68, 68, 0.2)' : 'rgba(255,255,255,0.1)',
            border: `1px solid ${isLocked ? 'rgba(239, 68, 68, 0.4)' : 'transparent'}`,
            color: isLocked ? '#ef4444' : '#fff',
            width: 24, height: 24, borderRadius: '4px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer',
          }}
        >
          {isLocked ? <Lock size={12} /> : <Unlock size={12} />}
        </button>
        <button
          onClick={onClickFullscreen}
          title="Fullscreen Target"
          style={{
            background: 'rgba(255,255,255,0.1)',
            border: 'none',
            color: '#fff',
            width: 24, height: 24, borderRadius: '4px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer',
          }}
          onMouseOver={(e) => e.currentTarget.style.background = 'var(--primary)'}
          onMouseOut={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
        >
          <Maximize2 size={12} />
        </button>
      </div>

    </div>
  );
}
