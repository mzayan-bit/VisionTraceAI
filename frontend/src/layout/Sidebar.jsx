import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Monitor, LayoutGrid, Camera, Crosshair,
  Brain, Search, Clock, Play, Bell,
  Bot, Database, GitBranch, ShieldAlert,
  BarChart3, TrendingUp, Users, Activity,
  Map, Globe,
  UserCog, Lock, FileText, Package, Settings,
  ChevronRight, Palette,
} from 'lucide-react';
import { useTheme } from '../themes/ThemeProvider';
import { themeList } from '../themes/themes';

// ─── Navigation Definition ──────────────────────────────────────────
const NAV_GROUPS = [
  {
    label: 'Live Operations',
    items: [
      { id: 'live-monitoring',  icon: Monitor,    label: 'Live Monitoring',  screen: 1 },
      { id: 'multi-camera',    icon: LayoutGrid,  label: 'Multi-Camera Grid', screen: 3 },
    ],
  },
  {
    label: 'Asset Infrastructure',
    items: [
      { id: 'camera-mgmt',    icon: Camera,      label: 'Camera Management', screen: 2 },
      { id: 'object-tracking', icon: Crosshair,   label: 'Object Tracking',   screen: 8 },
    ],
  },
  {
    label: 'Cognitive Engine',
    items: [
      { id: 'global-search',   icon: Search,      label: 'Global Search & Intelligence', screen: 5 },
    ],
  },
  {
    label: 'Operational Logs',
    items: [
      { id: 'event-timeline',  icon: Clock,       label: 'Event Timeline',   screen: 6 },
      { id: 'playback',        icon: Play,        label: 'Playback Center',  screen: 7 },
      { id: 'alert-center',    icon: Bell,        label: 'Alert Center',     screen: 10 },
    ],
  },
  {
    label: 'Autonomous Agents',
    items: [
      { id: 'agent-command',   icon: Bot,         label: 'Command Center',   screen: 11 },
    ],
  },
  {
    label: 'Deep Intelligence',
    items: [
      { id: 'kpi-dashboard',   icon: BarChart3,   label: 'KPI Dashboard',    screen: 15 },
      { id: 'deep-analytics',  icon: Activity,    label: 'Deep Analytics',   screen: 16 },
    ],
  },
  {
    label: 'Spatial Mapping',
    items: [
      { id: 'building-3d',    icon: Map,          label: 'Building Map 3D',  screen: 19 },
      { id: 'geo-view',       icon: Globe,        label: 'Geographic View',  screen: 20 },
    ],
  },
  {
    label: 'System Core',
    items: [
      { id: 'users',          icon: UserCog,      label: 'User Management',  screen: 21 },
      { id: 'permissions',    icon: Lock,         label: 'Permissions',      screen: 22 },
      { id: 'audit-logs',     icon: FileText,     label: 'Audit Logs',       screen: 23 },
      { id: 'export',         icon: Package,      label: 'Export & Evidence', screen: 24 },
      { id: 'settings',       icon: Settings,     label: 'Global Settings',  screen: 26 },
    ],
  },
];

