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
          </div>
        </div>
        
        <VideoPlayer 
          latestFrame={latestFrame} 
          isConnected={isConnected} 
          activeTrackId={activeTrackId} 
          fps={fps}
          latency={latency}
        />
      </div>

      {/* RIGHT PANEL - AI Insight Layer */}
      <div className="analytics-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', width: 'auto', minWidth: '400px' }}>
        
        {/* Chat Interface */}
        <ChatPanel onIntentChange={handleIntentChange} />

      </div>
    </div>
  );
}

export default App;
