import React, { useRef, useEffect, useState } from 'react';

const COLORS = [
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // yellow
  '#ef4444', // red
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
];



const VideoPlayer = ({ latestFrame, isConnected, activeTrackId, fps, latency }) => {
  const canvasRef = useRef(null);
  const imageRef = useRef(new Image());
  const interpolatedBoxesRef = useRef({});

  // Canvas drawing loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    const render = () => {
      // Clear previous frame
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // 1. Draw base64 background frame if available
      if (latestFrame && latestFrame.frame) {
        if (imageRef.current.src !== `data:image/jpeg;base64,${latestFrame.frame}`) {
          imageRef.current.src = `data:image/jpeg;base64,${latestFrame.frame}`;
        }
        
        // Only draw if image is loaded to prevent flickering
        if (imageRef.current.complete && imageRef.current.naturalWidth > 0) {
          if (canvas.width !== imageRef.current.naturalWidth) {
             canvas.width = imageRef.current.naturalWidth;
             canvas.height = imageRef.current.naturalHeight;
          }
          ctx.drawImage(imageRef.current, 0, 0, canvas.width, canvas.height);
        }
      }

      // 1:1 scaling since YOLO boxes are in original image dimensions
      const scaleX = 1;
      const scaleY = 1;

      // Ensure boxes exist
      const detections = latestFrame?.detections || [];
      const track_ids = latestFrame?.track_ids || [];
      const colors_array = latestFrame?.colors || [];

      // Update target interpolations
      const currentTargets = {};
      const currentColors = {};
      detections.forEach((bbox, idx) => {
        const track_id = track_ids[idx];
        if (track_id === undefined) return;
        currentTargets[track_id] = bbox;
        currentColors[track_id] = colors_array[idx] || COLORS[track_id % COLORS.length];
      });

      // Remove stale boxes
      Object.keys(interpolatedBoxesRef.current).forEach(id => {
        if (!currentTargets[id]) {
          delete interpolatedBoxesRef.current[id];
        }
      });

      // 2. Draw all active tracks with interpolation
      Object.entries(currentTargets).forEach(([id, targetBox]) => {
        const track_id = parseInt(id, 10);
        const isActive = track_id === activeTrackId;
        
        // Initialize or interpolate
        let currentBox = interpolatedBoxesRef.current[track_id];
        if (!currentBox) {
          currentBox = { ...targetBox }; // snap to target
        } else {
          // Linear interpolation factor (0.15 for smoother Palantir-like tracking)
          const lerp = 0.15; 
          currentBox.x1 += (targetBox.x1 - currentBox.x1) * lerp;
          currentBox.y1 += (targetBox.y1 - currentBox.y1) * lerp;
          currentBox.x2 += (targetBox.x2 - currentBox.x2) * lerp;
          currentBox.y2 += (targetBox.y2 - currentBox.y2) * lerp;
        }
        interpolatedBoxesRef.current[track_id] = currentBox;

        const baseColor = currentColors[track_id];
        const color = isActive ? '#ef4444' : baseColor; // Highlight in red
        
        // Fade inactive tracks
        ctx.globalAlpha = (activeTrackId !== null && !isActive) ? 0.3 : 1.0;

        const x = currentBox.x1 * scaleX;
        const y = currentBox.y1 * scaleY;
        const w = (currentBox.x2 - currentBox.x1) * scaleX;
        const h = (currentBox.y2 - currentBox.y1) * scaleY;

        // 1. Soft glow effect for bounding box
        ctx.shadowBlur = isActive ? 24 : 16;
        ctx.shadowColor = color;
        ctx.strokeStyle = color;
        ctx.lineWidth = isActive ? 3 : 2;

        // 2. Rounded bounding box
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(x, y, w, h, 6);
        } else {
          ctx.rect(x, y, w, h);
        }
        ctx.stroke();

        // 3. Optional: Hide labels to clean up UI, only show if hovered or active
        if (isActive) {
          ctx.shadowBlur = 0;
          ctx.fillStyle = color;
          ctx.beginPath();
          if (ctx.roundRect) {
            ctx.roundRect(x, y - 24, 60, 24, [4, 4, 0, 0]);
          } else {
            ctx.rect(x, y - 24, 60, 24);
          }
          ctx.fill();

          ctx.fillStyle = '#ffffff';
          ctx.font = '600 12px "Outfit", sans-serif';
          ctx.fillText(`TRK_${track_id}`, x + 6, y - 7);
        }
        
        // Reset alpha
        ctx.globalAlpha = 1.0;
      });

      // Synchronize with display refresh rate
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => cancelAnimationFrame(animationFrameId);
  }, [latestFrame, activeTrackId]);

  return (
    <div style={{
      position: 'relative',
      flex: 1,
      width: '100%',
      height: '100%',
      backgroundColor: '#0a0a0f',
      overflow: 'hidden',
      borderBottomLeftRadius: 'var(--radius-lg)',
      borderBottomRightRadius: 'var(--radius-lg)'
    }}>
      
      {/* Background / Placeholder stream if no frame */}
      {(!latestFrame || !latestFrame.frame) && (
        <div style={{
          position: 'absolute',
          top: 0, left: 0, width: '100%', height: '100%',
          background: 'linear-gradient(45deg, #1a1d2c 0%, #0f111a 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-secondary)',
          opacity: 0.5
        }}>
          {!isConnected ? "Connecting to WebSocket stream..." : "Waiting for video frames..."}
        </div>
      )}

      {/* Hardware-accelerated Canvas Overlay Layer */}
      <canvas
        ref={canvasRef}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          pointerEvents: 'none',
          zIndex: 10
        }}
      />
      
      {/* Minimal Metrics Overlay */}
      <div style={{
        position: 'absolute',
        top: '1rem',
        right: '1rem',
        display: 'flex',
        gap: '0.5rem',
        zIndex: 20,
        pointerEvents: 'none'
      }}>
        <div style={{
          background: 'rgba(12, 14, 22, 0.7)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          color: 'var(--text-secondary)',
          padding: '0.35rem 0.85rem',
          borderRadius: '20px',
          fontFamily: '"Outfit", sans-serif',
          fontWeight: 600,
          fontSize: '0.75rem',
          letterSpacing: '0.5px'
        }}>
          {fps || 0} FPS
        </div>
        <div style={{
          background: 'rgba(56, 189, 248, 0.1)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(56, 189, 248, 0.2)',
          color: 'var(--text-accent)',
          padding: '0.35rem 0.85rem',
          borderRadius: '20px',
          fontFamily: '"Outfit", sans-serif',
          fontWeight: 600,
          fontSize: '0.75rem',
          letterSpacing: '0.5px'
        }}>
          {latency || 0} MS
        </div>
      </div>
      
      {/* Quick Actions Overlay */}
      <div style={{
        position: 'absolute',
        bottom: '1.5rem',
        left: '50%',
        transform: 'translateX(-50%)',
        display: 'flex',
        gap: '1rem',
        zIndex: 20,
      }}>
        <button 
          onClick={() => window.dispatchEvent(new CustomEvent('ai-query', { detail: 'What is currently happening in the scene?' }))}
          style={{
            background: 'rgba(12, 14, 22, 0.85)',
            backdropFilter: 'blur(16px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: '#fff',
            padding: '0.6rem 1.2rem',
            borderRadius: '30px',
            fontFamily: '"Inter", sans-serif',
            fontSize: '0.85rem',
            fontWeight: 500,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
            transition: 'all 0.2s'
          }}
          onMouseOver={e => { e.currentTarget.style.background = 'rgba(56, 189, 248, 0.15)'; e.currentTarget.style.borderColor = 'rgba(56, 189, 248, 0.3)'; }}
          onMouseOut={e => { e.currentTarget.style.background = 'rgba(12, 14, 22, 0.85)'; e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)'; }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>
          Explain Scene
        </button>
        <button 
          onClick={() => window.dispatchEvent(new CustomEvent('ai-query', { detail: 'Summarize what happened in the last 30 seconds' }))}
          style={{
            background: 'rgba(12, 14, 22, 0.85)',
            backdropFilter: 'blur(16px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: '#fff',
            padding: '0.6rem 1.2rem',
            borderRadius: '30px',
            fontFamily: '"Inter", sans-serif',
            fontSize: '0.85rem',
            fontWeight: 500,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
            transition: 'all 0.2s'
          }}
          onMouseOver={e => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'; e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)'; }}
          onMouseOut={e => { e.currentTarget.style.background = 'rgba(12, 14, 22, 0.85)'; e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)'; }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path><path d="M12 7v5l4 2"></path></svg>
          Replay 30s
        </button>
      </div>
    </div>
  );
};

export default VideoPlayer;
