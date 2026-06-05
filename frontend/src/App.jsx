import { useState, useEffect, useRef } from 'react';
import { Activity, Camera, Cpu, Wifi, WifiOff } from 'lucide-react';
import VideoPlayer from './components/VideoPlayer';
import './App.css';

// Assume default 1080p stream for scaling bounding boxes
const FRAME_WIDTH = 1920;
const FRAME_HEIGHT = 1080;

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [framesReceived, setFramesReceived] = useState(0);
  const [fps, setFps] = useState(0);
  const [latency, setLatency] = useState(0);
  const [activeTracks, setActiveTracks] = useState({});
  const [recentTracks, setRecentTracks] = useState([]);
  
  const wsRef = useRef(null);
  const lastFrameTimeRef = useRef(Date.now());
  const framesCountRef = useRef(0);

  // Connect to WebSocket
  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket('ws://localhost:8000/ws/stream');
      
      ws.onopen = () => {
        setIsConnected(true);
        console.log('Connected to VisionTraceAI Stream');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleFrameData(data);
      };
      
      ws.onclose = () => {
        setIsConnected(false);
        // Auto reconnect after 2 seconds
        setTimeout(connect, 2000);
      };
      
      ws.onerror = (err) => {
        console.error('WebSocket Error:', err);
        ws.close();
      };
      
      wsRef.current = ws;
    };

    connect();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Calculate FPS
  useEffect(() => {
    const interval = setInterval(() => {
      setFps(framesCountRef.current);
      framesCountRef.current = 0;
      
      // Cleanup stale tracks (not seen in last 1 second)
      const now = Date.now();
      setActiveTracks(prev => {
        const next = { ...prev };
        Object.keys(next).forEach(trackId => {
          if (now - next[trackId].lastSeen > 1000) {
            delete next[trackId];
          }
        });
        return next;
      });
    }, 1000);
    
    return () => clearInterval(interval);
  }, []);

  const handleFrameData = (data) => {
    setFramesReceived(prev => prev + 1);
    framesCountRef.current += 1;
    
    if (data.latency_ms) {
      setLatency(data.latency_ms);
    }
    
    // Update active tracks for bounding boxes
    setActiveTracks(prev => ({
      ...prev,
      [data.track_id]: {
        ...data,
        lastSeen: Date.now()
      }
    }));
    
    // Update recent tracks history panel (keep last 10 unique)
    setRecentTracks(prev => {
      const exists = prev.find(t => t.track_id === data.track_id);
      if (!exists) {
        return [{...data, firstSeen: new Date().toLocaleTimeString()}, ...prev].slice(0, 10);
      }
      return prev;
    });
  };

  return (
    <div className="dashboard-container">
      {/* LEFT PANEL - Live Stream */}
      <div className="stream-panel glass-panel">
        <div className="stream-header">
          <div className="stream-title-group">
            <Camera className="text-accent" size={24} />
            <h2 className="stream-title">Live Camera Feed</h2>
            {isConnected && <div className="live-indicator" />}
          </div>
          <div className="fps-badge">
            {fps} FPS
          </div>
        </div>
        
        <VideoPlayer activeTracks={activeTracks} isConnected={isConnected} />
      </div>

      {/* RIGHT PANEL - Analytics */}
      <div className="analytics-panel">
        
        {/* System Status */}
        <div className="status-card glass-panel">
          <div className="status-header">
            <Activity size={20} />
            <h3>System Status</h3>
          </div>
          
          <div className="status-metric">
            <span className="metric-label">Connection</span>
            <span className={`metric-value ${isConnected ? 'connected' : 'disconnected'}`}>
              {isConnected ? <span className="flex items-center gap-2"><Wifi size={16} /> Online</span> : <span className="flex items-center gap-2"><WifiOff size={16} /> Offline</span>}
            </span>
          </div>
          
          <div className="status-metric">
            <span className="metric-label">Active Tracks</span>
            <span className="metric-value">{Object.keys(activeTracks).length}</span>
          </div>
          
          <div className="status-metric">
            <span className="metric-label">Total Frames</span>
            <span className="metric-value">{framesReceived.toLocaleString()}</span>
          </div>

          <div className="status-metric">
            <span className="metric-label">Pipeline Latency</span>
            <span className="metric-value">{latency.toFixed(1)} ms</span>
          </div>
        </div>

        {/* Recent Detections */}
        <div className="recent-tracks glass-panel">
          <div className="status-header">
            <Cpu size={20} />
            <h3>Recent Detections</h3>
          </div>
          
          {recentTracks.map((track, idx) => (
            <div key={`${track.track_id}-${idx}`} className="track-item">
              <div className="track-avatar">
                {track.track_id}
              </div>
              <div className="track-details">
                <div className="track-id">Person #{track.track_id}</div>
                <div className="track-meta">
                  <span>{track.camera_id}</span> • <span>{track.firstSeen}</span>
                </div>
              </div>
            </div>
          ))}
          
          {recentTracks.length === 0 && (
            <div className="text-center text-secondary py-4" style={{ color: 'var(--text-secondary)' }}>
              No tracks detected yet.
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default App;
