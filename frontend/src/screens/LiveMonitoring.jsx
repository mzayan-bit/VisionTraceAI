import React, { useRef, useState } from 'react';
import { Camera, Upload } from 'lucide-react';
import VideoPlayer from '../components/VideoPlayer';

export default function LiveMonitoring({ 
  isConnected, 
  latestFrame, 
  activeTrackId, 
  fps, 
  latency 
}) {
  const fileInputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);

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
      alert('Video uploaded successfully! The VisionTrace engine is now processing it in the background.');
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload video. Please ensure the backend is running.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="glass-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{
        padding: '1.25rem 1.5rem',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Camera className="text-accent" size={24} style={{ color: 'var(--text-accent)' }} />
          <h2 style={{ 
            fontFamily: 'var(--font-display)',
            fontSize: '1.25rem',
            fontWeight: 600,
            color: 'var(--text-primary)'
          }}>Live Camera Feed</h2>
          {isConnected && (
            <div style={{
              width: 10, height: 10, borderRadius: '50%',
              backgroundColor: 'var(--danger)',
              boxShadow: '0 0 10px var(--danger)',
            }} />
          )}
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <input 
            type="file" 
            accept="video/*" 
            ref={fileInputRef} 
            style={{ display: 'none' }} 
            onChange={handleFileUpload} 
          />
          <button 
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: 'var(--primary-subtle)',
              color: 'var(--primary)',
              border: '1px solid var(--border-accent)',
              padding: '0.5rem 1rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: isUploading ? 'not-allowed' : 'pointer',
              transition: 'all var(--transition-fast)',
            }}
            onMouseOver={(e) => {
              if (!isUploading) {
                e.currentTarget.style.background = 'var(--primary)';
                e.currentTarget.style.color = '#fff';
              }
            }}
            onMouseOut={(e) => {
              if (!isUploading) {
                e.currentTarget.style.background = 'var(--primary-subtle)';
                e.currentTarget.style.color = 'var(--primary)';
              }
            }}
          >
            <Upload size={16} />
            {isUploading ? 'Processing...' : 'Upload Video'}
          </button>
        </div>
      </div>

      {/* Video Area */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden', borderBottomLeftRadius: 'var(--radius-lg)', borderBottomRightRadius: 'var(--radius-lg)' }}>
        <VideoPlayer 
          latestFrame={latestFrame} 
          isConnected={isConnected} 
          activeTrackId={activeTrackId} 
          fps={fps}
          latency={latency}
        />
      </div>
    </div>
  );
}
