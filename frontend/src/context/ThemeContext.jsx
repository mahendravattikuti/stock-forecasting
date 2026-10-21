import React, { createContext, useState, useContext, useEffect } from 'react';

/**
 * Theme Context
 * 
 * Provides dark/light theme management across the application.
 * Persists theme preference to localStorage.
 */
const ThemeContext = createContext();

/**
 * ThemeProvider Component
 * 
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components
 * @param {('light'|'dark')} [props.defaultTheme='light'] - Initial theme
 * @returns {React.ReactNode} Provider wrapper
 */
export const ThemeProvider = ({ children, defaultTheme = 'light' }) => {
  const [theme, setTheme] = useState(() => {
    // Try to get theme from localStorage
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('app-theme');
      if (stored) return stored;
      // Check system preference
      if (window.matchMedia?.('(prefers-color-scheme: dark)').matches) {
        return 'dark';
      }
    }
    return defaultTheme;
  });

  // Update localStorage and DOM when theme changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('app-theme', theme);
      document.documentElement.setAttribute('data-theme', theme);
      document.body.className = `theme-${theme}`;
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const setThemeExplicitly = (newTheme) => {
    if (newTheme === 'light' || newTheme === 'dark') {
      setTheme(newTheme);
    }
  };

  const value = {
    theme,
    toggleTheme,
    setTheme: setThemeExplicitly,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

/**
 * useTheme Hook
 * 
 * Access theme context in any component.
 * Must be used within a ThemeProvider.
 * 
 * @returns {Object} Theme object: { theme, toggleTheme, setTheme }
 * @throws {Error} If used outside ThemeProvider
 */
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export default ThemeContext;
