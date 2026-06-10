import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { themes, defaultTheme } from './themes';

const ThemeContext = createContext(null);

const STORAGE_KEY = 'visiontrace-theme';

/**
 * Applies a theme by setting CSS custom properties directly on <html>.
 * This is a pure DOM operation — no React re-render needed for the
 * visual change to take effect across the entire app.
 */
function applyThemeToDOM(themeId) {
  const theme = themes[themeId];
  if (!theme) return;

  const root = document.documentElement;
  Object.entries(theme).forEach(([key, value]) => {
    if (key.startsWith('--')) {
      root.style.setProperty(key, value);
    }
  });

  // Set a data attribute for any CSS selectors that need theme-awareness
  root.setAttribute('data-theme', themeId);
}

export function ThemeProvider({ children }) {
  const [themeName, setThemeName] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) || defaultTheme;
    } catch {
      return defaultTheme;
    }
  });

  // Apply theme on mount and whenever themeName changes
  useEffect(() => {
    applyThemeToDOM(themeName);
    try {
      localStorage.setItem(STORAGE_KEY, themeName);
    } catch {
      // localStorage may be unavailable
    }
  }, [themeName]);

  const setTheme = useCallback((id) => {
    if (themes[id]) {
      setThemeName(id);
    }
  }, []);

  const value = {
    themeName,
    setTheme,
    theme: themes[themeName] || themes[defaultTheme],
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within <ThemeProvider>');
  return ctx;
}
