import React, { useState } from 'react';
import { Menu, X } from 'lucide-react';

export default function Navigation({ tabs, activeTab, setActiveTab }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleTabClick = (tabId) => {
    setActiveTab(tabId);
    setMobileMenuOpen(false); // Close menu after selection on mobile
  };

  return (
    <nav className="bg-slate-950 border-b border-slate-700 sticky top-0 z-50 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14 sm:h-16">
          {/* Logo */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold text-sm sm:text-base">📈</span>
            </div>
            <h1 className="text-base sm:text-xl font-bold text-white hidden xs:block">Stock Optimizer</h1>
          </div>
          
          {/* Desktop Navigation */}
          <div className="hidden md:flex gap-1">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabClick(tab.id)}
                  className={`px-3 lg:px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-all text-sm lg:text-base ${
                    activeTab === tab.id
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <Icon size={18} />
                  <span className="hidden lg:inline">{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg text-slate-300 hover:bg-slate-800 transition-colors"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden pb-3 space-y-2 animate-in fade-in slide-in-from-top-2 duration-200">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabClick(tab.id)}
                  className={`w-full px-4 py-2 rounded-lg font-medium flex items-center gap-3 transition-all ${
                    activeTab === tab.id
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <Icon size={20} />
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
