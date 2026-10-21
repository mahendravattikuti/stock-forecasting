import React, { useState } from 'react';

/**
 * Tabs Component
 * 
 * A reusable tabbed interface component for organizing content.
 * Supports keyboard navigation (arrows, Home, End) for accessibility.
 * 
 * @param {Object} props - Component props
 * @param {Array<{label: string, value: string, content: React.ReactNode}>} props.tabs - Tab definitions
 * @param {string} [props.defaultValue] - Initially active tab value (defaults to first tab)
 * @param {function} [props.onChange] - Callback when tab changes: (value) => void
 * @param {('line'|'card'|'button')} [props.variant='line'] - Tab style variant
 * @param {string} [props.className] - Additional CSS classes for container
 * @returns {React.ReactNode} Tabs component with tab buttons and content area
 */
export const Tabs = ({
  tabs = [],
  defaultValue = null,
  onChange,
  variant = 'line',
  className = '',
}) => {
  const [activeTab, setActiveTab] = useState(
    defaultValue || tabs[0]?.value || null
  );

  const handleTabClick = (value) => {
    setActiveTab(value);
    onChange?.(value);
  };

  const handleKeyDown = (e, index) => {
    let newIndex = index;

    switch (e.key) {
      case 'ArrowLeft':
      case 'ArrowUp':
        e.preventDefault();
        newIndex = (index - 1 + tabs.length) % tabs.length;
        break;
      case 'ArrowRight':
      case 'ArrowDown':
        e.preventDefault();
        newIndex = (index + 1) % tabs.length;
        break;
      case 'Home':
        e.preventDefault();
        newIndex = 0;
        break;
      case 'End':
        e.preventDefault();
        newIndex = tabs.length - 1;
        break;
      default:
        return;
    }

    const newValue = tabs[newIndex].value;
    setActiveTab(newValue);
    onChange?.(newValue);
  };

  const activeTabData = tabs.find((tab) => tab.value === activeTab);

  return (
    <div className={`tabs tabs-${variant} ${className}`}>
      <div className="tabs-list" role="tablist">
        {tabs.map((tab, index) => (
          <button
            key={tab.value}
            role="tab"
            aria-selected={activeTab === tab.value}
            aria-controls={`tabpanel-${tab.value}`}
            className={`tab-button ${activeTab === tab.value ? 'active' : ''}`}
            onClick={() => handleTabClick(tab.value)}
            onKeyDown={(e) => handleKeyDown(e, index)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTabData && (
        <div
          id={`tabpanel-${activeTabData.value}`}
          role="tabpanel"
          className="tabs-content"
          aria-labelledby={`tab-${activeTabData.value}`}
        >
          {activeTabData.content}
        </div>
      )}
    </div>
  );
};

export default Tabs;
