import React, { useState } from 'react';
import { Search, Sparkles, Filter, ShieldAlert, Camera, MapPin, Clock, Tag, Crosshair, AlertTriangle, Loader } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const MOCK_RESULTS = [
  { id: 'T_992', confidence: 98, time: '19:04:12', cam: 'CAM_01_SOUTH', tags: ['Red Jacket', 'Backpack', 'Adult Male', 'Fast Movement'] },
  { id: 'T_914', confidence: 85, time: '19:02:45', cam: 'CAM_03_LOBBY', tags: ['Red Hoodie', 'Duffel Bag', 'Adult Female'] },
  { id: 'T_880', confidence: 72, time: '18:45:10', cam: 'CAM_01_SOUTH', tags: ['Maroon Coat', 'Backpack', 'Loitering'] },
];

export default function GlobalSearch() {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsLoading(true);
    setError(null);
    setHasSearched(false);
    
    try {
      // Simulate AI parsing and vector matching
      await new Promise(resolve => setTimeout(resolve, 1200));
      
      // In production this would be: const res = await fetch(`/api/search?q=${query}`);
      // For now we use mock data — but safely guard against undefined
      const results = MOCK_RESULTS || [];
      setSearchResults(results);
      setHasSearched(true);
    } catch (err) {
      console.error("Search failed:", err);
      setError("Unable to complete search. Please try again or check the backend connection.");
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Quick-fill chip handler
  const handleChipClick = (chipText) => {
    setQuery(chipText.replace(/"/g, ''));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '24px' }}>
      
      {/* ── Search Header Container ────────────────────────────── */}
      <div 
        className="glass-panel" 
        style={{ 
          padding: '32px', 
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          background: 'linear-gradient(to bottom, rgba(56, 189, 248, 0.05), rgba(0,0,0,0.4))',
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <div style={{ position: 'absolute', top: -50, right: -50, width: 200, height: 200, background: 'radial-gradient(circle, var(--primary) 0%, transparent 70%)', opacity: 0.1, filter: 'blur(40px)' }} />
        
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '1.8rem', color: '#fff', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Sparkles size={24} color="var(--primary)" /> Open-Vocabulary Semantic Search
        </h1>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '32px', fontFamily: 'var(--font-mono)', fontSize: '0.9rem' }}>
          Query 10,000+ localized vector embeddings across all operational cameras using natural language.
        </p>

        <form onSubmit={handleSearch} style={{ width: '100%', maxWidth: '800px', position: 'relative' }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. 'Show all individuals wearing red jackets carrying laptop backpacks near entrance after 7 PM'"
            style={{
              width: '100%',
              padding: '20px 60px 20px 24px',
              fontSize: '1.1rem',
              fontFamily: 'var(--font-body)',
              color: '#fff',
              background: 'rgba(0,0,0,0.4)',
              border: '1px solid var(--primary-subtle)',
              borderRadius: '12px',
              outline: 'none',
              boxShadow: 'inset 0 2px 10px rgba(0,0,0,0.5), 0 0 20px rgba(56, 189, 248, 0.1)',
              transition: 'all var(--transition-fast)'
            }}
            onFocus={(e) => e.target.style.borderColor = 'var(--primary)'}
            onBlur={(e) => e.target.style.borderColor = 'var(--primary-subtle)'}
          />
          <button 
            type="submit"
            disabled={isLoading}
            style={{
              position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)',
              background: isLoading ? 'transparent' : 'var(--primary)',
              color: isLoading ? 'var(--primary)' : '#fff',
              border: 'none',
              width: 44, height: 44,
              borderRadius: '8px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: isLoading ? 'default' : 'pointer',
              transition: 'all var(--transition-fast)'
            }}
          >
            {isLoading ? <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}><Search size={20} /></motion.div> : <Search size={20} />}
          </button>
        </form>

        <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
          {['"Red jacket"', '"After 7 PM"', '"Backpack"', '"Lobby camera"'].map((chip, idx) => (
            <div 
              key={idx} 
              onClick={() => handleChipClick(chip)}
              style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.05)', color: 'var(--text-secondary)', borderRadius: '20px', fontSize: '0.8rem', cursor: 'pointer', border: '1px solid var(--border-color)', transition: 'all var(--transition-fast)' }}
              onMouseOver={e => { e.currentTarget.style.borderColor = 'var(--primary)'; e.currentTarget.style.color = 'var(--primary)'; }}
              onMouseOut={e => { e.currentTarget.style.borderColor = 'var(--border-color)'; e.currentTarget.style.color = 'var(--text-secondary)'; }}
            >
              {chip}
            </div>
          ))}
        </div>
      </div>

      {/* ── Loading State ─────────────────────────────────────────── */}
      {isLoading && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '16px' }}>
          <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 2, ease: "linear" }}>
            <Loader size={40} color="var(--primary)" />
          </motion.div>
          <p style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.9rem' }}>
            Searching the vector database...
          </p>
        </div>
      )}

      {/* ── Error State ───────────────────────────────────────────── */}
      {!isLoading && error && (
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '16px', background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
          <AlertTriangle size={24} color="#ef4444" />
          <div>
            <div style={{ color: '#ef4444', fontWeight: 600, marginBottom: '4px' }}>Search Error</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{error}</div>
          </div>
        </div>
      )}

      {/* ── Results Matrix ───────────────────────────────────────── */}
      <AnimatePresence>
        {!isLoading && !error && hasSearched && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '20px', overflow: 'hidden' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                Found <strong style={{ color: 'var(--primary)' }}>{searchResults?.length || 0} matches</strong> across vector space index.
              </div>
              <button style={{ background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-primary)', padding: '6px 16px', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <Filter size={16} /> Filter Results
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px', overflowY: 'auto', paddingRight: '8px' }}>
              
              {searchResults?.length > 0 ? (
                searchResults.map((res, idx) => (
                  <motion.div 
                    key={res?.id || idx}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: idx * 0.1 }}
                    className="glass-panel"
                    style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', cursor: 'pointer' }}
                    whileHover={{ y: -4, borderColor: 'var(--primary-subtle)' }}
                  >
                    {/* Thumbnail Placeholder */}
                    <div style={{ height: '160px', background: 'linear-gradient(45deg, #111, #1a1a1a)', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <div style={{ position: 'absolute', top: 12, left: 12, background: 'rgba(0,0,0,0.8)', padding: '4px 8px', borderRadius: '4px', fontSize: '0.7rem', color: '#fff', fontFamily: 'var(--font-mono)', border: '1px solid var(--border-color)' }}>
                        {res?.time || 'N/A'}
                      </div>
                      <div style={{ position: 'absolute', top: 12, right: 12, background: 'rgba(56, 189, 248, 0.2)', color: 'var(--primary)', padding: '4px 8px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 700, fontFamily: 'var(--font-mono)', border: '1px solid var(--primary-subtle)' }}>
                        {res?.confidence || 0}% MATCH
                      </div>
                      <Crosshair size={32} color="rgba(255,255,255,0.1)" />
                    </div>

                    {/* Details */}
                    <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}>Track {res?.id}</span>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Camera size={14} /> {res?.cam || 'Unknown'}
                        </span>
                      </div>

                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {res?.tags?.map((tag, tIdx) => (
                          <div key={tIdx} style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', fontSize: '0.75rem', padding: '4px 8px', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <Tag size={10} color="var(--primary)" /> {tag}
                          </div>
                        )) || null}
                      </div>
                    </div>
                  </motion.div>
                ))
              ) : (
                <div style={{ gridColumn: '1 / -1', padding: '60px 40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  <Search size={48} style={{ marginBottom: '16px', opacity: 0.4 }} />
                  <h3 style={{ margin: '0 0 8px 0', color: 'var(--text-primary)' }}>No matching identities or events found</h3>
                  <p style={{ margin: 0, fontSize: '0.9rem' }}>Try adjusting your natural language terms or broadening the search window.</p>
                </div>
              )}

            </div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}
