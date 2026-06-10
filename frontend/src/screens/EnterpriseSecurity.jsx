import React, { useState } from 'react';
import { Shield, UserCog, Lock, Save, Plus } from 'lucide-react';

const CAPABILITIES = [
  { id: 'view_live', label: 'Access Live Camera Feeds', desc: 'Can view real-time operations.' },
  { id: 'view_history', label: 'Access Historical Playback', desc: 'Can scrub past timelines.' },
  { id: 'export_data', label: 'Request Vector/Video Export', desc: 'Can generate evidence packages.' },
  { id: 'mutate_rules', label: 'Mutate AI Alert Rule Sets', desc: 'Can change trigger thresholds.' },
  { id: 'view_logs', label: 'View Global System Audit Logs', desc: 'Can inspect security histories.' },
  { id: 'manage_users', label: 'Manage Roles & Users', desc: 'Can allocate clearance levels.' },
];

const ROLES = [
  { id: 'sysadmin', label: 'System Administrator' },
  { id: 'operator', label: 'Monitoring Room Operator' },
  { id: 'viewer', label: 'Incident Field Viewer' },
];

const DEFAULT_PERMISSIONS = {
  sysadmin: ['view_live', 'view_history', 'export_data', 'mutate_rules', 'view_logs', 'manage_users'],
  operator: ['view_live', 'view_history', 'export_data'],
  viewer: ['view_live'],
};

export default function EnterpriseSecurity({ mode = 'users' }) {
  const [permissions, setPermissions] = useState(DEFAULT_PERMISSIONS);

  const togglePermission = (roleId, capId) => {
    setPermissions(prev => {
      const rolePerms = prev[roleId];
      if (rolePerms.includes(capId)) {
        return { ...prev, [roleId]: rolePerms.filter(id => id !== capId) };
      } else {
        return { ...prev, [roleId]: [...rolePerms, capId] };
      }
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '24px' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderBottom: '1px solid var(--border-color)', paddingBottom: '20px' }}>
        <div>
          <h1 className="text-heading" style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: 0 }}>
            <div style={{ width: 40, height: 40, background: 'var(--primary-subtle)', color: 'var(--primary)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {mode === 'users' ? <UserCog size={20} /> : <Lock size={20} />}
            </div>
            {mode === 'users' ? 'User Management' : 'Role Access & Permissions'}
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: '8px 0 0 52px', fontSize: '0.9rem' }}>
            Enterprise security gateway allocating operational clearance levels.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          {mode === 'users' && (
            <button style={{ background: 'var(--primary)', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: 600 }}>
              <Plus size={16} /> Add User
            </button>
          )}
          {mode === 'permissions' && (
            <button style={{ background: 'var(--primary)', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: 600 }}>
              <Save size={16} /> Save Security Matrix
            </button>
          )}
        </div>
      </div>

      {mode === 'permissions' ? (
        <div className="glass-panel" style={{ flex: 1, overflowY: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-surface-hover)', zIndex: 10 }}>
              <tr>
                <th style={{ padding: '20px 24px', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px', textTransform: 'uppercase', width: '40%' }}>System Capability Gate</th>
                {ROLES.map(role => (
                  <th key={role.id} style={{ padding: '20px 24px', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)', textAlign: 'center' }}>{role.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {CAPABILITIES.map((cap, idx) => (
                <tr key={cap.id} style={{ borderBottom: '1px solid var(--border-color)', background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)' }}>
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>{cap.label}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>{cap.desc}</div>
                  </td>
                  {ROLES.map(role => {
                    const isChecked = permissions[role.id].includes(cap.id);
                    return (
                      <td key={role.id} style={{ padding: '16px 24px', textAlign: 'center' }}>
                        <div 
                          onClick={() => togglePermission(role.id, cap.id)}
                          style={{
                            width: 24, height: 24, margin: '0 auto',
                            background: isChecked ? 'var(--primary)' : 'transparent',
                            border: `2px solid ${isChecked ? 'var(--primary)' : 'var(--border-color)'}`,
                            borderRadius: '6px',
                            cursor: 'pointer',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            transition: 'all var(--transition-fast)'
                          }}
                        >
                          {isChecked && <Shield size={14} color="#fff" />}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
          User Directory interface goes here. (See Permissions mode for the security matrix).
        </div>
      )}

    </div>
  );
}
