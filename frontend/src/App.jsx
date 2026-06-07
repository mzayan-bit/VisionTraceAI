import { useState, useEffect, useRef } from 'react';
import { Camera, Cpu, Upload } from 'lucide-react';
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
  const fileInputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);

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
        if (data.event_type === 'agent_response') {
          handleAgentEvent(data);
        } else {
          handleFrameData(data);
        }
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

  const handleAgentEvent = (data) => {
    console.log("Received Agent Event:", data);
    if (data.action === 'highlight' && data.track_id) {
      setActiveTrackId(data.track_id);
    } else {
      setActiveTrackId(null);
    }
  };

  const handleIntentChange = (intent) => {
    // Rely on handleAgentEvent via WebSocket for highlighting instead.
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload-video', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      console.log('Upload success:', data);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="dashboard-container">
      {/* LEFT PANEL - Live Stream */}
      <div className="stream-panel glass-panel" style={{ flex: 2 }}>
        <div className="stream-header">
          <div className="stream-title-group" style={{ display: 'flex', alignItems: 'center' }}>
            <Camera className="text-accent" size={24} />
            <h2 className="stream-title">Live Camera Feed</h2>
            {isConnected && <div className="live-indicator" />}
            
            <input 
              type="file" 
              accept="video/*" 
              ref={fileInputRef} 
              style={{ display: 'none' }} 
              onChange={handleFileUpload} 
            />
            <button 
              className="upload-button" 
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              style={{
                marginLeft: '1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                background: 'rgba(59, 130, 246, 0.15)',
                color: '#3b82f6',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                padding: '0.4rem 0.8rem',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: isUploading ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              <Upload size={16} />
              {isUploading ? 'Processing...' : 'Upload Video'}
            </button>
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
