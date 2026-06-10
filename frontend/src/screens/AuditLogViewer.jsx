import React, { useState } from 'react';
import { FileText, Download, Lock } from 'lucide-react';

const MOCK_AUDIT_LOGS = Array.from({ length: 100 }).map((_, i) => ({
  id: `AL-${100000 - i}`,
  timestamp: new Date(Date.now() - i * 15000).toISOString().replace('T', ' ').substring(0, 23), // Include ms
  user: ['sysadmin_01', 'operator_j.doe', 'sysadmin_02', 'viewer_x'][Math.floor(Math.random() * 4)],
  action: [
    'Exported video chunk [CAM_01_SOUTH]',
    'Mutated AI trigger rule [Loitering Threshold -> 15s]',
    'Granted access level [operator] to [new_user]',
    'Initiated semantic search query',
    'Acknowledged critical alert [ALT-900]'
  ][Math.floor(Math.random() * 5)],
  ip: `10.0.1.${Math.floor(Math.random() * 255)}`
}));

export default function AuditLogViewer() {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredLogs = MOCK_AUDIT_LOGS.filter(log => 
    log.user.includes(searchTerm) || log.action.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '24px' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderBottom: '1px solid var(--border-color)', paddingBottom: '20px' }}>
        <div>
          <h1 className="text-heading" style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: 0 }}>
            <div style={{ width: 40, height: 40, background: 'var(--primary-subtle)', color: 'var(--primary)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <FileText size={20} />
            </div>
            Immutable Audit Logs
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: '8px 0 0 52px', fontSize: '0.9rem' }}>
            High-speed, cryptographic text grid logging every human interaction to the millisecond.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <input 
            type="text" 
            placeholder="Search operator or action..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ 
              background: 'rgba(0,0,0,0.4)', color: '#fff', 
              border: '1px solid var(--border-color)', padding: '8px 16px', 
              borderRadius: '6px', outline: 'none', fontFamily: 'var(--font-body)', width: 250 
            }}
          />
          <button style={{ background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--border-color)', padding: '8px 16px', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <Download size={16} /> Export CSV
          </button>
        </div>
      </div>

      {/* Grid */}
      <div className="glass-panel" style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <div style={{ overflowY: 'auto', flex: 1 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-surface-hover)', zIndex: 10 }}>
              <tr>
                <th style={{ padding: '12px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px' }}>TIMESTAMP (UTC)</th>
                <th style={{ padding: '12px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px' }}>OPERATOR ID</th>
                <th style={{ padding: '12px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px' }}>IP ADDRESS</th>
                <th style={{ padding: '12px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px' }}>MUTATION ACTION</th>
                <th style={{ padding: '12px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px' }}>HASH</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((log, idx) => (
                <tr key={log.id} style={{ borderBottom: '1px solid var(--border-color)', background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)' }}>
                  <td style={{ padding: '10px 24px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--primary)' }}>{log.timestamp}</td>
                  <td style={{ padding: '10px 24px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-primary)' }}>{log.user}</td>
                  <td style={{ padding: '10px 24px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{log.ip}</td>
                  <td style={{ padding: '10px 24px', fontSize: '0.85rem', color: 'var(--text-primary)' }}>{log.action}</td>
                  <td style={{ padding: '10px 24px' }}>
                    <Lock size={14} color="var(--success)" title="Signature Verified" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
