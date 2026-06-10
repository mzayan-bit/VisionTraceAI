import React, { useState } from 'react';
import { Camera, Filter, ShieldAlert, CheckCircle2, AlertTriangle, Settings2, SlidersHorizontal, UserCog } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Mock Data
const MOCK_CAMERAS = Array.from({ length: 24 }).map((_, i) => {
  const isFaulty = Math.random() > 0.85;
  const isWarning = Math.random() > 0.7 && !isFaulty;
  
  let status = 'LIVE';
  if (isFaulty) status = 'OFFLINE';
  if (isWarning) status = 'WARNING';

  const group = i < 8 ? 'Perimeter Tier 1' : (i < 16 ? 'High-Risk Zone' : 'Internal Hallways');

  return {
    id: `CAM_${String(i + 1).padStart(3, '0')}`,
    host: `node-optics-${i + 1}.vt.local`,
    ip: `192.168.10.${100 + i}`,
    group: group,
    status: status,
    health: isFaulty ? 0 : (isWarning ? Math.floor(Math.random() * 40 + 40) : Math.floor(Math.random() * 10 + 90)),
    firmware: Math.random() > 0.8 ? 'v2.4.1 (Update Available)' : 'v2.5.0',
    calibration: isWarning ? 'Drift Detected' : 'Aligned',
  };
});

const FILTERS = ['All Active Nodes', 'Perimeter Tiers', 'High-Risk Zones', 'Hardware Fault Errors'];

// ─── Camera Calibration Panel (Right Drawer Content) ──────────────
export const CameraCalibrationPanel = ({ camera, onApplyCalibration }) => {
  const [isSaved, setIsSaved] = useState(false);

  const handleApply = () => {
    setIsSaved(true);
    if (onApplyCalibration) onApplyCalibration(camera.id);
    setTimeout(() => setIsSaved(false), 2000);
  };

  if (!camera) return null;

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px', height: '100%' }}>
      <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ margin: 0, fontFamily: 'var(--font-display)', fontSize: '1.25rem', color: 'var(--text-primary)' }}>
            {camera.id}
          </h3>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>
            {camera.ip} | {camera.host}
          </div>
        </div>
        {isSaved && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', fontWeight: 600 }}>
            <CheckCircle2 size={16} /> Saved!
          </motion.div>
        )}
      </div>

      {/* Sliders */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-accent)', fontSize: '0.85rem', fontWeight: 600 }}>
          <SlidersHorizontal size={16} /> LENS CALIBRATION
        </div>
        
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
            <span>Focal Length</span>
            <span style={{ fontFamily: 'var(--font-mono)' }}>35mm</span>
          </div>
          <input type="range" min="12" max="200" defaultValue="35" style={{ width: '100%', accentColor: 'var(--primary)' }} />
        </div>

        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>
            <span>Pan / Tilt Rotation</span>
            <span style={{ fontFamily: 'var(--font-mono)' }}>+14° / -5°</span>
          </div>
          <input type="range" min="-90" max="90" defaultValue="14" style={{ width: '100%', accentColor: 'var(--primary)' }} />
        </div>
      </div>

      {/* Access Rules */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--success)', fontSize: '0.85rem', fontWeight: 600 }}>
          <UserCog size={16} /> ROLE ACCESS PERMISSIONS
        </div>
        
        <label style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.9rem', color: 'var(--text-primary)' }}>
          <input type="checkbox" defaultChecked accentColor="var(--primary)" /> Global Admins
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.9rem', color: 'var(--text-primary)' }}>
          <input type="checkbox" defaultChecked accentColor="var(--primary)" /> Perimeter Security Operators
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.9rem', color: 'var(--text-primary)' }}>
          <input type="checkbox" accentColor="var(--primary)" /> Public Read-Only Viewers
        </label>
      </div>

      <div style={{ marginTop: 'auto', display: 'flex', gap: '12px' }}>
        <button onClick={handleApply} style={{ flex: 1, padding: '10px', background: 'var(--primary)', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 600 }}>
          Apply Calibration
        </button>
        <button style={{ padding: '10px', background: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px', cursor: 'pointer' }}>
          Reset
        </button>
      </div>
    </div>
  );
};


