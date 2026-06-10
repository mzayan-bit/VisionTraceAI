import React, { useState } from 'react';
import { Settings, Server, Brain, Clock, ShieldAlert, Palette, Key, Save } from 'lucide-react';
import { useTheme } from '../themes/ThemeProvider';
import { themeList } from '../themes/themes';

const TABS = [
  { id: 'appearance', label: 'Appearance & Theme', icon: Palette },
  { id: 'ai', label: 'AI Inference Models', icon: Brain },
  { id: 'alerts', label: 'System Alert Rules', icon: ShieldAlert },
  { id: 'retention', label: 'Storage Retention', icon: Clock },
  { id: 'api', label: 'External API Keys', icon: Key },
];

export default function GlobalSettingsPanel() {
  const [activeTab, setActiveTab] = useState('appearance');
  const { themeName, setTheme } = useTheme();

  // Mock Settings State
  const [retentionDays, setRetentionDays] = useState(30);
  const [confidenceThreshold, setConfidenceThreshold] = useState(85);
  const [visionModel, setVisionModel] = useState('yolo11-tensorrt');
  const [llmEngine, setLlmEngine] = useState('gemini-1.5-pro');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '24px' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderBottom: '1px solid var(--border-color)', paddingBottom: '20px' }}>
        <div>
          <h1 className="text-heading" style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: 0 }}>
            <div style={{ width: 40, height: 40, background: 'var(--primary-subtle)', color: 'var(--primary)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Settings size={20} />
            </div>
            Global System Settings
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: '8px 0 0 52px', fontSize: '0.9rem' }}>
            Core administrative configuration for VisionTraceAI operational framework.
          </p>
        </div>
        
        <button style={{ background: 'var(--primary)', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: 600 }}>
          <Save size={16} /> Save Configuration
        </button>
      </div>

      <div style={{ display: 'flex', gap: '32px', flex: 1, overflow: 'hidden' }}>
        
        {/* Settings Sidebar */}
        <div style={{ width: '220px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {TABS.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '12px',
                  width: '100%', padding: '12px 16px',
                  background: isActive ? 'var(--primary-subtle)' : 'transparent',
                  color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                  border: 'none',
                  borderLeft: `3px solid ${isActive ? 'var(--primary)' : 'transparent'}`,
                  borderRadius: '0 6px 6px 0',
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: '0.9rem',
                  transition: 'all var(--transition-fast)'
                }}
              >
                <Icon size={18} /> {tab.label}
              </button>
            );
          })}
        </div>

        {/* Settings Form Area */}
        <div className="glass-panel" style={{ flex: 1, padding: '32px', overflowY: 'auto' }}>
          
          {activeTab === 'appearance' && (
            <div>
              <h3 style={{ margin: '0 0 24px 0', color: 'var(--text-primary)' }}>System Theme Engine</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' }}>
                {themeList.map(t => (
                  <div 
                    key={t.id}
                    onClick={() => setTheme(t.id)}
                    style={{
                      padding: '16px',
                      border: `2px solid ${themeName === t.id ? 'var(--primary)' : 'var(--border-color)'}`,
                      borderRadius: '8px',
                      background: 'rgba(255,255,255,0.02)',
                      cursor: 'pointer',
                      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px',
                      transition: 'all var(--transition-fast)'
                    }}
                  >
                    <div style={{ width: 40, height: 40, borderRadius: '50%', background: t.swatch, boxShadow: themeName === t.id ? `0 0 16px ${t.swatch}` : 'none' }} />
                    <span style={{ fontWeight: 600, color: themeName === t.id ? 'var(--primary)' : 'var(--text-primary)' }}>{t.label}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'ai' && (
            <div>
              <h3 style={{ margin: '0 0 24px 0', color: 'var(--text-primary)' }}>AI Vision & Reasoning Inference</h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>Vision Pipeline Model (Edge Compute)</label>
                  <select value={visionModel} onChange={(e) => setVisionModel(e.target.value)} style={{ width: '100%', maxWidth: '400px', padding: '12px', background: 'rgba(0,0,0,0.5)', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#fff', outline: 'none' }}>
                    <option value="yolo11-tensorrt">YOLO11-TensorRT (Optimized)</option>
                    <option value="yolo11x">YOLO11x (Maximum Accuracy)</option>
                    <option value="custom">Custom Compiled ONNX</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>Reasoning Agent Engine</label>
                  <select value={llmEngine} onChange={(e) => setLlmEngine(e.target.value)} style={{ width: '100%', maxWidth: '400px', padding: '12px', background: 'rgba(0,0,0,0.5)', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#fff', outline: 'none' }}>
                    <option value="gemini-1.5-pro">Google Gemini 1.5 Pro</option>
                    <option value="gemini-1.5-flash">Google Gemini 1.5 Flash (Fast Routing)</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>Target Confidence Threshold: {confidenceThreshold}%</label>
                  <input type="range" min="50" max="99" value={confidenceThreshold} onChange={(e) => setConfidenceThreshold(e.target.value)} style={{ width: '100%', maxWidth: '400px', accentColor: 'var(--primary)' }} />
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '8px' }}>Detections below this threshold are discarded from the Qdrant vector index.</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'retention' && (
            <div>
              <h3 style={{ margin: '0 0 24px 0', color: 'var(--text-primary)' }}>Storage Asset Retention Rules</h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>Raw Video Expiration (Days)</label>
                  <input type="number" min="1" max="365" value={retentionDays} onChange={(e) => setRetentionDays(Math.max(1, parseInt(e.target.value) || 1))} style={{ width: '100%', maxWidth: '200px', padding: '12px', background: 'rgba(0,0,0,0.5)', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#fff', outline: 'none', fontFamily: 'var(--font-mono)' }} />
                </div>

                <label style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}>
                  <input type="checkbox" defaultChecked accentColor="var(--primary)" style={{ width: 18, height: 18 }} />
                  <div>
                    <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.9rem' }}>Permanent Vector Storage</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Retain visual embeddings in Qdrant even after raw video expires.</div>
                  </div>
                </label>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
