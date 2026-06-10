import React, { useState, useEffect } from 'react';
import { Bell, ShieldAlert, AlertOctagon, CheckCircle2, Crosshair, Users, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const MOCK_ALERTS = [
  { id: 'ALT-901', type: 'Ingress Violation', time: 'Just now', priority: 'critical', loc: 'CAM_01_SOUTH', icon: ShieldAlert },
  { id: 'ALT-900', type: 'Physical Altercation', time: '2m ago', priority: 'critical', loc: 'CAM_03_LOBBY', icon: AlertOctagon },
  { id: 'ALT-899', type: 'Extended Loitering', time: '15m ago', priority: 'high', loc: 'CAM_01_SOUTH', icon: Activity },
  { id: 'ALT-898', type: 'Crowd Surge Anomaly', time: '1h ago', priority: 'high', loc: 'CAM_05_MAIN', icon: Users },
];

export default function AlertCenter() {
  const [alerts, setAlerts] = useState([]);
  
  // Simulate alerts coming in real-time
  useEffect(() => {
    // Start with 3
    setAlerts(MOCK_ALERTS.slice(1));
    
    // Slide in the top critical alert after 1.5s
    const timer = setTimeout(() => {
      setAlerts(MOCK_ALERTS);
    }, 1500);
    
    return () => clearTimeout(timer);
  }, []);

  const dismissAlert = (id) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '24px', maxWidth: '1000px', margin: '0 auto', width: '100%' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderBottom: '1px solid var(--border-color)', paddingBottom: '20px' }}>
        <div>
          <h1 className="text-heading" style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: 0, color: 'var(--danger)' }}>
            <div style={{ width: 40, height: 40, background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Bell size={20} />
            </div>
            High-Priority Alert Hub
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: '8px 0 0 52px', fontSize: '0.9rem' }}>
            System autonomously monitoring for lethal threats, perimeter breaches, and anomalies.
          </p>
        </div>
        
        <button style={{ background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}>
          Mark All Acknowledged
        </button>
      </div>

      {/* Alert Stack */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px', paddingRight: '8px' }}>
        <AnimatePresence>
          {alerts.map((alert) => {
            const Icon = alert.icon;
            const isCritical = alert.priority === 'critical';
            
            return (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, x: 100, scale: 0.95 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: -100, scale: 0.95 }}
                transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                className="glass-panel"
                style={{
                  display: 'flex',
                  gap: '20px',
                  padding: '20px',
                  background: isCritical ? 'rgba(239, 68, 68, 0.05)' : 'var(--bg-surface)',
                  border: `1px solid ${isCritical ? 'rgba(239, 68, 68, 0.3)' : 'var(--border-color)'}`,
                  position: 'relative',
                  overflow: 'hidden'
                }}
              >
                {/* Radial Glow for Critical */}
                {isCritical && (
                  <motion.div 
                    animate={{ opacity: [0.1, 0.3, 0.1] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                    style={{ position: 'absolute', top: 0, right: 0, width: 200, height: 200, background: 'radial-gradient(circle, rgba(239, 68, 68, 0.4) 0%, transparent 70%)', pointerEvents: 'none' }}
                  />
                )}

                {/* Thumbnail Snapshot */}
                <div style={{ width: 160, height: 100, background: 'linear-gradient(45deg, #111, #222)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
                  <Crosshair size={32} color="rgba(255,255,255,0.1)" />
                  <div style={{ position: 'absolute', bottom: 8, left: 8, background: 'rgba(0,0,0,0.8)', padding: '2px 6px', fontSize: '0.6rem', color: '#fff', fontFamily: 'var(--font-mono)', borderRadius: '4px' }}>{alert.loc}</div>
                </div>

                {/* Info */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <Icon size={20} color={isCritical ? 'var(--danger)' : 'var(--warning)'} />
                      <h3 style={{ margin: 0, color: '#fff', fontSize: '1.2rem' }}>{alert.type}</h3>
                      <div style={{ 
                        padding: '2px 8px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', fontFamily: 'var(--font-mono)',
                        background: isCritical ? 'var(--danger)' : 'var(--warning)', color: isCritical ? '#fff' : '#000'
                      }}>
                        {alert.priority}
                      </div>
                    </div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>{alert.time}</div>
                  </div>
                  
                  <div style={{ marginTop: '12px', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    System triggered automated threshold break. Subject matched against ingress restriction vectors.
                  </div>

                  {/* Actions */}
                  <div style={{ display: 'flex', gap: '12px', marginTop: 'auto', paddingTop: '16px' }}>
                    <button 
                      onClick={() => dismissAlert(alert.id)}
                      style={{ background: 'var(--success)', color: '#000', border: 'none', padding: '8px 16px', borderRadius: '6px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
                    >
                      <CheckCircle2 size={16} /> Acknowledge Alert
                    </button>
                    <button style={{ background: 'transparent', color: '#fff', border: '1px solid var(--border-color)', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}>
                      Dispatch Unit
                    </button>
                    <button style={{ background: 'var(--primary-subtle)', color: 'var(--primary)', border: '1px solid var(--primary)', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}>
                      Trigger Investigation Agent
                    </button>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

    </div>
  );
}