// ─── Main Screen Component ──────────────────────────────────────────
export default function CameraManagement({ setRightPanelContent }) {
  const [cameras, setCameras] = useState(MOCK_CAMERAS);
  const [activeFilter, setActiveFilter] = useState('All Active Nodes');
  const [selectedCamera, setSelectedCamera] = useState(null);

  // Filter Logic
  const filteredCameras = cameras.filter(cam => {
    if (activeFilter === 'Perimeter Tiers') return cam.group.includes('Perimeter');
    if (activeFilter === 'High-Risk Zones') return cam.group.includes('High-Risk');
    if (activeFilter === 'Hardware Fault Errors') return cam.status === 'OFFLINE' || cam.status === 'WARNING';
    return true;
  });

  const handleApplyCalibration = (camId) => {
    setCameras(prev => prev.map(c => c.id === camId ? { ...c, calibration: 'Aligned' } : c));
  };

  const handleRowClick = (cam) => {
    setSelectedCamera(cam.id);
    // When a row is clicked, we pass the Calibration Panel back up to App to render in the right drawer
    setRightPanelContent(<CameraCalibrationPanel camera={cam} onApplyCalibration={handleApplyCalibration} />);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '24px' }}>
      
      {/* Header & Filter Chips */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 className="text-heading" style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: 0 }}>
            <div style={{ width: 40, height: 40, background: 'var(--primary-subtle)', color: 'var(--primary)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Camera size={20} />
            </div>
            Camera Fleet Management
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: '8px 0 0 52px', fontSize: '0.9rem' }}>
            Total Managed Nodes: {MOCK_CAMERAS.length} | Online: {MOCK_CAMERAS.filter(c => c.status === 'LIVE').length}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          {FILTERS.map(filter => (
            <button
              key={filter}
              onClick={() => setActiveFilter(filter)}
              style={{
                background: activeFilter === filter ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                color: activeFilter === filter ? '#fff' : 'var(--text-secondary)',
                border: `1px solid ${activeFilter === filter ? 'var(--primary)' : 'var(--border-color)'}`,
                padding: '6px 16px',
                borderRadius: '20px',
                fontSize: '0.8rem',
                fontFamily: 'var(--font-body)',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all var(--transition-fast)'
              }}
            >
              {filter}
            </button>
          ))}
        </div>
      </div>

      {/* Data Grid */}
      <div className="glass-panel" style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <div style={{ overflowY: 'auto', flex: 1 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-surface-hover)', zIndex: 10 }}>
              <tr>
                <th style={{ padding: '16px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px', textTransform: 'uppercase' }}>Status</th>
                <th style={{ padding: '16px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px', textTransform: 'uppercase' }}>Node ID</th>
                <th style={{ padding: '16px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px', textTransform: 'uppercase' }}>IP Address</th>
                <th style={{ padding: '16px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px', textTransform: 'uppercase' }}>Allocation Group</th>
                <th style={{ padding: '16px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px', textTransform: 'uppercase' }}>Health</th>
                <th style={{ padding: '16px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px', textTransform: 'uppercase' }}>Firmware</th>
                <th style={{ padding: '16px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px', textTransform: 'uppercase' }}>Calibration</th>
              </tr>
            </thead>
            <tbody>
              {filteredCameras.map((cam, idx) => (
                <tr 
                  key={cam.id} 
                  onClick={() => handleRowClick(cam)}
                  style={{
                    borderBottom: '1px solid var(--border-color)',
                    background: selectedCamera === cam.id ? 'var(--primary-subtle)' : (idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)'),
                    cursor: 'pointer',
                    transition: 'background var(--transition-fast)'
                  }}
                  onMouseOver={(e) => { if (selectedCamera !== cam.id) e.currentTarget.style.background = 'var(--bg-surface-hover)' }}
                  onMouseOut={(e) => { if (selectedCamera !== cam.id) e.currentTarget.style.background = (idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)') }}
                >
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {cam.status === 'LIVE' && <CheckCircle2 size={16} color="var(--success)" />}
                      {cam.status === 'WARNING' && <AlertTriangle size={16} color="var(--warning)" />}
                      {cam.status === 'OFFLINE' && <ShieldAlert size={16} color="var(--danger)" />}
                      <span style={{ 
                        fontSize: '0.75rem', fontWeight: 700, fontFamily: 'var(--font-mono)',
                        color: cam.status === 'LIVE' ? 'var(--success)' : (cam.status === 'WARNING' ? 'var(--warning)' : 'var(--danger)')
                      }}>
                        {cam.status}
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '16px 24px', fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{cam.id}</td>
                  <td style={{ padding: '16px 24px', fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{cam.ip}</td>
                  <td style={{ padding: '16px 24px', fontSize: '0.85rem', color: 'var(--text-primary)' }}>{cam.group}</td>
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                      <div style={{ width: '40px', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                        <div style={{ width: `${cam.health}%`, height: '100%', background: cam.health > 80 ? 'var(--success)' : (cam.health > 0 ? 'var(--warning)' : 'var(--danger)') }} />
                      </div>
                      {cam.health}%
                    </div>
                  </td>
                  <td style={{ padding: '16px 24px', fontSize: '0.85rem', color: cam.firmware.includes('Update') ? 'var(--warning)' : 'var(--text-secondary)' }}>{cam.firmware}</td>
                  <td style={{ padding: '16px 24px', fontSize: '0.85rem', color: cam.calibration === 'Aligned' ? 'var(--text-secondary)' : 'var(--warning)' }}>{cam.calibration}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
