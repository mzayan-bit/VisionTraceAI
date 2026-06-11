import React, { useState, useRef, useCallback } from 'react';
import { Play, Pause, SkipBack, SkipForward, Maximize, Download } from 'lucide-react';
import { motion } from 'framer-motion';

const PLAYBACK_SPEEDS = [0.25, 0.5, 1.0, 2.0, 4.0];

// Mock historical timeline events
const EVENTS = [
  { timePercent: 12, width: 2, type: 'motion', color: '#3b82f6' },
  { timePercent: 35, width: 5, type: 'loitering', color: '#f59e0b' },
  { timePercent: 68, width: 1.5, type: 'security', color: '#ef4444' },
  { timePercent: 82, width: 4, type: 'motion', color: '#3b82f6' },
];

const VIDEO_SRC = 'http://localhost:8000/download-video';

export default function PlaybackCenter() {
  const handleExportVideo = () => {
    const a = document.createElement('a');
    a.href = VIDEO_SRC;
    a.download = `VisionTrace_Processed_${new Date().toISOString().slice(0,10)}.mp4`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '24px' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderBottom: '1px solid var(--border-color)', paddingBottom: '20px' }}>
        <div>
          <h1 className="text-heading" style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: 0 }}>
            <div style={{ width: 40, height: 40, background: 'var(--primary-subtle)', color: 'var(--primary)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Play size={20} />
            </div>
            Processed Video Playback
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: '8px 0 0 52px', fontSize: '0.9rem' }}>
            Review the latest backend-processed video with YOLO-pose joints and object tracking overlays.
          </p>
        </div>

        <button
          onClick={handleExportVideo}
          style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            background: 'var(--primary)', color: '#fff',
            border: 'none', padding: '10px 20px', borderRadius: '6px',
            fontWeight: 600, cursor: 'pointer',
            transition: 'all var(--transition-fast)',
          }}
        >
          <Download size={16} /> Export Video
        </button>
      </div>

      {/* Main Video Area */}
      <div className="glass-panel" style={{ flex: 1, background: '#000', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <video 
          src={VIDEO_SRC}
          controls
          autoPlay
          style={{ width: '100%', height: '100%', objectFit: 'contain' }}
        >
          Your browser does not support the video element.
        </video>
      </div>

    </div>
  );
}
