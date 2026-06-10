import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, ChevronLeft, Bot } from 'lucide-react';

export default function RightDrawer({
  isOpen,
  onToggle,
  children,
  width = 380
}) {
  return (
    <>
      {/* ── Desktop Drawer ────────────────────────────────────── */}
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 150, damping: 20 }}
            style={{
              height: '100%',
              background: 'var(--bg-surface)',
              borderLeft: '1px solid var(--border-color)',
              backdropFilter: 'var(--glass-blur)',
              WebkitBackdropFilter: 'var(--glass-blur)',
              display: 'flex',
              flexDirection: 'column',
              position: 'relative',
              overflow: 'hidden',
              flexShrink: 0,
            }}
          >
            <div style={{
              width: width,
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              position: 'absolute',
              top: 0,
              right: 0,
            }}>
              {/* Header */}
              <div style={{
                padding: '16px 20px',
                borderBottom: '1px solid var(--border-color)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{
                    width: 28, height: 28, borderRadius: 'var(--radius-sm)',
                    background: 'var(--primary-subtle)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: 'var(--primary)'
                  }}>
                    <Bot size={16} />
                  </div>
                  <span style={{
                    fontFamily: 'var(--font-display)',
                    fontWeight: 600,
                    letterSpacing: '0.5px'
                  }}>AI Operations Context</span>
                </div>
                
                <button
                  onClick={onToggle}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    padding: 4,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: 'var(--radius-sm)',
                    transition: 'all var(--transition-fast)',
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.background = 'var(--bg-surface-hover)';
                    e.currentTarget.style.color = 'var(--text-primary)';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.color = 'var(--text-secondary)';
                  }}
                >
                  <ChevronRight size={20} />
                </button>
              </div>

              {/* Content */}
              <div style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden' }}>
                {children}
              </div>
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* ── Toggle Button when closed ─────────────────────────── */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            onClick={onToggle}
            style={{
              position: 'fixed',
              right: 0,
              top: '50%',
              transform: 'translateY(-50%)',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-color)',
              borderRight: 'none',
              color: 'var(--text-secondary)',
              padding: '16px 8px',
              borderRadius: '8px 0 0 8px',
              cursor: 'pointer',
              zIndex: 90,
              backdropFilter: 'var(--glass-blur)',
              boxShadow: '-4px 0 15px rgba(0,0,0,0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all var(--transition-fast)',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = 'var(--primary-subtle)';
              e.currentTarget.style.color = 'var(--primary)';
              e.currentTarget.style.paddingRight = '12px';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'var(--bg-surface)';
              e.currentTarget.style.color = 'var(--text-secondary)';
              e.currentTarget.style.paddingRight = '8px';
            }}
          >
            <ChevronLeft size={20} />
          </motion.button>
        )}
      </AnimatePresence>
    </>
  );
}
