import React, { useState } from 'react';
import { Shield, UserCog, Lock, Save, Plus, X, Trash2, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

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

const INITIAL_USERS = [
  { id: 1, name: 'sysadmin_01', role: 'sysadmin', email: 'admin@visiontrace.io', lastActive: '2 min ago' },
  { id: 2, name: 'operator_j.doe', role: 'operator', email: 'j.doe@facility.net', lastActive: '15 min ago' },
  { id: 3, name: 'viewer_x', role: 'viewer', email: 'viewer@external.org', lastActive: '1 hour ago' },
];

const DEFAULT_PERMISSIONS = {
  sysadmin: ['view_live', 'view_history', 'export_data', 'mutate_rules', 'view_logs', 'manage_users'],
  operator: ['view_live', 'view_history', 'export_data'],
  viewer: ['view_live'],
};

export default function EnterpriseSecurity({ mode = 'users' }) {
  const [permissions, setPermissions] = useState(DEFAULT_PERMISSIONS);
  const [users, setUsers] = useState(INITIAL_USERS);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newUser, setNewUser] = useState({ name: '', role: 'operator', email: '' });
  const [saveFlash, setSaveFlash] = useState(false);

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

  const handleAddUser = () => {
    if (!newUser.name.trim()) return;
    const user = {
      id: Date.now(),
      name: newUser.name.trim(),
      role: newUser.role,
      email: newUser.email.trim() || `${newUser.name.trim()}@visiontrace.io`,
      lastActive: 'Just now',
    };
    setUsers(prev => [...prev, user]);
    setNewUser({ name: '', role: 'operator', email: '' });
    setShowAddModal(false);
  };

  const handleDeleteUser = (userId) => {
    setUsers(prev => prev.filter(u => u.id !== userId));
  };

  const handleSaveMatrix = () => {
    setSaveFlash(true);
    setTimeout(() => setSaveFlash(false), 2500);
  };

  const getRoleLabel = (roleId) => {
    const r = ROLES.find(r => r.id === roleId);
    return r ? r.label : roleId;
  };

  const getRoleColor = (roleId) => {
    switch (roleId) {
      case 'sysadmin': return '#ef4444';
      case 'operator': return '#38bdf8';
      case 'viewer': return '#10b981';
      default: return 'var(--text-secondary)';
    }
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
            {mode === 'users' 
              ? `${users.length} registered operators across ${ROLES.length} security tiers.`
              : 'Enterprise security gateway allocating operational clearance levels.'
            }
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          {mode === 'users' && (
            <button 
              onClick={() => setShowAddModal(true)}
              style={{ background: 'var(--primary)', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: 600 }}
            >
              <Plus size={16} /> Add User
            </button>
          )}
          {mode === 'permissions' && (
            <button 
              onClick={handleSaveMatrix}
              style={{ 
                background: saveFlash ? 'rgba(16, 185, 129, 0.15)' : 'var(--primary)', 
                color: saveFlash ? '#10b981' : '#fff', 
                border: saveFlash ? '1px solid rgba(16, 185, 129, 0.4)' : 'none', 
                padding: '8px 16px', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: 600,
                transition: 'all 0.3s ease',
              }}
            >
              {saveFlash ? <><CheckCircle2 size={16} /> Saved!</> : <><Save size={16} /> Save Security Matrix</>}
            </button>
          )}
        </div>
      </div>

      {mode === 'permissions' ? (
        /* ── Permissions Matrix ────────────────────────────────────── */
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
                    const isChecked = permissions[role.id]?.includes(cap.id);
                    return (
                      <td key={role.id} style={{ padding: '16px 24px', textAlign: 'center' }}>
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => togglePermission(role.id, cap.id)}
                          style={{
                            width: 22, height: 22,
                            accentColor: 'var(--primary)',
                            cursor: 'pointer',
                          }}
                        />
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        /* ── User Directory ────────────────────────────────────────── */
        <div className="glass-panel" style={{ flex: 1, overflowY: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-surface-hover)', zIndex: 10 }}>
              <tr>
                <th style={{ padding: '16px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px', textTransform: 'uppercase' }}>Operator ID</th>
                <th style={{ padding: '16px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px', textTransform: 'uppercase' }}>Email</th>
                <th style={{ padding: '16px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px', textTransform: 'uppercase' }}>Role</th>
                <th style={{ padding: '16px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px', textTransform: 'uppercase' }}>Permissions</th>
                <th style={{ padding: '16px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px', textTransform: 'uppercase' }}>Last Active</th>
                <th style={{ padding: '16px 24px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px', textTransform: 'uppercase', width: '60px' }}></th>
              </tr>
            </thead>
            <tbody>
              {users.map((user, idx) => (
                <tr key={user.id} style={{ borderBottom: '1px solid var(--border-color)', background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)' }}>
                  <td style={{ padding: '16px 24px' }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>{user.name}</div>
                  </td>
                  <td style={{ padding: '16px 24px', fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{user.email}</td>
                  <td style={{ padding: '16px 24px' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '4px 12px', borderRadius: '20px',
                      fontSize: '0.75rem', fontWeight: 700, fontFamily: 'var(--font-mono)',
                      color: getRoleColor(user.role),
                      background: `${getRoleColor(user.role)}15`,
                      border: `1px solid ${getRoleColor(user.role)}30`,
                    }}>
                      {getRoleLabel(user.role)}
                    </span>
                  </td>
                  <td style={{ padding: '16px 24px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {(permissions[user.role] || []).length} capabilities
                  </td>
                  <td style={{ padding: '16px 24px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>{user.lastActive}</td>
                  <td style={{ padding: '16px 24px' }}>
                    <button
                      onClick={() => handleDeleteUser(user.id)}
                      title="Remove User"
                      style={{
                        background: 'transparent', border: 'none',
                        color: 'var(--text-muted)', cursor: 'pointer',
                        padding: '4px', borderRadius: '4px',
                        transition: 'color var(--transition-fast)',
                      }}
                      onMouseOver={e => e.currentTarget.style.color = '#ef4444'}
                      onMouseOut={e => e.currentTarget.style.color = 'var(--text-muted)'}
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Add User Modal ──────────────────────────────────────── */}
      <AnimatePresence>
        {showAddModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
              background: 'rgba(0,0,0,0.6)',
              backdropFilter: 'blur(4px)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              zIndex: 1000,
            }}
            onClick={() => setShowAddModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={e => e.stopPropagation()}
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-lg)',
                padding: '32px',
                width: '100%',
                maxWidth: '480px',
                boxShadow: 'var(--shadow-elevation-3)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <h3 style={{ margin: 0, color: 'var(--text-primary)', fontFamily: 'var(--font-display)', fontSize: '1.25rem' }}>
                  Add New Operator
                </h3>
                <button onClick={() => setShowAddModal(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                  <X size={20} />
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px', fontWeight: 600 }}>Operator Username</label>
                  <input
                    type="text"
                    placeholder="e.g. operator_smith"
                    value={newUser.name}
                    onChange={e => setNewUser(prev => ({ ...prev, name: e.target.value }))}
                    autoFocus
                    style={{
                      width: '100%', padding: '12px 16px',
                      background: 'rgba(0,0,0,0.4)', color: '#fff',
                      border: '1px solid var(--border-color)', borderRadius: '6px',
                      fontFamily: 'var(--font-mono)', fontSize: '0.9rem',
                      outline: 'none',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px', fontWeight: 600 }}>Email Address</label>
                  <input
                    type="email"
                    placeholder="e.g. smith@facility.net"
                    value={newUser.email}
                    onChange={e => setNewUser(prev => ({ ...prev, email: e.target.value }))}
                    style={{
                      width: '100%', padding: '12px 16px',
                      background: 'rgba(0,0,0,0.4)', color: '#fff',
                      border: '1px solid var(--border-color)', borderRadius: '6px',
                      fontFamily: 'var(--font-body)', fontSize: '0.9rem',
                      outline: 'none',
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px', fontWeight: 600 }}>Clearance Role</label>
                  <select
                    value={newUser.role}
                    onChange={e => setNewUser(prev => ({ ...prev, role: e.target.value }))}
                    style={{
                      width: '100%', padding: '12px 16px',
                      background: 'rgba(0,0,0,0.4)', color: '#fff',
                      border: '1px solid var(--border-color)', borderRadius: '6px',
                      fontSize: '0.9rem', outline: 'none',
                    }}
                  >
                    {ROLES.map(r => (
                      <option key={r.id} value={r.id}>{r.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '12px', marginTop: '32px', justifyContent: 'flex-end' }}>
                <button
                  onClick={() => setShowAddModal(false)}
                  style={{ background: 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--border-color)', padding: '10px 20px', borderRadius: '6px', cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddUser}
                  disabled={!newUser.name.trim()}
                  style={{
                    background: newUser.name.trim() ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                    color: newUser.name.trim() ? '#fff' : 'var(--text-muted)',
                    border: 'none', padding: '10px 24px', borderRadius: '6px',
                    cursor: newUser.name.trim() ? 'pointer' : 'not-allowed',
                    fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px',
                  }}
                >
                  <Plus size={16} /> Create Operator
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}
