import React, { useState } from 'react';
import Navigation from '../Navigation';
import { useTheme } from '../../context/ThemeContext';

/**
 * AppLayout Component
 * 
 * Main application layout wrapper providing:
 * - Responsive sidebar navigation
 * - Header with theme toggle
 * - Main content area
 * - Mobile-friendly hamburger menu
 * 
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Main content to render
 * @param {string} [props.title] - Page title shown in header
 * @param {React.ReactNode} [props.headerActions] - Custom actions in header right
 * @returns {React.ReactNode} Complete app layout wrapper
 */
export const AppLayout = ({ children, title, headerActions }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { theme, toggleTheme } = useTheme();

  return (
    <div className={`app-layout theme-${theme}`}>
      {/* Skip to Main Content Link - Accessibility Feature */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only fixed top-0 left-0 z-[9999] px-4 py-2 bg-blue-600 text-white rounded-b-lg focus:outline-none"
      >
        Skip to main content
      </a>

      {/* Header */}
      <header className="app-header" role="banner">
        <div className="header-left">
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
            aria-expanded={sidebarOpen}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
          {title && <h1 className="page-title">{title}</h1>}
        </div>

        <div className="header-right">
          {headerActions}
          <button
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            title={`${theme === 'light' ? 'Dark' : 'Light'} mode`}
          >
            {theme === 'light' ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
          </button>
        </div>
      </header>

      <div className="app-container">
        {/* Sidebar */}
        <aside className={`app-sidebar ${sidebarOpen ? 'open' : 'closed'}`} role="complementary" aria-label="Navigation sidebar">
          <Navigation />
        </aside>

        {/* Main Content */}
        <main className="app-main" id="main-content" role="main">
          <div className="app-content">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
