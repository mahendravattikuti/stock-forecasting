import React, { useState, useRef, useEffect } from 'react';
import '../../../styles/Tooltip.css';

/**
 * Tooltip Component
 * 
 * Displays a small popup with additional information when hovering over or focusing an element.
 * Includes automatic positioning to avoid viewport edges.
 * 
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - The element that triggers the tooltip
 * @param {string} props.content - Text content of the tooltip
 * @param {('top'|'bottom'|'left'|'right')} [props.position='top'] - Preferred tooltip position
 * @param {number} [props.delay=200] - Delay before showing tooltip (ms)
 * @param {string} [props.className] - Additional CSS classes
 * @returns {React.ReactNode} Tooltip container with trigger element
 */
export const Tooltip = ({
  children,
  content,
  position = 'top',
  delay = 200,
  className = '',
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [actualPosition, setActualPosition] = useState(position);
  const triggerRef = useRef(null);
  const tooltipRef = useRef(null);
  const timeoutRef = useRef(null);

  useEffect(() => {
    const handleMouseEnter = () => {
      timeoutRef.current = setTimeout(() => {
        setIsVisible(true);
      }, delay);
    };

    const handleMouseLeave = () => {
      clearTimeout(timeoutRef.current);
      setIsVisible(false);
    };

    const handleFocus = () => {
      setIsVisible(true);
    };

    const handleBlur = () => {
      setIsVisible(false);
    };

    if (triggerRef.current) {
      triggerRef.current.addEventListener('mouseenter', handleMouseEnter);
      triggerRef.current.addEventListener('mouseleave', handleMouseLeave);
      triggerRef.current.addEventListener('focus', handleFocus, true);
      triggerRef.current.addEventListener('blur', handleBlur, true);
    }

    return () => {
      if (triggerRef.current) {
        triggerRef.current.removeEventListener('mouseenter', handleMouseEnter);
        triggerRef.current.removeEventListener('mouseleave', handleMouseLeave);
        triggerRef.current.removeEventListener('focus', handleFocus, true);
        triggerRef.current.removeEventListener('blur', handleBlur, true);
      }
    };
  }, [delay]);

  // Adjust position if tooltip goes off-screen
  useEffect(() => {
    if (!isVisible || !tooltipRef.current || !triggerRef.current) return;

    const rect = tooltipRef.current.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let newPosition = position;

    if (rect.left < 0) newPosition = 'right';
    else if (rect.right > viewportWidth) newPosition = 'left';
    else if (rect.top < 0) newPosition = 'bottom';
    else if (rect.bottom > viewportHeight) newPosition = 'top';

    setActualPosition(newPosition);
  }, [isVisible, position]);

  return (
    <div className={`tooltip-wrapper ${className}`} ref={triggerRef}>
      {children}
      {isVisible && (
        <div
          ref={tooltipRef}
          className={`tooltip tooltip-${actualPosition}`}
          role="tooltip"
        >
          {content}
        </div>
      )}
    </div>
  );
};

export default Tooltip;
