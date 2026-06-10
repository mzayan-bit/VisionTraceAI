import React, { useState } from 'react';
import { Activity, Users, Layers, TrendingUp, Navigation } from 'lucide-react';

const HEATMAP_MODES = [
  { id: 'density', label: 'Crowd Density', icon: Users, color: '#f59e0b' },
  { id: 'velocity', label: 'Velocity Vector Flow', icon: Navigation, color: '#38bdf8' },
  { id: 'occupancy', label: 'Space Occupancy Duration', icon: Layers, color: '#ec4899' },
  { id: 'traffic', label: 'Route Traffic Intersections', icon: TrendingUp, color: '#10b981' },
];

export default function HeatmapAnalytics() {
  const [activeMode, setActiveMode] = useState(HEATMAP_MODES[0]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '20px' }}>
      
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="glass-panel" style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', gap: '16px', flexShrink: 0 }}>
        <div style={{ width: 40, height: 40, background: 'var(--primary-subtle)', color: 'var(--primary)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Activity size={20} />
        </div>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.2rem', fontFamily: 'var(--font-display)', fontWeight: 600, color: 'var(--text-primary)' }}>
            Spatial Heatmap Analytics
          </h2>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
            Aggregating historical tracking data to visualize high-traffic zones and behavior patterns.
          </div>
        </div>
      </div>

      {/* ── Tabs ───────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: '8px' }}>
        {HEATMAP_MODES.map(mode => {
          const Icon = mode.icon;
          const isActive = activeMode.id === mode.id;
          return (
            <button
              key={mode.id}
              onClick={() => setActiveMode(mode)}
              style={{
                background: isActive ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                color: isActive ? '#fff' : 'var(--text-secondary)',
                border: `1px solid ${isActive ? 'var(--primary)' : 'var(--border-color)'}`,
                padding: '10px 20px',
                borderRadius: '8px',
                display: 'flex', alignItems: 'center', gap: '8px',
                cursor: 'pointer',
                fontFamily: 'var(--font-body)',
                fontSize: '0.85rem',
                fontWeight: isActive ? 600 : 500,
                transition: 'all var(--transition-fast)'
              }}
            >
              <Icon size={16} /> {mode.label}
            </button>
          );
        })}
      </div>

      {/* ── Heatmap Canvas Container ───────────────────────────── */}
      <div className="glass-panel" style={{ flex: 1, position: 'relative', overflow: 'hidden', background: '#050505', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        
        {/* Placeholder Scene Background */}
        <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', background: 'linear-gradient(45deg, #111, #0a0a0a)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ color: 'rgba(255,255,255,0.1)', fontFamily: 'var(--font-mono)', fontSize: '2rem', letterSpacing: '10px' }}>
            SCENE_CAPTURE_01
          </div>
        </div>

        {/* Heatmap Overlay Simulation */}
        <div style={{ 
          position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
          // Use radial gradients to simulate heatmap hotspots based on active mode
          background: activeMode.id === 'density' 
            ? 'radial-gradient(circle at 30% 60%, rgba(245, 158, 11, 0.4) 0%, transparent 30%), radial-gradient(circle at 70% 40%, rgba(239, 68, 68, 0.5) 0%, transparent 40%)'
            : activeMode.id === 'occupancy'
            ? 'radial-gradient(circle at 50% 50%, rgba(236, 72, 153, 0.3) 0%, transparent 50%)'
            : 'linear-gradient(90deg, rgba(56, 189, 248, 0.1) 0%, transparent 100%)',
          mixBlendMode: 'screen',
          pointerEvents: 'none',
          transition: 'background 0.5s ease'
        }} />

        {/* Mock Flow Vectors for Velocity mode */}
        {activeMode.id === 'velocity' && (
          <div style={{ position: 'absolute', top: '40%', left: '40%', color: 'var(--primary)', transform: 'rotate(45deg)', opacity: 0.5 }}>
            <Navigation size={48} />
          </div>
        )}

      </div>

    </div>
  );
}
