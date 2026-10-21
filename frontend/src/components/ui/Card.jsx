/**
 * Card Component
 * Base card container with consistent styling
 */

import React from 'react';

/**
 * CardHeader Sub-component
 */
function CardHeader({ title, subtitle = null, icon: Icon = null, action = null }) {
  return (
    <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
      <div className="flex items-center gap-3">
        {Icon && (
          <div className="p-2 bg-slate-100 dark:bg-slate-700 rounded-lg text-blue-600 dark:text-blue-400">
            <Icon size={20} />
          </div>
        )}
        <div>
          {title && (
            <h3 className="font-semibold text-slate-900 dark:text-white">
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              {subtitle}
            </p>
          )}
        </div>
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

/**
 * CardBody Sub-component
 */
function CardBody({ children }) {
  return <div className="px-6 py-4">{children}</div>;
}

/**
 * CardFooter Sub-component
 */
function CardFooter({ children }) {
  return (
    <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 rounded-b-lg">
      {children}
    </div>
  );
}

/**
 * Main Card Component
 */
function Card({
  children,
  className = '',
  title = null,
  subtitle = null,
  icon: Icon = null,
  footer = null,
  hover = true,
  elevation = 'base', // 'none', 'sm', 'base', 'md', 'lg'
}) {
  const elevationMap = {
    none: 'shadow-none',
    sm: 'shadow-sm',
    base: 'shadow',
    md: 'shadow-md',
    lg: 'shadow-lg',
  };

  return (
    <div
      className={`
        bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg
        ${elevationMap[elevation]}
        ${hover ? 'hover:border-slate-300 dark:hover:border-slate-600 hover:shadow-md transition-all duration-200' : ''}
        ${className}
      `}
    >
      {/* Header */}
      {(title || Icon) && (
        <CardHeader title={title} subtitle={subtitle} icon={Icon} />
      )}

      {/* Content */}
      <div className="px-6 py-4">
        {children}
      </div>

      {/* Footer */}
      {footer && (
        <CardFooter>{footer}</CardFooter>
      )}
    </div>
  );
}

// Attach sub-components
Card.Header = CardHeader;
Card.Body = CardBody;
Card.Footer = CardFooter;

export default Card;

// ==================== VARIANTS ====================

/**
 * CollapsibleCard Component
 * Card that can be expanded/collapsed
 */
export function CollapsibleCard({
  title,
  children,
  defaultOpen = true,
  icon: Icon = null,
}) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen);

  return (
    <Card title={title} icon={Icon}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between text-left hover:opacity-70 transition-opacity"
      >
        <div />
        <span className="text-slate-400 dark:text-slate-500">
          {isOpen ? '▼' : '▶'}
        </span>
      </button>
      {isOpen && <div className="mt-4">{children}</div>}
    </Card>
  );
}

/**
 * CardGrid Component
 * Layout multiple cards in a responsive grid
 */
export function CardGrid({ children, columns = 2, gap = 4 }) {
  const colClass = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
  };

  const gapClass = {
    2: 'gap-2',
    3: 'gap-3',
    4: 'gap-4',
    6: 'gap-6',
  };

  return (
    <div className={`grid ${colClass[columns]} ${gapClass[gap]}`}>
      {children}
    </div>
  );
}
