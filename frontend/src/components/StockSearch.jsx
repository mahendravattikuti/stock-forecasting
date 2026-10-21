import React, { useState, useEffect, useRef } from 'react';
import { Search, X, TrendingUp } from 'lucide-react';
import { Tooltip } from './ui';

/**
 * StockSearch Component
 * 
 * Autocomplete search for stock symbols with suggestions and filtering.
 * Integrates with popular stocks and API for real-time quotes.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {string} props.value - Current search input value
 * @param {function} props.onChange - Callback when search value changes
 * @param {function} props.onSelect - Callback when a stock is selected
 * @param {boolean} [props.loading] - Show loading state
 * @param {Array<Object>} [props.suggestions] - Stock suggestions to display
 * @returns {React.ReactNode} Autocomplete search component
 */
export function StockSearch({
  value = '',
  onChange,
  onSelect,
  loading = false,
  suggestions = [],
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const searchRef = useRef(null);
  const listRef = useRef(null);

  // Popular stocks for quick access
  const popularStocks = [
    { symbol: 'AAPL', name: 'Apple Inc.' },
    { symbol: 'MSFT', name: 'Microsoft Corporation' },
    { symbol: 'GOOGL', name: 'Alphabet Inc.' },
    { symbol: 'AMZN', name: 'Amazon.com Inc.' },
    { symbol: 'TSLA', name: 'Tesla Inc.' },
    { symbol: 'NVDA', name: 'NVIDIA Corporation' },
    { symbol: 'META', name: 'Meta Platforms Inc.' },
    { symbol: 'NFLX', name: 'Netflix Inc.' },
  ];

  // Filter suggestions based on input
  useEffect(() => {
    if (!value.trim()) {
      setFilteredSuggestions(popularStocks);
      setSelectedIndex(-1);
      return;
    }

    const filtered = [
      ...suggestions,
      ...popularStocks.filter(
        (stock) =>
          stock.symbol.includes(value.toUpperCase()) &&
          !suggestions.some((s) => s.symbol === stock.symbol)
      ),
    ].slice(0, 8);

    setFilteredSuggestions(filtered);
    setSelectedIndex(-1);
  }, [value, suggestions]);

  // Handle keyboard navigation
  const handleKeyDown = (e) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        setIsOpen(true);
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < filteredSuggestions.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev > 0 ? prev - 1 : filteredSuggestions.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0) {
          handleSelect(filteredSuggestions[selectedIndex]);
        } else if (value.trim()) {
          onSelect({ symbol: value.toUpperCase(), name: '' });
          setIsOpen(false);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        break;
      default:
        break;
    }
  };

  const handleSelect = (stock) => {
    onSelect(stock);
    setIsOpen(false);
    setSelectedIndex(-1);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        searchRef.current &&
        !searchRef.current.contains(e.target)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={searchRef} className="relative w-full">
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-3.5 text-slate-400" size={20} aria-hidden="true" />
        <input
          type="text"
          value={value}
          onChange={(e) => {
            onChange(e.target.value.toUpperCase());
            setIsOpen(true);
          }}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsOpen(true)}
          placeholder="Search stock symbol (e.g., AAPL, MSFT)"
          aria-label="Search for stock symbol"
          aria-autocomplete="list"
          aria-expanded={isOpen}
          aria-controls="stock-listbox"
          aria-busy={loading}
          className="w-full bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg pl-10 pr-10 py-2.5 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:ring-2 focus:ring-blue-500 dark:focus:ring-cyan-400 transition-all"
        />
        {value && (
          <button
            onClick={() => {
              onChange('');
              setIsOpen(true);
            }}
            className="absolute right-3 top-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
            aria-label="Clear search"
          >
            <X size={18} aria-hidden="true" />
          </button>
        )}
      </div>

      {/* Dropdown Suggestions - Using ARIA Listbox Pattern */}
      {isOpen && filteredSuggestions.length > 0 && (
        <ul
          id="stock-listbox"
          ref={listRef}
          role="listbox"
          className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg z-50 overflow-hidden"
        >
          {filteredSuggestions.map((stock, index) => (
            <li key={stock.symbol} role="none">
              <button
                role="option"
                aria-selected={index === selectedIndex}
                onClick={() => handleSelect(stock)}
                onMouseEnter={() => setSelectedIndex(index)}
                className={`w-full text-left px-4 py-2.5 flex items-center justify-between transition-colors focus:ring-2 focus:ring-blue-500 focus:outline-none ${
                  index === selectedIndex
                    ? 'bg-blue-100 dark:bg-blue-900'
                    : 'hover:bg-slate-100 dark:hover:bg-slate-700'
                }`}
                aria-label={`${stock.symbol}${stock.name ? ': ' + stock.name : ''}`}
              >
                <div>
                  <p className="font-semibold text-slate-900 dark:text-white">
                    {stock.symbol}
                  </p>
                  {stock.name && (
                    <p className="text-xs text-slate-600 dark:text-slate-400">
                      {stock.name}
                    </p>
                  )}
                </div>
                <Tooltip content="Click to predict" position="left">
                  <TrendingUp
                    size={16}
                    className="text-slate-400 dark:text-slate-500"
                    aria-hidden="true"
                  />
                </Tooltip>
              </button>
            </li>
          ))}
        </ul>
      )}

      {/* Loading State */}
      {loading && (
        <div 
          className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-3 text-center text-sm text-slate-600 dark:text-slate-400"
          role="status"
          aria-live="polite"
        >
          Loading suggestions...
        </div>
      )}

      {/* No Results */}
      {isOpen && value && filteredSuggestions.length === 0 && !loading && (
        <div 
          className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-3 text-center text-sm text-slate-600 dark:text-slate-400"
          role="status"
          aria-live="polite"
        >
          No stocks found. Press Enter to search "{value}"
        </div>
      )}
    </div>
  );
}

export default StockSearch;
