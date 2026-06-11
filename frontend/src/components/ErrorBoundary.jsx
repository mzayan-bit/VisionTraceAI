import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

/**
 * Global ErrorBoundary — catches any unhandled render errors
 * in child components and displays a fallback UI instead of
 * unmounting the entire application shell.
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary] Caught fatal render error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          height: '100%', padding: '40px', textAlign: 'center', gap: '20px',
        }}>
          <div style={{
            width: 80, height: 80, borderRadius: '50%',
            background: 'rgba(239, 68, 68, 0.1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <AlertTriangle size={40} color="#ef4444" />
          </div>

          <h2 style={{ margin: 0, color: 'var(--text-primary, #fff)', fontFamily: 'var(--font-display, sans-serif)', fontSize: '1.4rem' }}>
            Something went wrong in this module
          </h2>
          <p style={{ margin: 0, color: 'var(--text-secondary, #999)', fontSize: '0.9rem', maxWidth: 500 }}>
            A render error crashed this panel. Your other controls and navigation remain functional.
          </p>

          {this.state.error && (
            <div style={{
              background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(239, 68, 68, 0.2)',
              borderRadius: '8px', padding: '12px 16px', maxWidth: 600, width: '100%',
              fontFamily: 'var(--font-mono, monospace)', fontSize: '0.8rem', color: '#ef4444',
              textAlign: 'left', overflowX: 'auto',
            }}>
              {this.state.error.toString()}
            </div>
          )}

          <button
            onClick={this.handleReset}
            style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              background: 'var(--primary, #38bdf8)', color: '#fff',
              border: 'none', padding: '10px 24px', borderRadius: '6px',
              cursor: 'pointer', fontWeight: 600, fontSize: '0.9rem',
            }}
          >
            <RefreshCw size={16} /> Retry Module
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
