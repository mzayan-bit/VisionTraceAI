import React, { useRef, useEffect } from 'react';

const COLORS = [
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // yellow
  '#ef4444', // red
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
];

const FRAME_WIDTH = 1920;
const FRAME_HEIGHT = 1080;

const VideoPlayer = ({ activeTracks, isConnected }) => {
  const canvasRef = useRef(null);

  // Canvas drawing loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    const render = () => {
      // Clear previous frame to prevent ghosting/flicker
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Internal resolution scaling
      const scaleX = canvas.width / FRAME_WIDTH;
      const scaleY = canvas.height / FRAME_HEIGHT;

      // Draw all active tracks
      Object.values(activeTracks).forEach((track) => {
        if (!track.bbox) return;

        const { bbox, track_id, confidence } = track;
        
        // Color coding based on track_id
        const color = COLORS[track_id % COLORS.length];

        const x = bbox.x1 * scaleX;
        const y = bbox.y1 * scaleY;
        const w = (bbox.x2 - bbox.x1) * scaleX;
        const h = (bbox.y2 - bbox.y1) * scaleY;

        // 1. Soft glow effect for bounding box
        ctx.shadowBlur = 12;
        ctx.shadowColor = color;
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;

        // 2. Rounded bounding box
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(x, y, w, h, 8);
        } else {
          // Fallback if roundRect is not supported
          ctx.rect(x, y, w, h);
        }
        ctx.stroke();

        // 3. Label background (No glow to keep text crisp)
        ctx.shadowBlur = 0;
        ctx.fillStyle = color;
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(x, y - 26, 90, 26, [6, 6, 0, 0]);
        } else {
          ctx.rect(x, y - 26, 90, 26);
        }
        ctx.fill();

        // 4. Label text
        ctx.fillStyle = '#ffffff';
        ctx.font = '600 13px "Outfit", sans-serif';
        ctx.fillText(`ID: ${track_id} ${(confidence * 100).toFixed(0)}%`, x + 8, y - 8);
      });

      // Synchronize with display refresh rate
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => cancelAnimationFrame(animationFrameId);
  }, [activeTracks]);

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
      
      {/* Background / Placeholder stream */}
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
        {!isConnected && "Waiting for video stream connection..."}
      </div>

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
