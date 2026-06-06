import { useState, useEffect, useRef } from 'react';
import { Camera, Cpu } from 'lucide-react';
import VideoPlayer from './components/VideoPlayer';
import ChatPanel from './components/ChatPanel';
import './App.css';

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [framesReceived, setFramesReceived] = useState(0);
  const [fps, setFps] = useState(0);
  const [latency, setLatency] = useState(0);
  const [latestFrame, setLatestFrame] = useState(null);
  const [recentTracks, setRecentTracks] = useState([]);
  const [activeTrackId, setActiveTrackId] = useState(null);
  
  const wsRef = useRef(null);
  const framesCountRef = useRef(0);

  // Connect to WebSocket
  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket('ws://localhost:8000/ws/video');
      
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
    }, 1000);
    
    return () => clearInterval(interval);
  }, []);

  const handleFrameData = (data) => {
    setFramesReceived(prev => prev + 1);
    framesCountRef.current += 1;
    setLatestFrame(data);
    
    if (data.latency_ms !== undefined) {
      setLatency(data.latency_ms);
    }
    
    // Extract unique track IDs from the payload
    if (data.track_ids && data.track_ids.length > 0) {
      setRecentTracks(prev => {
        const newTracks = [...prev];
        data.track_ids.forEach(id => {
          if (!newTracks.find(t => t.track_id === id)) {
            newTracks.unshift({ track_id: id, firstSeen: new Date().toLocaleTimeString(), camera_id: 'cam_1' });
          }
        });
        return newTracks.slice(0, 10);
      });
    }
  };

  const handleIntentChange = (intent) => {
    // If the intent suggests tracking a specific person, we could highlight them
    if (intent && intent.type === 'track' && intent.target_id) {
      setActiveTrackId(intent.target_id);
    }
  };

  return (
    <div className="dashboard-container">
      {/* LEFT PANEL - Live Stream */}
      <div className="stream-panel glass-panel" style={{ flex: 2 }}>
        <div className="stream-header">
          <div className="stream-title-group">
            <Camera className="text-accent" size={24} />
            <h2 className="stream-title">Live Camera Feed</h2>
            {isConnected && <div className="live-indicator" />}
          </div>
          <div className="flex gap-4">
            <div className="fps-badge">
              {fps} FPS
            </div>
            <div className="latency-badge" style={{
              background: 'rgba(245, 158, 11, 0.15)',
              color: 'var(--warning)',
              padding: '0.25rem 0.75rem',
              borderRadius: 'var(--radius-sm)',
              fontFamily: '"Outfit", sans-serif',
              fontWeight: 600,
              fontSize: '0.875rem',
              border: '1px solid rgba(245, 158, 11, 0.3)'
            }}>
              {latency} ms
            </div>
          </div>
        </div>
        
        <VideoPlayer 
          latestFrame={latestFrame} 
          isConnected={isConnected} 
          activeTrackId={activeTrackId} 
        />
      </div>

      {/* RIGHT PANEL - Analytics & Chat */}
      <div className="analytics-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1rem', width: 'auto', minWidth: '400px' }}>
        
        {/* Chat Interface */}
        <ChatPanel onIntentChange={handleIntentChange} />

        {/* Recent Detections */}
        <div className="recent-tracks glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', maxHeight: '40%' }}>
          <div className="status-header">
            <Cpu size={20} />
            <h3>Detection Logs</h3>
          </div>
          
          <div style={{ flex: 1, overflowY: 'auto', paddingRight: '0.5rem', marginTop: '1rem' }}>
            {recentTracks.map((track, idx) => (
              <div key={`${track.track_id}-${idx}`} className="track-item" style={{ marginBottom: '0.75rem' }}>
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
    </div>
  );
}

export default App;
