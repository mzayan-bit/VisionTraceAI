import { useState, useEffect, useRef } from 'react';
import { Camera, Cpu, Upload } from 'lucide-react';
import VideoPlayer from './components/VideoPlayer';
import ChatPanel from './components/ChatPanel';
import './App.css';
import React from 'react';

const AgentDashboard = React.lazy(() => import('./components/AgentDashboard'));

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [framesReceived, setFramesReceived] = useState(0);
  const [fps, setFps] = useState(0);
  const [latency, setLatency] = useState(0);
  const [latestFrame, setLatestFrame] = useState(null);
  const [activeTrackId, setActiveTrackId] = useState(null);
  const [peopleCount, setPeopleCount] = useState(0);
  const [totalPeople, setTotalPeople] = useState(0);
  const [activityLevel, setActivityLevel] = useState('Low');
  const [showAgentDashboard, setShowAgentDashboard] = useState(false);
  
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
    
    if (data.total_people !== undefined) {
      setTotalPeople(data.total_people);
    }
    
    if (data.detections) {
      setPeopleCount(data.detections.length);
      if (data.detections.length >= 4) setActivityLevel('High');
      else if (data.detections.length >= 2) setActivityLevel('Medium');
      else setActivityLevel('Low');
    } else {
      setPeopleCount(0);
      setActivityLevel('Low');
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
            <button
              className="upload-button"
              onClick={() => setShowAgentDashboard(true)}
              style={{
                marginLeft: '0.5rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(236, 72, 153, 0.15))',
                color: '#d946ef',
                border: '1px solid rgba(217, 70, 239, 0.3)',
                padding: '0.4rem 0.8rem',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: '0 0 10px rgba(217, 70, 239, 0.1)'
              }}
            >
              <Cpu size={16} />
              Command Center
            </button>
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
      <div className="analytics-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', width: 'auto', minWidth: '400px', maxWidth: '450px' }}>
        
        {/* Chat Interface / Insight Dashboard */}
        <ChatPanel 
          onIntentChange={handleIntentChange} 
          peopleCount={peopleCount}
          activityLevel={activityLevel}
          totalPeople={totalPeople}
        />

      </div>
      
      {showAgentDashboard && (
        <React.Suspense fallback={<div>Loading Command Center...</div>}>
          <AgentDashboard 
            onClose={() => setShowAgentDashboard(false)} 
            latestFrame={latestFrame}
            totalPeople={totalPeople}
            runtimePeople={peopleCount}
          />
        </React.Suspense>
      )}
    </div>
  );
}

export default App;
