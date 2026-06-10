import { motion } from 'framer-motion';
import { Construction } from 'lucide-react';

export default function PlaceholderScreen({ screenId }) {
  // Format the ID into a title
  const title = screenId
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <motion.div
        className="glass-panel"
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        style={{
          padding: '3rem',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          maxWidth: 500,
          border: '1px solid var(--border-accent)',
          boxShadow: 'var(--shadow-elevation-2)',
        }}
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
          style={{
            width: 80, height: 80,
            borderRadius: '50%',
            background: 'var(--primary-subtle)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: '1.5rem',
            color: 'var(--primary)',
            boxShadow: 'var(--shadow-glow)'
          }}
        >
          <Construction size={40} />
        </motion.div>
        
        <h2 style={{
          fontFamily: 'var(--font-display)',
          fontSize: '2rem',
          color: 'var(--text-primary)',
          marginBottom: '0.5rem',
          fontWeight: 700,
        }}>
          {title}
        </h2>
        
        <p style={{
          color: 'var(--text-secondary)',
          fontSize: '1.1rem',
          lineHeight: 1.6,
        }}>
          This module is currently under active development. It will be available in an upcoming release.
        </p>
      </motion.div>
    </div>
  );
}
