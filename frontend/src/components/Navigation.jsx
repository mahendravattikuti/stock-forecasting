import React, { useState, useRef } from 'react';
import { Menu, X } from 'lucide-react';

export default function Navigation({ tabs, activeTab, setActiveTab }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const tabsRef = useRef([]);

  const handleTabClick = (tabId, index) => {
    setActiveTab(tabId);
    setMobileMenuOpen(false);
    // Set focus to the clicked tab for keyboard users
    tabsRef.current[index]?.focus();
  };

  const handleKeyDown = (e, index) => {
    let newIndex = index;
    let shouldFocus = false;

    switch (e.key) {
      case 'ArrowRight':
      case 'ArrowDown':
        e.preventDefault();
        newIndex = (index + 1) % tabs.length;
        shouldFocus = true;
        break;
      case 'ArrowLeft':
      case 'ArrowUp':
        e.preventDefault();
        newIndex = (index - 1 + tabs.length) % tabs.length;
        shouldFocus = true;
        break;
      case 'Home':
        e.preventDefault();
        newIndex = 0;
        shouldFocus = true;
        break;
      case 'End':
        e.preventDefault();
        newIndex = tabs.length - 1;
        shouldFocus = true;
        break;
      default:
        return;
    }

    if (shouldFocus) {
      setActiveTab(tabs[newIndex].id);
      setTimeout(() => tabsRef.current[newIndex]?.focus(), 0);
    }
  };

  return (
    <nav className="bg-slate-950 border-b border-slate-700 sticky top-0 z-50 shadow-lg" aria-label="Main navigation">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14 sm:h-16">
          {/* Logo */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold text-sm sm:text-base" aria-hidden="true">📈</span>
            </div>
            <h1 className="text-base sm:text-xl font-bold text-white hidden xs:block">Stock Optimizer</h1>
          </div>
          
          {/* Desktop Navigation */}
          <div className="hidden md:flex gap-1" role="tablist">
            {tabs.map((tab, index) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  ref={(el) => (tabsRef.current[index] = el)}
                  role="tab"
                  aria-selected={activeTab === tab.id}
                  aria-controls={`tabpanel-${tab.id}`}
                  tabIndex={activeTab === tab.id ? 0 : -1}
                  onClick={() => handleTabClick(tab.id, index)}
                  onKeyDown={(e) => handleKeyDown(e, index)}
                  className={`px-3 lg:px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-all text-sm lg:text-base focus:ring-2 focus:ring-blue-500 focus:outline-none ${
                    activeTab === tab.id
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <Icon size={18} aria-hidden="true" />
                  <span className="hidden lg:inline">{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg text-slate-300 hover:bg-slate-800 transition-colors focus:ring-2 focus:ring-blue-500 focus:outline-none"
            aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-nav-menu"
          >
            {mobileMenuOpen ? <X size={24} aria-hidden="true" /> : <Menu size={24} aria-hidden="true" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div id="mobile-nav-menu" className="md:hidden pb-3 space-y-2 animate-in fade-in slide-in-from-top-2 duration-200" role="tablist">
            {tabs.map((tab, index) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  role="tab"
                  aria-selected={activeTab === tab.id}
                  aria-controls={`tabpanel-${tab.id}`}
                  onClick={() => handleTabClick(tab.id, index)}
                  onKeyDown={(e) => handleKeyDown(e, index)}
                  className={`w-full px-4 py-2 rounded-lg font-medium flex items-center gap-3 transition-all focus:ring-2 focus:ring-blue-500 focus:outline-none ${
                    activeTab === tab.id
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <Icon size={20} aria-hidden="true" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        )}
      </div>
    </nav>
  );
}
