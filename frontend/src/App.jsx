import { useState, useEffect, useRef } from 'react';
import React from 'react';

// Shell & Navigation
import LayoutShell from './layout/LayoutShell';

// Screens
import LiveMonitoring from './screens/LiveMonitoring';
import AgentCommandCenter from './screens/AgentCommandCenter';
import PlaceholderScreen from './screens/PlaceholderScreen';

// Components
import ChatPanel from './components/ChatPanel';
import './App.css';

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
  
  // Navigation State (defaults to Screen 1)
  const [activeScreen, setActiveScreen] = useState('live-monitoring');
  
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

  // ─── Render Engine ──────────────────────────────────────────────────
  const renderScreen = (screenId) => {
    switch (screenId) {
      case 'live-monitoring':
        return (
          <LiveMonitoring
            isConnected={isConnected}
            latestFrame={latestFrame}
            activeTrackId={activeTrackId}
            fps={fps}
            latency={latency}
          />
        );
      case 'agent-command':
        return (
          <AgentCommandCenter
            latestFrame={latestFrame}
            totalPeople={totalPeople}
            runtimePeople={peopleCount}
          />
        );
      default:
        // Use placeholder for all other unbuilt screens
        return <PlaceholderScreen screenId={screenId} />;
    }
  };

  // ChatPanel serves as the global persistent right context drawer
  const rightPanelContent = (
    <div style={{ height: '100%', padding: '20px' }}>
      <ChatPanel 
        onIntentChange={handleIntentChange} 
        peopleCount={peopleCount}
        activityLevel={activityLevel}
        totalPeople={totalPeople}
      />
    </div>
  );

  return (
    <LayoutShell
      activeScreen={activeScreen}
      onNavigate={setActiveScreen}
      renderScreen={renderScreen}
      rightPanelContent={rightPanelContent}
    />
  );
}

export default App;
