import React from 'react';
import { Users, Activity, Sparkles } from 'lucide-react';
import RollingNumber from './RollingNumber';

export default function IntelligentInsightPanel({ 
  peopleCount, 
  totalPeople, 
  activityLevel,
  latestSummary = "Crowd density scaling upwards; main vector flow concentrated toward northwest exit vector corridor."
}) {
  
  // Dynamic color for activity level
  let activityColor = 'var(--success)';
  if (activityLevel === 'Medium') activityColor = 'var(--warning)';
  if (activityLevel === 'High') activityColor = 'var(--danger)';

  // Format activity text based on level
  let activityText = 'NORMAL CROWD FLOW';
  if (activityLevel === 'Medium') activityText = 'ELEVATED ACTIVITY';
  if (activityLevel === 'High') activityText = 'CRITICAL SURGE';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '20px', padding: '20px' }}>
      
      {/* ── Live / Total Readout Card ────────────────────────── */}
      <div className="glass-panel hover-lift" style={{ padding: '20px', borderRadius: 'var(--radius-md)' }}>
        <div style={{
          color: 'var(--text-secondary)',
          fontSize: '0.75rem',
          fontWeight: 600,
          letterSpacing: '1px',
          display: 'flex', alignItems: 'center', gap: '8px',
          marginBottom: '12px'
        }}>
          <Users size={14} /> LIVE TOTAL / CURRENT SESSION
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          <div style={{
            fontFamily: 'var(--font-display)',
            fontSize: '3.5rem',
            fontWeight: 800,
            lineHeight: 1,
            color: 'var(--text-primary)'
          }}>
            <RollingNumber value={peopleCount || 0} />
          </div>
          <div style={{
            fontFamily: 'var(--font-display)',
            fontSize: '1.5rem',
            fontWeight: 600,
            color: 'var(--text-muted)'
          }}>
            / <RollingNumber value={totalPeople || 0} />
          </div>
        </div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '8px' }}>
          Unique tracked identities in current operational session.
        </div>
      </div>

      {/* ── Activity Heat Pill ─────────────────────────────── */}
      <div className="glass-panel hover-lift" style={{ 
        padding: '20px', 
        borderRadius: 'var(--radius-md)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
      }}>
        <div style={{
          color: 'var(--text-secondary)',
          fontSize: '0.75rem',
          fontWeight: 600,
          letterSpacing: '1px',
          display: 'flex', alignItems: 'center', gap: '8px'
        }}>
          <Activity size={14} /> ACTIVITY HEAT
        </div>
        
        <div style={{
          background: `rgba(${activityColor === 'var(--danger)' ? '239, 68, 68' : activityColor === 'var(--warning)' ? '245, 158, 11' : '16, 185, 129'}, 0.1)`,
          border: `1px solid ${activityColor}`,
          borderRadius: '4px',
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          boxShadow: `0 0 20px rgba(${activityColor === 'var(--danger)' ? '239, 68, 68' : activityColor === 'var(--warning)' ? '245, 158, 11' : '16, 185, 129'}, 0.2)`
        }}>
          <div style={{
            width: 12, height: 12, borderRadius: '50%',
            background: activityColor,
            animation: 'pulse-glow 2s infinite',
            boxShadow: `0 0 10px ${activityColor}`
          }} />
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontWeight: 700,
            letterSpacing: '1px',
            color: activityColor,
            fontSize: '0.9rem'
          }}>
            {activityText}
          </span>
        </div>
      </div>

      {/* ── Scene Summary Module ───────────────────────────── */}
      <div className="glass-panel" style={{ 
        padding: '20px', 
        borderRadius: 'var(--radius-md)',
        flex: 1, // take up remaining space
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{
          color: 'var(--text-accent)',
          fontSize: '0.75rem',
          fontWeight: 700,
          letterSpacing: '1px',
          display: 'flex', alignItems: 'center', gap: '8px',
          marginBottom: '16px'
        }}>
          <Sparkles size={14} /> SCENE INTELLIGENCE
        </div>
        
        <p style={{
          fontFamily: 'var(--font-body)',
          fontSize: '1rem',
          lineHeight: 1.7,
          color: 'var(--text-primary)',
          margin: 0
        }}>
          {latestSummary}
        </p>
      </div>

    </div>
  );
}
