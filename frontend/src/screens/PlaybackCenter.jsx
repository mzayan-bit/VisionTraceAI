import React, { useState } from 'react';
import { Play, Pause, SkipBack, SkipForward, Maximize, Clock, FileWarning, ShieldAlert } from 'lucide-react';
import { motion } from 'framer-motion';

const PLAYBACK_SPEEDS = [0.25, 0.5, 1.0, 2.0, 4.0];

// Mock historical timeline events
const EVENTS = [
  { timePercent: 12, width: 2, type: 'motion', color: '#3b82f6' },
  { timePercent: 35, width: 5, type: 'loitering', color: '#f59e0b' },
  { timePercent: 68, width: 1.5, type: 'security', color: '#ef4444' },
  { timePercent: 82, width: 4, type: 'motion', color: '#3b82f6' },
];

export default function PlaybackCenter() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [progress, setProgress] = useState(45); // percent
  const [hoveredEvent, setHoveredEvent] = useState(null);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '20px' }}>
      
      {/* ── Main Video Area ────────────────────────────────────── */}
      <div className="glass-panel" style={{ 
        flex: 1, 
        position: 'relative', 
        background: '#050505', 
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
          Historical Stream Rendering Pipeline
        </div>
        
        {/* Mock Top Overlay */}
        <div style={{ position: 'absolute', top: 20, left: 20, color: '#fff', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', background: 'rgba(0,0,0,0.6)', padding: '4px 8px', borderRadius: '4px' }}>
          2026-06-10 14:32:04 UTC
        </div>
      </div>

      {/* ── Playback Control Strip ─────────────────────────────── */}
      <div className="glass-panel" style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        {/* Timeline Scrubber */}
        <div style={{ position: 'relative', height: '36px', display: 'flex', alignItems: 'center' }}>
          {/* Base Track */}
          <div style={{ position: 'absolute', width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
            {/* Filled Track */}
            <div style={{ width: `${progress}%`, height: '100%', background: 'var(--primary)', transition: 'width 0.1s linear' }} />
          </div>

          {/* Event Blocks Overlay */}
          {EVENTS.map((ev, i) => (
            <div 
              key={i}
              onMouseEnter={() => setHoveredEvent(ev)}
              onMouseLeave={() => setHoveredEvent(null)}
              style={{
                position: 'absolute',
                left: `${ev.timePercent}%`,
                width: `${ev.width}%`,
                height: '16px',
                background: ev.color,
                borderRadius: '2px',
                cursor: 'pointer',
                opacity: 0.8,
                transition: 'all var(--transition-fast)'
              }}
              onMouseOver={(e) => { e.currentTarget.style.height = '20px'; e.currentTarget.style.opacity = 1; }}
              onMouseOut={(e) => { e.currentTarget.style.height = '16px'; e.currentTarget.style.opacity = 0.8; }}
            />
          ))}

          {/* Scrubber Handle */}
          <motion.div 
            style={{
              position: 'absolute',
              left: `calc(${progress}% - 8px)`,
              width: '16px', height: '24px',
              background: '#fff',
              borderRadius: '4px',
              cursor: 'grab',
              boxShadow: '0 0 10px rgba(0,0,0,0.5)'
            }}
          />
        </div>

        {/* Controls Layout */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          
          {/* Legend / Status */}
          <div style={{ display: 'flex', gap: '16px', color: 'var(--text-secondary)', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: 8, height: 8, background: '#3b82f6', borderRadius: '50%' }} /> Motion
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: 8, height: 8, background: '#f59e0b', borderRadius: '50%' }} /> Loitering
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: 8, height: 8, background: '#ef4444', borderRadius: '50%' }} /> Infraction
            </div>
          </div>

          {/* Core Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <button style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: 'pointer' }}><SkipBack size={20} /></button>
            <button 
              onClick={() => setIsPlaying(!isPlaying)}
              style={{ 
                background: 'var(--primary)', border: 'none', color: '#fff', 
                width: 48, height: 48, borderRadius: '50%', 
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                cursor: 'pointer', boxShadow: 'var(--shadow-glow)'
              }}
            >
              {isPlaying ? <Pause size={24} /> : <Play size={24} style={{ marginLeft: '4px' }} />}
            </button>
            <button style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: 'pointer' }}><SkipForward size={20} /></button>
          </div>

          {/* Speed & Maximize */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ display: 'flex', background: 'rgba(0,0,0,0.2)', padding: '4px', borderRadius: 'var(--radius-sm)' }}>
              {PLAYBACK_SPEEDS.map(speed => (
                <button
                  key={speed}
                  onClick={() => setPlaybackSpeed(speed)}
                  style={{
                    background: playbackSpeed === speed ? 'rgba(255,255,255,0.1)' : 'transparent',
                    color: playbackSpeed === speed ? 'var(--text-primary)' : 'var(--text-secondary)',
                    border: 'none',
                    padding: '4px 12px',
                    borderRadius: '4px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.8rem',
                    fontWeight: playbackSpeed === speed ? 700 : 500,
                    cursor: 'pointer'
                  }}
                >
                  {speed}x
                </button>
              ))}
            </div>
            <button style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', padding: '8px', borderRadius: '6px', cursor: 'pointer' }}>
              <Maximize size={16} />
            </button>
          </div>

        </div>
      </div>

    </div>
  );
}
