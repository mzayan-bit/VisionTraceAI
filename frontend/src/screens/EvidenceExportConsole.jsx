import React, { useState } from 'react';
import { Package, Download, FileText, CheckCircle2, ChevronRight, Archive } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// ─── Browser File Download Utility ────────────────────────────────
function triggerBlobDownload(filename, content, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function generateMockEvidence() {
  const timestamp = new Date().toISOString();
  return JSON.stringify({
    package_id: `EVD-${Date.now()}`,
    generated_at: timestamp,
    signed_by: 'sysadmin_01',
    chain_of_custody: 'Verified — SHA-256',
    assets: [
      { type: 'video_clip', camera: 'CAM_01_SOUTH', duration_s: 15, track_id: 'T_992' },
      { type: 'embedding_vectors', count: 128, model: 'SigLIP-512d' },
      { type: 'ai_case_writeup', agent: 'VisionTrace Reasoning Agent v2', tokens: 1024 },
    ],
    timeline_events: [
      { time: '14:32:04', event: 'Target entered perimeter zone' },
      { time: '14:32:19', event: 'Loitering threshold exceeded (15s)' },
      { time: '14:33:01', event: 'Target exited field of view' },
    ],
  }, null, 2);
}

function generateMockPDF() {
  const timestamp = new Date().toISOString();
  return `VISIONTRACE — EXECUTIVE INCIDENT SUMMARY
============================================
Generated: ${timestamp}
Classification: CONFIDENTIAL
Signed: sysadmin_01 (SHA-256 Verified)

INCIDENT OVERVIEW
-----------------
A tracked individual (Track ID: T_992) was observed entering
the southern perimeter zone via CAM_01_SOUTH at 14:32:04 UTC.

The individual exhibited loitering behavior for 15+ seconds,
triggering automated alert ALT-900. The AI reasoning agent
synthesized 128 SigLIP-512d embedding vectors with 98% match
confidence against the watchlist.

TIMELINE
--------
14:32:04  Target entered perimeter zone
14:32:19  Loitering threshold exceeded (15s)
14:33:01  Target exited field of view

EVIDENCE MANIFEST
-----------------
- Verified Video Clip Block (15s, CAM_01_SOUTH)
- Target Identity Embeddings (128 vectors, SigLIP-512d)
- Automated AI Case Write-up (1024 tokens)

END OF REPORT
`;
}

export default function EvidenceExportConsole() {
  const [step, setStep] = useState(1);
  const [isExporting, setIsExporting] = useState(false);
  const [selectedFormats, setSelectedFormats] = useState({ zip: true, pdf: false });

  // Asset selection state
  const [assets, setAssets] = useState([
    { id: 'video', label: 'Verified Video Clip Block', desc: 'Track T_992 from CAM_01_SOUTH (15s)', checked: true },
    { id: 'embeddings', label: 'Target Identity Embeddings', desc: 'Cropped profile frames and Vector UUIDs', checked: true },
    { id: 'writeup', label: 'Automated AI Case Write-up', desc: 'Agent synthesized reasoning logs', checked: true },
  ]);

  const toggleAsset = (id) => {
    setAssets(prev => prev.map(a => a.id === id ? { ...a, checked: !a.checked } : a));
  };

  const toggleFormat = (format) => {
    setSelectedFormats(prev => ({ ...prev, [format]: !prev[format] }));
  };

  const handleExport = () => {
    setIsExporting(true);
    setTimeout(() => {
      setIsExporting(false);
      setStep(3);
    }, 2000);
  };

  const handleDownload = () => {
    const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    if (selectedFormats.zip) {
      triggerBlobDownload(
        `Evidence_EVD-${dateStr}.zip`,
        generateMockEvidence(),
        'application/zip'
      );
    }
    if (selectedFormats.pdf) {
      triggerBlobDownload(
        `Executive_Summary_${dateStr}.pdf`,
        generateMockPDF(),
        'application/pdf'
      );
    }
    // If neither selected, download zip by default
    if (!selectedFormats.zip && !selectedFormats.pdf) {
      triggerBlobDownload(
        `Evidence_EVD-${dateStr}.zip`,
        generateMockEvidence(),
        'application/zip'
      );
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '24px', maxWidth: '1000px', margin: '0 auto', width: '100%' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderBottom: '1px solid var(--border-color)', paddingBottom: '20px' }}>
        <div>
          <h1 className="text-heading" style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: 0 }}>
            <div style={{ width: 40, height: 40, background: 'var(--primary-subtle)', color: 'var(--primary)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Package size={20} />
            </div>
            Export & Evidence Hub
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: '8px 0 0 52px', fontSize: '0.9rem' }}>
            Compile multi-format analytical files and bind signed evidence containers.
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '24px', flex: 1 }}>
        
        {/* Workflow Sidebar */}
        <div style={{ width: '250px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {[
            { id: 1, label: 'Select Assets' },
            { id: 2, label: 'Configure Format' },
            { id: 3, label: 'Finalize & Sign' }
          ].map(s => (
            <div 
              key={s.id} 
              onClick={() => { if (s.id < step || s.id === step) setStep(s.id); }}
              style={{ display: 'flex', alignItems: 'center', gap: '12px', color: step >= s.id ? 'var(--primary)' : 'var(--text-muted)', cursor: step >= s.id ? 'pointer' : 'default' }}
            >
              <div style={{ width: 24, height: 24, borderRadius: '50%', background: step >= s.id ? 'var(--primary-subtle)' : 'transparent', border: `1px solid ${step >= s.id ? 'var(--primary)' : 'var(--text-muted)'}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700 }}>
                {step > s.id ? <CheckCircle2 size={14} /> : s.id}
              </div>
              <span style={{ fontWeight: step === s.id ? 700 : 500, fontSize: '0.9rem' }}>{s.label}</span>
            </div>
          ))}
        </div>

        {/* Main Content Area */}
        <div className="glass-panel" style={{ flex: 1, padding: '32px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div key="step1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h3 style={{ margin: '0 0 16px 0', color: 'var(--text-primary)' }}>Select Assets to Bind</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {assets.map(asset => (
                    <label 
                      key={asset.id}
                      style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', background: asset.checked ? 'rgba(56, 189, 248, 0.04)' : 'rgba(255,255,255,0.02)', border: `1px solid ${asset.checked ? 'var(--primary)' : 'var(--border-color)'}`, borderRadius: '8px', cursor: 'pointer', transition: 'all var(--transition-fast)' }}
                    >
                      <input 
                        type="checkbox" 
                        checked={asset.checked}
                        onChange={() => toggleAsset(asset.id)}
                        style={{ accentColor: 'var(--primary)', width: 18, height: 18 }} 
                      />
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.9rem' }}>{asset.label}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{asset.desc}</div>
                      </div>
                    </label>
                  ))}
                </div>
                <button onClick={() => setStep(2)} style={{ marginTop: '24px', background: 'var(--primary)', color: '#fff', border: 'none', padding: '10px 20px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
                  Continue <ChevronRight size={16} />
                </button>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h3 style={{ margin: '0 0 16px 0', color: 'var(--text-primary)' }}>Configure Output Format</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '20px' }}>Select one or more output formats for your evidence package.</p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div 
                    onClick={() => toggleFormat('zip')}
                    style={{ 
                      padding: '20px', 
                      background: selectedFormats.zip ? 'var(--primary-subtle)' : 'rgba(255,255,255,0.02)', 
                      border: `2px solid ${selectedFormats.zip ? 'var(--primary)' : 'var(--border-color)'}`, 
                      borderRadius: '8px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', cursor: 'pointer',
                      transition: 'all var(--transition-fast)',
                    }}
                  >
                    <Archive size={32} color={selectedFormats.zip ? 'var(--primary)' : 'var(--text-muted)'} />
                    <span style={{ fontWeight: 700, color: selectedFormats.zip ? '#fff' : 'var(--text-secondary)' }}>Secure ZIP Container</span>
                    {selectedFormats.zip && <CheckCircle2 size={16} color="var(--primary)" />}
                  </div>
                  <div 
                    onClick={() => toggleFormat('pdf')}
                    style={{ 
                      padding: '20px', 
                      background: selectedFormats.pdf ? 'var(--primary-subtle)' : 'rgba(255,255,255,0.02)', 
                      border: `2px solid ${selectedFormats.pdf ? 'var(--primary)' : 'var(--border-color)'}`, 
                      borderRadius: '8px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', cursor: 'pointer',
                      transition: 'all var(--transition-fast)',
                    }}
                  >
                    <FileText size={32} color={selectedFormats.pdf ? 'var(--primary)' : 'var(--text-muted)'} />
                    <span style={{ fontWeight: 700, color: selectedFormats.pdf ? '#fff' : 'var(--text-secondary)' }}>PDF Executive Summary</span>
                    {selectedFormats.pdf && <CheckCircle2 size={16} color="var(--primary)" />}
                  </div>
                </div>

                <div style={{ marginTop: '32px' }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Cryptographic Signature Key</label>
                  <input type="password" defaultValue="**************" style={{ width: '100%', padding: '12px', background: 'rgba(0,0,0,0.5)', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#fff', fontFamily: 'var(--font-mono)' }} />
                </div>

                <div style={{ display: 'flex', gap: '12px', marginTop: '32px' }}>
                  <button onClick={() => setStep(1)} style={{ background: 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--border-color)', padding: '10px 20px', borderRadius: '6px', cursor: 'pointer' }}>
                    Back
                  </button>
                  <button onClick={handleExport} disabled={isExporting} style={{ background: 'var(--success)', color: '#000', border: 'none', padding: '10px 20px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
                    {isExporting ? 'Compiling Package...' : 'Generate & Sign Package'}
                  </button>
                </div>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div key="step3" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px' }}>
                <div style={{ width: 80, height: 80, borderRadius: '50%', background: 'rgba(16, 185, 129, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <CheckCircle2 size={40} color="var(--success)" />
                </div>
                <h2 style={{ margin: 0, color: '#fff' }}>Package Generated Successfully</h2>
                <p style={{ color: 'var(--text-secondary)' }}>
                  Evidence bundle EVD-{new Date().toISOString().slice(0,10).replace(/-/g,'')}.zip has been cryptographically signed.
                </p>
                
                <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                  <button 
                    onClick={handleDownload} 
                    style={{ background: 'var(--primary)', color: '#fff', border: 'none', padding: '10px 24px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}
                  >
                    <Download size={16} /> Download Archive
                  </button>
                  <button 
                    onClick={() => setStep(1)} 
                    style={{ background: 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--border-color)', padding: '10px 24px', borderRadius: '6px', cursor: 'pointer' }}
                  >
                    New Package
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

        </div>
      </div>
    </div>
  );
}
