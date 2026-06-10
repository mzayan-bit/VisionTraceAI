import React, { useState } from 'react';
import { BarChart3, TrendingUp, Users, Activity, Layers } from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  LineChart, Line, ComposedChart, Bar 
} from 'recharts';

// Mock Time-Series Data
const PERFORMANCE_DATA = Array.from({ length: 24 }).map((_, i) => ({
  time: `${String(i).padStart(2, '0')}:00`,
  events: Math.floor(Math.random() * 500 + 200),
  latency: Math.floor(Math.random() * 15 + 10),
  gpu: Math.floor(Math.random() * 40 + 50),
}));

const PREDICTIVE_OCCUPANCY = Array.from({ length: 24 }).map((_, i) => {
  const base = Math.sin((i / 24) * Math.PI) * 1000;
  return {
    time: `${String(i).padStart(2, '0')}:00`,
    historical: Math.max(0, base + (Math.random() * 200 - 100)),
    predicted: i > 12 ? Math.max(0, base + (Math.random() * 400)) : null, // Predict spike in PM
  };
});

// Custom Tooltip for dark mode
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: 'rgba(0,0,0,0.8)', border: '1px solid var(--border-color)', padding: '12px', borderRadius: '8px', backdropFilter: 'blur(4px)' }}>
        <p style={{ margin: '0 0 8px 0', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{label} UTC</p>
        {payload.map((entry, idx) => (
          <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', color: entry.color, fontWeight: 600 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: entry.color }} />
            {entry.name}: {Math.round(entry.value)}
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export default function KPIDashboard({ mode = 'kpi' }) {
  const isPredictive = mode === 'traffic' || mode === 'occupancy' || mode === 'trends';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '24px' }}>
      
      {/* ── Header ─────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderBottom: '1px solid var(--border-color)', paddingBottom: '20px' }}>
        <div>
          <h1 className="text-heading" style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: 0 }}>
            <div style={{ width: 40, height: 40, background: 'var(--primary-subtle)', color: 'var(--primary)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {isPredictive ? <TrendingUp size={20} /> : <BarChart3 size={20} />}
            </div>
            {isPredictive ? 'Predictive Analytics & Traffic' : 'System Performance KPI'}
          </h1>
          <p style={{ color: 'var(--text-secondary)', margin: '8px 0 0 52px', fontSize: '0.9rem' }}>
            {isPredictive ? 'AI-driven projected congestion vectors over a rolling 24-hour cycle.' : 'High-fidelity telemetry mapping hardware load and pipeline latency.'}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <select style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', border: '1px solid var(--border-color)', padding: '8px 16px', borderRadius: '6px', outline: 'none' }}>
            <option>Last 24 Hours</option>
            <option>Last 7 Days</option>
            <option>Last 30 Days</option>
          </select>
        </div>
      </div>

      {/* ── Metrics Summary Cards ──────────────────────────────── */}
      {!isPredictive && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
          {[
            { label: 'Cumulative Events', value: '14,204', trend: '+12%', icon: Layers, color: '#38bdf8' },
            { label: 'Avg Inference Latency', value: '14.2ms', trend: '-2.1%', icon: Activity, color: '#10b981' },
            { label: 'GPU Compute Load', value: '78%', trend: '+5%', icon: BarChart3, color: '#f59e0b' },
            { label: 'Detection Accuracy', value: '99.1%', trend: '+0.2%', icon: Users, color: '#ec4899' },
          ].map((stat, i) => {
            const Icon = stat.icon;
            return (
              <div key={i} className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--text-secondary)' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{stat.label}</span>
                  <Icon size={16} />
                </div>
                <div style={{ fontSize: '2rem', fontFamily: 'var(--font-display)', fontWeight: 700, color: stat.color }}>
                  {stat.value}
                </div>
                <div style={{ fontSize: '0.8rem', color: stat.trend.startsWith('+') && stat.label !== 'Avg Inference Latency' ? 'var(--success)' : (stat.label === 'Avg Inference Latency' && stat.trend.startsWith('-') ? 'var(--success)' : 'var(--danger)') }}>
                  {stat.trend} vs yesterday
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Charts Engine ──────────────────────────────────────── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '24px', overflowY: 'auto', paddingRight: '8px' }}>
        
        {isPredictive ? (
          <>
            <div className="glass-panel" style={{ padding: '24px', flex: 1, minHeight: '400px' }}>
              <h3 style={{ margin: '0 0 24px 0', color: 'var(--text-primary)' }}>Occupancy Projection Model</h3>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={PREDICTIVE_OCCUPANCY}>
                  <defs>
                    <linearGradient id="colorHist" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#38bdf8" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={12} tickMargin={10} />
                  <YAxis stroke="var(--text-muted)" fontSize={12} tickFormatter={(val) => `${val/1000}k`} />
                  <Tooltip content={<CustomTooltip />} />
                  
                  {/* Historical Area */}
                  <Area type="monotone" dataKey="historical" name="Recorded Traffic" stroke="#38bdf8" strokeWidth={2} fillOpacity={1} fill="url(#colorHist)" animationDuration={1000} />
                  
                  {/* AI Prediction Line (Dashed) */}
                  <Line type="monotone" dataKey="predicted" name="AI Projection" stroke="#ec4899" strokeWidth={2} strokeDasharray="5 5" dot={false} animationDuration={1000} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </>
        ) : (
          <>
            <div className="glass-panel" style={{ padding: '24px', height: '320px' }}>
              <h3 style={{ margin: '0 0 24px 0', color: 'var(--text-primary)' }}>System Events & Inference Latency</h3>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={PERFORMANCE_DATA}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={12} tickMargin={10} />
                  <YAxis yAxisId="left" stroke="var(--text-muted)" fontSize={12} />
                  <YAxis yAxisId="right" orientation="right" stroke="var(--text-muted)" fontSize={12} />
                  <Tooltip content={<CustomTooltip />} />
                  
                  <Bar yAxisId="left" dataKey="events" name="Total Events" fill="var(--primary-subtle)" radius={[4, 4, 0, 0]} animationDuration={1000} />
                  <Line yAxisId="right" type="monotone" dataKey="latency" name="Latency (ms)" stroke="#10b981" strokeWidth={3} dot={{ r: 2, fill: '#10b981' }} animationDuration={1000} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            <div className="glass-panel" style={{ padding: '24px', height: '320px' }}>
              <h3 style={{ margin: '0 0 24px 0', color: 'var(--text-primary)' }}>Hardware Resource Load (GPU %)</h3>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={PERFORMANCE_DATA}>
                  <defs>
                    <linearGradient id="colorGpu" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={12} tickMargin={10} />
                  <YAxis stroke="var(--text-muted)" fontSize={12} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="gpu" name="GPU Usage" stroke="#f59e0b" strokeWidth={2} fillOpacity={1} fill="url(#colorGpu)" animationDuration={1000} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </>
        )}

      </div>
    </div>
  );
}
