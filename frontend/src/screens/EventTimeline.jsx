import React, { useState } from 'react';
import { Clock, Filter, Download, Server, Cpu } from 'lucide-react';

const MOCK_EVENTS = Array.from({ length: 50 }).map((_, i) => ({
  id: `EVT-${10000 - i}`,
  timestamp: new Date(Date.now() - i * 60000).toISOString().replace('T', ' ').substring(0, 19),
  level: Math.random() > 0.8 ? 'WARN' : (Math.random() > 0.95 ? 'ERROR' : 'INFO'),
  source: ['Vision Engine', 'Kafka Stream', 'Qdrant Vector DB', 'Agent Router'][Math.floor(Math.random() * 4)],
  message: [
    'Successfully processed frame batch [3402]',
    'Vector embedding cached in Redis layer',
    'Detected latency spike in decode pipeline',
    'Agent successfully parsed semantic intention',
    'Reconnecting to stream CAM_01_SOUTH'
  ][Math.floor(Math.random() * 5)]
}));

export default function EventTimeline() {
  const [filterLevel, setFilterLevel] = useState('ALL');

  const filteredEvents = MOCK_EVENTS.filter(ev => filterLevel === 'ALL' || ev.level === filterLevel);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '24px' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 className="text-heading" style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: 0 }}>
            <div style={{ width: 40, height: 40, background: 'var(--primary-subtle)', color: 'var(--primary)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Clock size={20} />
            </div>
            System Event Timeline
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: '8px 0 0 52px', fontSize: '0.9rem' }}>
            Stateful chronological logging grid for all core system services.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <select 
            value={filterLevel} 
            onChange={(e) => setFilterLevel(e.target.value)}
            style={{ 
              background: 'rgba(255,255,255,0.05)', color: '#fff', 
              border: '1px solid var(--border-color)', padding: '8px 16px', 
              borderRadius: '6px', outline: 'none' 
            }}
          >
            <option value="ALL">All Levels</option>
            <option value="INFO">INFO</option>
            <option value="WARN">WARN</option>
            <option value="ERROR">ERROR</option>
          </select>
          <button style={{ background: 'var(--primary)', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <Download size={16} /> Export Logs
          </button>
        </div>
      </div>

      {/* Grid */}
      <div className="glass-panel" style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <div style={{ overflowY: 'auto', flex: 1 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-surface-hover)', zIndex: 10 }}>
              <tr>
                <th style={{ padding: '16px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px' }}>TIMESTAMP (UTC)</th>
                <th style={{ padding: '16px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px' }}>LEVEL</th>
                <th style={{ padding: '16px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px' }}>SOURCE MODULE</th>
                <th style={{ padding: '16px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px' }}>EVENT MESSAGE</th>
              </tr>
            </thead>
            <tbody>
              {filteredEvents.map((ev, idx) => (
                <tr key={ev.id} style={{ borderBottom: '1px solid var(--border-color)', background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)' }}>
                  <td style={{ padding: '12px 24px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{ev.timestamp}</td>
                  <td style={{ padding: '12px 24px' }}>
                    <span style={{ 
                      fontFamily: 'var(--font-mono)', fontSize: '0.75rem', fontWeight: 700, padding: '2px 6px', borderRadius: '4px',
                      background: ev.level === 'ERROR' ? 'rgba(239, 68, 68, 0.1)' : (ev.level === 'WARN' ? 'rgba(245, 158, 11, 0.1)' : 'transparent'),
                      color: ev.level === 'ERROR' ? 'var(--danger)' : (ev.level === 'WARN' ? 'var(--warning)' : 'var(--text-muted)')
                    }}>
                      {ev.level}
                    </span>
                  </td>
                  <td style={{ padding: '12px 24px', fontSize: '0.85rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {ev.source.includes('Agent') ? <Cpu size={14} color="var(--primary)" /> : <Server size={14} color="var(--text-secondary)" />}
                    {ev.source}
                  </td>
                  <td style={{ padding: '12px 24px', fontSize: '0.85rem', color: ev.level === 'ERROR' ? 'var(--danger)' : 'var(--text-primary)' }}>{ev.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
