import { useState, useEffect, useRef } from 'react';
import React from 'react';

// Shell & Navigation
import LayoutShell from './layout/LayoutShell';

// Screens
import LiveMonitoring from './screens/LiveMonitoring';
import AgentCommandCenter from './screens/AgentCommandCenter';
import PlaceholderScreen from './screens/PlaceholderScreen';
import CameraManagement from './screens/CameraManagement';
import MultiCameraGrid from './screens/MultiCameraGrid';
import PlaybackCenter from './screens/PlaybackCenter';
import SpatialMapViewer from './screens/SpatialMapViewer';

// Deeper Intelligence Screens
import GlobalSearch from './screens/GlobalSearch';
import AlertCenter from './screens/AlertCenter';
import EventTimeline from './screens/EventTimeline';
import HeatmapAnalytics from './screens/HeatmapAnalytics';

// Administrative & Analytic Framework
import KPIDashboard from './screens/KPIDashboard';
import EnterpriseSecurity from './screens/EnterpriseSecurity';
import AuditLogViewer from './screens/AuditLogViewer';
import EvidenceExportConsole from './screens/EvidenceExportConsole';
import GlobalSettingsPanel from './screens/GlobalSettingsPanel';

// Insight Panels
import IntelligentInsightPanel from './components/IntelligentInsightPanel';
import './App.css';

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [framesReceived, setFramesReceived] = useState(0);
  const [fps, setFps] = useState(0);
  const [latency, setLatency] = useState(0);
  const [latestFrame, setLatestFrame] = useState(null);
  
  // Lifted global state for cross-component binding
  const [activeTrackId, setActiveTrackId] = useState(null);
  
  const [peopleCount, setPeopleCount] = useState(0);
  const [totalPeople, setTotalPeople] = useState(0);
  const [activityLevel, setActivityLevel] = useState('Low');
  
  // Navigation & Layout State
  const [activeScreen, setActiveScreen] = useState('live-monitoring');
  const [customRightPanel, setCustomRightPanel] = useState(null);
  
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
          if (data.action === 'highlight' && data.track_id !== undefined) {
             setActiveTrackId(data.track_id);
          }
        } else {
          handleFrameData(data);
        }
      };
      
      ws.onclose = () => {
        setIsConnected(false);
        setTimeout(connect, 2000);
      };
      
      ws.onerror = (err) => {
        console.error('WebSocket Error:', err);
        ws.close();
      };
      
      wsRef.current = ws;
    };

    connect();
    return () => { if (wsRef.current) wsRef.current.close(); };
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
    
    if (data.latency_ms !== undefined) setLatency(data.latency_ms);
    if (data.total_people !== undefined) setTotalPeople(data.total_people);
    
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

  const handleTargetSelect = (trackId) => {
    setActiveTrackId(trackId);
  };

  const handleNavigate = (screenId) => {
    setCustomRightPanel(null); // Clear custom panels on navigation
    setActiveScreen(screenId);
  };

  // ─── Render Engine ──────────────────────────────────────────────────
  const renderScreen = (screenId) => {
    switch (screenId) {
      // Live Operations & Infrastructure
      case 'live-monitoring':
        return (
          <LiveMonitoring
            isConnected={isConnected}
            latestFrame={latestFrame}
            activeTrackId={activeTrackId}
            onTrackSelect={handleTargetSelect}
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
            onTargetSelect={handleTargetSelect}
          />
        );
      case 'camera-mgmt':
        return <CameraManagement setRightPanelContent={setCustomRightPanel} />;
      case 'multi-camera':
        return <MultiCameraGrid />;
      case 'playback':
        return <PlaybackCenter />;
      case 'building-3d':
        return <SpatialMapViewer mode="building" />;
      case 'geo-view':
        return <SpatialMapViewer mode="geo" />;
        
      // Deeper Intelligence Screens
      case 'global-search':
        return <GlobalSearch />;
      case 'alert-center':
        return <AlertCenter />;
      case 'event-timeline':
      case 'object-tracking': 
        return <EventTimeline />;
      case 'heatmap':
        return <HeatmapAnalytics />;

      // Analytics & Settings Screens
      case 'kpi-dashboard':
        return <KPIDashboard mode="kpi" />;
      case 'deep-analytics':
        return <KPIDashboard mode="deep-analytics" />;
      case 'users':
        return <EnterpriseSecurity mode="users" />;
      case 'permissions':
        return <EnterpriseSecurity mode="permissions" />;
      case 'audit-logs':
        return <AuditLogViewer />;
      case 'export':
      case 'evidence':
        return <EvidenceExportConsole />;
      case 'settings':
        return <GlobalSettingsPanel />;
        
      default:
        return <PlaceholderScreen screenId={screenId} />;
    }
  };

  // The active right panel depends on what the current screen has requested
  const rightPanelContent = customRightPanel || (
    <IntelligentInsightPanel 
      peopleCount={peopleCount}
      totalPeople={totalPeople}
      activityLevel={activityLevel}
    />
  );

  return (
    <LayoutShell
      activeScreen={activeScreen}
      onNavigate={handleNavigate}
      renderScreen={renderScreen}
      rightPanelContent={rightPanelContent}
    />
  );
}

export default App;
