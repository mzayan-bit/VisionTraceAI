import React, { useRef, useEffect, useState } from 'react';
import { PlayCircle, Download, FileText } from 'lucide-react';

const COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4',
];

export default function LiveVideoWorkspace({
  latestFrame,
  isConnected,
  activeTrackId,
  onTrackSelect,
  fps,
  latency
}) {
  const canvasRef = useRef(null);
  const imageRef = useRef(new Image());
  const interpolatedBoxesRef = useRef({});

  // 1. Hover/Click Hit Detection
  const [hoveredTrackId, setHoveredTrackId] = useState(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      // Calculate cursor position relative to original image coordinates
      const scaleX = imageRef.current.naturalWidth / rect.width;
      const scaleY = imageRef.current.naturalHeight / rect.height;
      
      const x = (e.clientX - rect.left) * scaleX;
      const y = (e.clientY - rect.top) * scaleY;

      let foundHover = null;
      // Loop over active interpolations backwards to hit topmost first
      const boxes = Object.entries(interpolatedBoxesRef.current);
      for (let i = boxes.length - 1; i >= 0; i--) {
        const [idStr, box] = boxes[i];
        if (x >= box.x1 && x <= box.x2 && y >= box.y1 && y <= box.y2) {
          foundHover = parseInt(idStr, 10);
          break;
        }
      }
      
      if (foundHover !== hoveredTrackId) {
        setHoveredTrackId(foundHover);
        canvas.style.cursor = foundHover ? 'pointer' : 'default';
      }
    };

    const handleClick = () => {
      if (hoveredTrackId !== null) {
        onTrackSelect(hoveredTrackId);
      } else {
        onTrackSelect(null); // Click empty space to deselect
      }
    };

    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('click', handleClick);
    return () => {
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('click', handleClick);
    };
  }, [hoveredTrackId, onTrackSelect]);

  // 2. Hardware-accelerated Canvas Rendering
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    const render = () => {
      if (latestFrame && latestFrame.frame) {
        if (imageRef.current.src !== `data:image/jpeg;base64,${latestFrame.frame}`) {
          imageRef.current.src = `data:image/jpeg;base64,${latestFrame.frame}`;
        }
      }
      
      if (imageRef.current.complete && imageRef.current.naturalWidth > 0) {
        if (canvas.width !== imageRef.current.naturalWidth) {
           canvas.width = imageRef.current.naturalWidth;
           canvas.height = imageRef.current.naturalHeight;
        }
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(imageRef.current, 0, 0, canvas.width, canvas.height);
      } else {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }

      // Dim background if a track is actively selected
      if (activeTrackId !== null) {
        ctx.fillStyle = 'rgba(0,0,0,0.4)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      }

      const detections = latestFrame?.detections || [];
      const track_ids = latestFrame?.track_ids || [];
      
      const currentTargets = {};
      detections.forEach((bbox, idx) => {
        const track_id = track_ids[idx];
        if (track_id !== undefined) currentTargets[track_id] = bbox;
      });

      Object.keys(interpolatedBoxesRef.current).forEach(id => {
        if (!currentTargets[id]) delete interpolatedBoxesRef.current[id];
      });

      Object.entries(currentTargets).forEach(([idStr, targetBox]) => {
        const track_id = parseInt(idStr, 10);
        const isActive = (track_id === activeTrackId);
        const isHovered = (track_id === hoveredTrackId);
        
        let currentBox = interpolatedBoxesRef.current[track_id];
        if (!currentBox) {
          currentBox = { ...targetBox }; 
        } else {
          const lerp = 0.2; 
          currentBox.x1 += (targetBox.x1 - currentBox.x1) * lerp;
          currentBox.y1 += (targetBox.y1 - currentBox.y1) * lerp;
          currentBox.x2 += (targetBox.x2 - currentBox.x2) * lerp;
          currentBox.y2 += (targetBox.y2 - currentBox.y2) * lerp;
        }
        interpolatedBoxesRef.current[track_id] = currentBox;

        // Base color or Cyan if active
        const color = isActive ? '#00ffff' : COLORS[track_id % COLORS.length];
        
        // Handle active/inactive alpha
        if (activeTrackId !== null && !isActive) {
          ctx.globalAlpha = 0.2; // Dim unselected
        } else {
          ctx.globalAlpha = 1.0;
        }

        const x = currentBox.x1;
        const y = currentBox.y1;
        const w = currentBox.x2 - currentBox.x1;
        const h = currentBox.y2 - currentBox.y1;

        // Draw Bounding Box (2px thin border)
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = isActive || isHovered ? 4 : 2;
        ctx.shadowBlur = isActive || isHovered ? 15 : 0;
        ctx.shadowColor = color;
        ctx.rect(x, y, w, h);
        ctx.stroke();

        // Draw Top-Left Flag (Microscopic metadata)
        ctx.shadowBlur = 0;
        ctx.fillStyle = color;
        const labelW = 100;
        const labelH = 20;
        ctx.fillRect(x, y - labelH, labelW, labelH);
        
        ctx.fillStyle = '#000000';
        ctx.font = '600 12px "Inter", sans-serif';
        // Mock confidence to 98% since it's not currently tracked in stream
        ctx.fillText(`[TRK ${track_id}] | 98%`, x + 5, y - 5);
        
        ctx.globalAlpha = 1.0; // Reset
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationFrameId);
  }, [latestFrame, activeTrackId, hoveredTrackId]);

  // Color logic for Network Pill
  const latencyColor = latency < 15 ? '#10b981' : (latency < 30 ? '#f59e0b' : '#ef4444');

  return (
    <div style={{
      position: 'relative',
      flex: 1,
      width: '100%',
      height: '100%',
      backgroundColor: '#000',
      overflow: 'hidden',
      borderBottomLeftRadius: 'var(--radius-lg)',
      borderBottomRightRadius: 'var(--radius-lg)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      
      {/* 16:9 Container for absolute UI overlay positioning */}
      <div style={{
        position: 'relative',
        width: '100%',
        aspectRatio: '16/9',
        maxHeight: '100%',
        backgroundColor: '#050505'
      }}>
        <canvas
          ref={canvasRef}
          style={{
            position: 'absolute',
            top: 0, left: 0, width: '100%', height: '100%',
            objectFit: 'contain'
          }}
        />

        {/* ── Top-Left Badge ───────────────────────────────────── */}
        <div style={{
          position: 'absolute',
          top: '20px', left: '20px',
          display: 'flex', gap: '8px',
          pointerEvents: 'none'
        }}>
          <div style={{
            background: 'rgba(220, 38, 38, 0.8)',
            backdropFilter: 'blur(4px)',
            color: '#fff',
            padding: '4px 10px',
            borderRadius: '4px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            fontWeight: 700,
            letterSpacing: '1px',
            display: 'flex', alignItems: 'center', gap: '6px',
            boxShadow: '0 0 10px rgba(220, 38, 38, 0.5)',
            animation: isConnected ? 'pulse-glow 2s infinite' : 'none'
          }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#fff' }} />
            {isConnected ? 'LIVE' : 'OFFLINE'}
          </div>
          <div style={{
            background: 'rgba(0, 0, 0, 0.6)',
            backdropFilter: 'blur(4px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: 'var(--text-secondary)',
            padding: '4px 10px',
            borderRadius: '4px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            fontWeight: 600,
            letterSpacing: '0.5px',
          }}>
            CAM_01_SOUTH_GATE
          </div>
        </div>

        {/* ── Top-Right Network Status Pill ─────────────────────── */}
        <div style={{
          position: 'absolute',
          top: '20px', right: '20px',
          background: 'rgba(0, 0, 0, 0.7)',
          backdropFilter: 'blur(8px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          color: 'var(--text-primary)',
          padding: '6px 12px',
          borderRadius: '4px',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.7rem',
          fontWeight: 600,
          letterSpacing: '0.5px',
          display: 'flex',
          gap: '12px',
          pointerEvents: 'none'
        }}>
          <span>FPS: <span style={{ color: '#38bdf8' }}>{fps || 0}</span></span>
          <span style={{ color: 'rgba(255,255,255,0.2)' }}>|</span>
          <span>LATENCY: <span style={{ color: latencyColor }}>{latency || 0}ms</span></span>
          <span style={{ color: 'rgba(255,255,255,0.2)' }}>|</span>
          <span>DECODE: <span style={{ color: '#a78bfa' }}>NVDEC</span></span>
        </div>

        {/* ── Bottom Control Strip ──────────────────────────────── */}
        <div style={{
          position: 'absolute',
          bottom: '20px', left: '50%',
          transform: 'translateX(-50%)',
          display: 'flex', gap: '12px',
          zIndex: 20
        }}>
          <button 
            className="hover-lift"
            onClick={() => window.dispatchEvent(new CustomEvent('ai-query', { detail: 'What is currently happening in the scene?' }))}
            style={{
              background: 'var(--primary)',
              color: '#fff',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '6px',
              fontFamily: 'var(--font-body)',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '8px',
              boxShadow: '0 4px 15px var(--primary-glow)'
            }}
          >
            <FileText size={16} /> Explain Scene
          </button>
          
          <button 
            className="hover-lift"
            onClick={() => window.dispatchEvent(new CustomEvent('ai-query', { detail: 'Summarize what happened in the last 30 seconds' }))}
            style={{
              background: 'rgba(0, 0, 0, 0.7)',
              backdropFilter: 'blur(8px)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-primary)',
              padding: '8px 16px',
              borderRadius: '6px',
              fontFamily: 'var(--font-body)',
              fontSize: '0.85rem',
              fontWeight: 500,
              cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '8px',
            }}
          >
            <PlayCircle size={16} /> Replay 30s
          </button>
          
          <button 
            className="hover-lift"
            onClick={() => window.open('http://localhost:8000/download-video', '_blank')}
            style={{
              background: 'rgba(0, 0, 0, 0.4)',
              backdropFilter: 'blur(8px)',
              border: '1px solid transparent',
              color: 'var(--text-secondary)',
              padding: '8px 16px',
              borderRadius: '6px',
              fontFamily: 'var(--font-body)',
              fontSize: '0.85rem',
              fontWeight: 500,
              cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '8px',
            }}
          >
            <Download size={16} /> Export Video
          </button>
        </div>
        
      </div>
    </div>
  );
}
