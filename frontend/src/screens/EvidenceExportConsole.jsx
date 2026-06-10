import React, { useState } from 'react';
import { Package, Download, FileText, CheckCircle2, ChevronRight, FileSpreadsheet, Archive } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function EvidenceExportConsole({ mode = 'export' }) {
  const [step, setStep] = useState(1);
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = () => {
    setIsExporting(true);
    setTimeout(() => {
      setIsExporting(false);
      setStep(3); // Success state
    }, 2000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '24px', maxWidth: '1000px', margin: '0 auto', width: '100%' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderBottom: '1px solid var(--border-color)', paddingBottom: '20px' }}>
        <div>
          <h1 className="text-heading" style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: 0 }}>
            <div style={{ width: 40, height: 40, background: 'var(--primary-subtle)', color: 'var(--primary)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {mode === 'export' ? <Download size={20} /> : <Package size={20} />}
            </div>
            {mode === 'export' ? 'Report Generation Workspace' : 'Evidence Bundle Assembly'}
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: '8px 0 0 52px', fontSize: '0.9rem' }}>
            {mode === 'export' ? 'Compile multi-format analytical files.' : 'Bind target embeddings, video clips, and AI write-ups into a signed zip container.'}
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
            <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: '12px', color: step >= s.id ? 'var(--primary)' : 'var(--text-muted)' }}>
              <div style={{ width: 24, height: 24, borderRadius: '50%', background: step >= s.id ? 'var(--primary-subtle)' : 'transparent', border: `1px solid ${step >= s.id ? 'var(--primary)' : 'var(--text-muted)'}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700 }}>
                {s.id}
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
                  <label style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)', borderRadius: '8px', cursor: 'pointer' }}>
                    <input type="checkbox" defaultChecked accentColor="var(--primary)" />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.9rem' }}>Verified Video Clip Block</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Track T_992 from CAM_01_SOUTH (15s)</div>
                    </div>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)', borderRadius: '8px', cursor: 'pointer' }}>
                    <input type="checkbox" defaultChecked accentColor="var(--primary)" />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.9rem' }}>Target Identity Embeddings</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Cropped profile frames and Vector UUIDs</div>
                    </div>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)', borderRadius: '8px', cursor: 'pointer' }}>
                    <input type="checkbox" defaultChecked accentColor="var(--primary)" />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.9rem' }}>Automated AI Case Write-up</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Agent synthesized reasoning logs</div>
                    </div>
                  </label>
                </div>
                <button onClick={() => setStep(2)} style={{ marginTop: '24px', background: 'var(--primary)', color: '#fff', border: 'none', padding: '10px 20px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
                  Continue <ChevronRight size={16} />
                </button>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h3 style={{ margin: '0 0 16px 0', color: 'var(--text-primary)' }}>Configure Output Format</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div style={{ padding: '20px', background: 'var(--primary-subtle)', border: '2px solid var(--primary)', borderRadius: '8px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', cursor: 'pointer' }}>
                    <Archive size={32} color="var(--primary)" />
                    <span style={{ fontWeight: 700, color: '#fff' }}>Secure ZIP Container</span>
                  </div>
                  <div style={{ padding: '20px', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-color)', borderRadius: '8px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', cursor: 'pointer' }}>
                    <FileText size={32} color="var(--text-muted)" />
                    <span style={{ fontWeight: 700, color: 'var(--text-secondary)' }}>PDF Executive Summary</span>
                  </div>
                </div>

                <div style={{ marginTop: '32px' }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Cryptographic Signature Key</label>
                  <input type="password" value="**************" readOnly style={{ width: '100%', padding: '12px', background: 'rgba(0,0,0,0.5)', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#fff', fontFamily: 'var(--font-mono)' }} />
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
                <p style={{ color: 'var(--text-secondary)' }}>Evidence bundle EVD-20260610-01.zip has been cryptographically signed.</p>
                
                <button onClick={() => setStep(1)} style={{ marginTop: '24px', background: 'var(--primary)', color: '#fff', border: 'none', padding: '10px 24px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
                  <Download size={16} /> Download Archive
                </button>
              </motion.div>
            )}
          </AnimatePresence>

        </div>
      </div>
    </div>
  );
}
