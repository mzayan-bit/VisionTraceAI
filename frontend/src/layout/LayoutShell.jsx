import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './Sidebar';
import RightDrawer from './RightDrawer';

export default function LayoutShell({
  activeScreen,
  onNavigate,
  renderScreen,
  rightPanelContent,
}) {
  const [isRightDrawerOpen, setIsRightDrawerOpen] = useState(true);

  return (
    <div style={{
      display: 'flex',
      width: '100vw',
      height: '100vh',
      background: 'var(--bg-base)',
      color: 'var(--text-primary)',
      overflow: 'hidden',
      position: 'relative',
    }}>
      {/* Background visual effects based on theme */}
      <div style={{
        position: 'absolute',
        top: 0, left: 0, right: 0, bottom: 0,
        background: 'var(--bg-gradient)',
        pointerEvents: 'none',
        zIndex: 0,
      }} />
      <div style={{
        position: 'absolute',
        top: 0, left: 0, right: 0, bottom: 0,
        background: 'var(--scanline)',
        pointerEvents: 'none',
        zIndex: 1,
      }} />

      {/* ── 1. Global Sidebar (Fixed Left) ────────── */}
      <div style={{ zIndex: 100 }}>
        <Sidebar activeScreen={activeScreen} onNavigate={onNavigate} />
      </div>

      {/* ── 2. Hero Workspace (Center/Left) ───────── */}
      <div style={{
        flex: 1,
        height: '100%',
        marginLeft: '72px', /* Reserve space for collapsed sidebar */
        position: 'relative',
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* Main Content Area */}
        <main style={{
          flex: 1,
          padding: '24px',
          overflowY: 'auto',
          overflowX: 'hidden',
        }}>
          <AnimatePresence mode="wait">
            <motion.div
              key={activeScreen}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              style={{ height: '100%' }}
            >
              {renderScreen(activeScreen)}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* ── 3. Right Drawer (30% Width) ───────────── */}
      <div style={{ zIndex: 20 }}>
        <RightDrawer
          isOpen={isRightDrawerOpen}
          onToggle={() => setIsRightDrawerOpen(!isRightDrawerOpen)}
          width={400}
        >
          {rightPanelContent}
        </RightDrawer>
      </div>
    </div>
  );
}
