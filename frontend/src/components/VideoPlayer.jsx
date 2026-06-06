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

// Target internal resolution
const FRAME_WIDTH = 1920;
const FRAME_HEIGHT = 1080;

const VideoPlayer = ({ latestFrame, isConnected, activeTrackId }) => {
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
          ctx.drawImage(imageRef.current, 0, 0, canvas.width, canvas.height);
        }
      }

      // Internal resolution scaling
      const scaleX = canvas.width / FRAME_WIDTH;
      const scaleY = canvas.height / FRAME_HEIGHT;

      // Ensure boxes exist
      const detections = latestFrame?.detections || [];
      const track_ids = latestFrame?.track_ids || [];

      // Update target interpolations
      const currentTargets = {};
      detections.forEach((bbox, idx) => {
        const track_id = track_ids[idx];
        if (track_id === undefined) return;
        currentTargets[track_id] = bbox;
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
          // Linear interpolation factor (0.3 = 30% towards target per frame)
          const lerp = 0.3; 
          currentBox.x1 += (targetBox.x1 - currentBox.x1) * lerp;
          currentBox.y1 += (targetBox.y1 - currentBox.y1) * lerp;
          currentBox.x2 += (targetBox.x2 - currentBox.x2) * lerp;
          currentBox.y2 += (targetBox.y2 - currentBox.y2) * lerp;
        }
        interpolatedBoxesRef.current[track_id] = currentBox;

        const color = isActive ? '#ffffff' : COLORS[track_id % COLORS.length];

        const x = currentBox.x1 * scaleX;
        const y = currentBox.y1 * scaleY;
        const w = (currentBox.x2 - currentBox.x1) * scaleX;
        const h = (currentBox.y2 - currentBox.y1) * scaleY;

        // 1. Soft glow effect for bounding box
        ctx.shadowBlur = isActive ? 20 : 12;
        ctx.shadowColor = color;
        ctx.strokeStyle = color;
        ctx.lineWidth = isActive ? 4 : 3;

        // 2. Rounded bounding box
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(x, y, w, h, 8);
        } else {
          ctx.rect(x, y, w, h);
        }
        ctx.stroke();

        // 3. Label background
        ctx.shadowBlur = 0;
        ctx.fillStyle = color;
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(x, y - 26, 70, 26, [6, 6, 0, 0]);
        } else {
          ctx.rect(x, y - 26, 70, 26);
        }
        ctx.fill();

        // 4. Label text
        ctx.fillStyle = isActive ? '#000000' : '#ffffff';
        ctx.font = '600 13px "Outfit", sans-serif';
        ctx.fillText(`ID: ${track_id}`, x + 8, y - 8);
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
        width={FRAME_WIDTH}
        height={FRAME_HEIGHT}
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
    </div>
  );
};

export default VideoPlayer;
