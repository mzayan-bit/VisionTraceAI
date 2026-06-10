import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

export default function TypewriterMarkdown({ content, speed = 15 }) {
  const [displayedText, setDisplayedText] = useState('');

  useEffect(() => {
    // If the text drastically changes (e.g. new message), reset
    if (!content.startsWith(displayedText)) {
      setDisplayedText('');
    }

    if (displayedText.length < content.length) {
      const timeoutId = setTimeout(() => {
        // Add chunk of characters at a time for realism rather than 1 by 1
        const remainingChars = content.length - displayedText.length;
        const charsToAdd = Math.min(Math.floor(Math.random() * 3) + 1, remainingChars);
        setDisplayedText(content.slice(0, displayedText.length + charsToAdd));
      }, speed + (Math.random() * 10)); // Variable speed for natural feel
      
      return () => clearTimeout(timeoutId);
    }
  }, [content, displayedText, speed]);

  return (
    <div className="typewriter-markdown">
      <ReactMarkdown
        components={{
          p: ({node, ...props}) => <p style={{ margin: '0 0 0.5em 0' }} {...props} />,
          strong: ({node, ...props}) => <strong style={{ color: 'var(--text-accent)' }} {...props} />,
          ul: ({node, ...props}) => <ul style={{ margin: '0.5em 0', paddingLeft: '1.2em' }} {...props} />,
          li: ({node, ...props}) => <li style={{ margin: '0.2em 0' }} {...props} />
        }}
      >
        {displayedText}
      </ReactMarkdown>
      {displayedText.length < content.length && (
        <span style={{ 
          display: 'inline-block', 
          width: 6, 
          height: 14, 
          background: 'var(--primary)',
          marginLeft: 4,
          animation: 'pulse 1s infinite' 
        }} />
      )}
    </div>
  );
}