// ─── Component ──────────────────────────────────────────────────────
export default function Sidebar({ activeScreen, onNavigate }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showThemes, setShowThemes] = useState(false);
  const { themeName, setTheme } = useTheme();

  return (
    <motion.nav
      className="vt-sidebar"
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => { setIsExpanded(false); setShowThemes(false); }}
      animate={{ width: isExpanded ? 260 : 72 }}
      transition={{ type: 'spring', stiffness: 200, damping: 26 }}
      style={{
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        background: 'var(--bg-sidebar)',
        borderRight: '1px solid var(--border-color)',
        backdropFilter: 'var(--glass-blur)',
        WebkitBackdropFilter: 'var(--glass-blur)',
        zIndex: 100,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        boxShadow: 'var(--shadow-elevation-2)',
      }}
    >
      {/* ── Logo ─────────────────────────────────────────────────── */}
      <div style={{
        padding: '20px 0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderBottom: '1px solid var(--border-color)',
        minHeight: 64,
        gap: 12,
        overflow: 'hidden',
        flexShrink: 0,
      }}>
        <div style={{
          width: 36, height: 36, borderRadius: 'var(--radius-md)',
          background: 'linear-gradient(135deg, var(--primary), var(--text-accent))',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
          boxShadow: 'var(--shadow-glow)',
        }}>
          <Monitor size={20} color="#fff" />
        </div>
        <AnimatePresence>
          {isExpanded && (
            <motion.span
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.15 }}
              style={{
                fontFamily: 'var(--font-display)',
                fontWeight: 700,
                fontSize: '1.1rem',
                color: 'var(--text-primary)',
                letterSpacing: '0.5px',
                whiteSpace: 'nowrap',
              }}
            >
              VisionTrace
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* ── Navigation Groups ────────────────────────────────────── */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        overflowX: 'hidden',
        padding: '12px 0',
        scrollbarWidth: 'thin',
        scrollbarColor: 'var(--border-color) transparent',
      }}>
        {NAV_GROUPS.map((group, gi) => (
          <div key={gi} style={{ marginBottom: 8 }}>
            {/* Group Label */}
            <AnimatePresence>
              {isExpanded && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.1 }}
                  style={{
                    padding: '8px 20px 4px',
                    fontSize: '0.65rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '1.5px',
                    color: 'var(--text-muted)',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {group.label}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Items */}
            {group.items.map((item) => {
              const Icon = item.icon;
              const isActive = activeScreen === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onNavigate(item.id)}
                  title={item.label}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14,
                    padding: isExpanded ? '10px 20px' : '10px 0',
                    justifyContent: isExpanded ? 'flex-start' : 'center',
                    background: isActive ? 'var(--primary-subtle)' : 'transparent',
                    border: 'none',
                    borderLeft: isActive ? '3px solid var(--primary)' : '3px solid transparent',
                    color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)',
                    position: 'relative',
                    fontSize: '0.875rem',
                    fontFamily: 'var(--font-body)',
                    fontWeight: isActive ? 600 : 400,
                  }}
                  onMouseOver={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.background = 'var(--bg-surface-hover)';
                      e.currentTarget.style.color = 'var(--text-primary)';
                    }
                  }}
                  onMouseOut={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.background = 'transparent';
                      e.currentTarget.style.color = 'var(--text-secondary)';
                    }
                  }}
                >
                  <Icon size={20} style={{ flexShrink: 0 }} />
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.span
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -8 }}
                        transition={{ duration: 0.12 }}
                        style={{ whiteSpace: 'nowrap', overflow: 'hidden' }}
                      >
                        {item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </button>
              );
            })}

            {/* Divider between groups */}
            {gi < NAV_GROUPS.length - 1 && (
              <div style={{
                height: 1,
                background: 'var(--border-color)',
                margin: '8px 16px',
              }} />
            )}
          </div>
        ))}
      </div>

      {/* ── Theme Switcher ───────────────────────────────────────── */}
      <div style={{
        borderTop: '1px solid var(--border-color)',
        padding: '12px',
        flexShrink: 0,
      }}>
        <button
          onClick={() => setShowThemes(!showThemes)}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: isExpanded ? 'flex-start' : 'center',
            gap: 14,
            padding: isExpanded ? '10px 8px' : '10px 0',
            background: showThemes ? 'var(--primary-subtle)' : 'transparent',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            fontSize: '0.875rem',
            fontFamily: 'var(--font-body)',
            transition: 'all var(--transition-fast)',
          }}
        >
          <Palette size={20} style={{ flexShrink: 0 }} />
          <AnimatePresence>
            {isExpanded && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{ whiteSpace: 'nowrap' }}
              >
                Theme
              </motion.span>
            )}
          </AnimatePresence>
        </button>

        {/* Theme Swatches */}
        <AnimatePresence>
          {showThemes && isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 8,
                padding: '10px 8px 4px',
                overflow: 'hidden',
              }}
            >
              {themeList.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTheme(t.id)}
                  title={t.label}
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    background: t.swatch,
                    border: themeName === t.id
                      ? '3px solid var(--text-primary)'
                      : '2px solid rgba(255,255,255,0.15)',
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)',
                    transform: themeName === t.id ? 'scale(1.15)' : 'scale(1)',
                    boxShadow: themeName === t.id
                      ? `0 0 12px ${t.swatch}60`
                      : 'none',
                  }}
                />
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.nav>
  );
}
