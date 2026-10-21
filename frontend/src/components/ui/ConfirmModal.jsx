import React, { useEffect, useRef } from 'react';

/**
 * ConfirmModal Component
 * 
 * A reusable confirmation dialog for destructive or important actions.
 * Features keyboard support (Enter to confirm, Escape to cancel), focus trap,
 * and complete ARIA implementation.
 * 
 * @param {Object} props - Component props
 * @param {boolean} props.isOpen - Whether the modal is visible
 * @param {string} props.title - Modal title
 * @param {string} props.message - Confirmation message
 * @param {string} [props.confirmText='Confirm'] - Text for confirm button
 * @param {string} [props.cancelText='Cancel'] - Text for cancel button
 * @param {('danger'|'warning'|'info')} [props.type='warning'] - Modal type (affects styling)
 * @param {boolean} [props.isLoading=false] - Show loading state on confirm button
 * @param {function} props.onConfirm - Callback when user confirms: () => void|Promise
 * @param {function} props.onCancel - Callback when user cancels: () => void
 * @param {React.ReactNode} [props.children] - Additional content in modal body
 * @returns {React.ReactNode} Modal dialog or null if not open
 */
export const ConfirmModal = ({
  isOpen,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  type = 'warning',
  isLoading = false,
  onConfirm,
  onCancel,
  children,
}) => {
  const modalRef = useRef(null);
  const cancelButtonRef = useRef(null);
  const confirmButtonRef = useRef(null);
  const previouslyFocusedElement = useRef(null);

  // Focus trap and keyboard handling
  useEffect(() => {
    if (!isOpen) return;

    // Store the element that had focus before modal opened
    previouslyFocusedElement.current = document.activeElement;

    // Focus the first focusable element (cancel button) when modal opens
    setTimeout(() => {
      cancelButtonRef.current?.focus();
    }, 0);

    // Handle keyboard events
    const handleKeyDown = (e) => {
      // Escape key closes modal
      if (e.key === 'Escape') {
        e.preventDefault();
        onCancel?.();
        return;
      }

      // Tab key: trap focus within modal
      if (e.key === 'Tab') {
        const focusableElements = modalRef.current?.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        ) || [];

        const focusableList = Array.from(focusableElements);
        const firstElement = focusableList[0];
        const lastElement = focusableList[focusableList.length - 1];
        const activeElement = document.activeElement;

        // Shift+Tab on first element: move to last
        if (e.shiftKey) {
          if (activeElement === firstElement) {
            e.preventDefault();
            lastElement?.focus();
          }
        }
        // Tab on last element: move to first
        else {
          if (activeElement === lastElement) {
            e.preventDefault();
            firstElement?.focus();
          }
        }
      }

      // Enter key on confirm button confirms action
      if (e.key === 'Enter' && document.activeElement === confirmButtonRef.current) {
        e.preventDefault();
        handleConfirm();
      }
    };

    // Prevent scrolling when modal is open
    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      // Restore previous focus when modal closes
      if (previouslyFocusedElement.current) {
        previouslyFocusedElement.current.focus();
      }

      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  const handleConfirm = async () => {
    await onConfirm?.();
  };

  const confirmButtonClass =
    type === 'danger'
      ? 'btn-danger'
      : type === 'warning'
        ? 'btn-warning'
        : 'btn-primary';

  return (
    <div 
      className="modal-overlay" 
      onClick={onCancel} 
      role="presentation"
      aria-hidden="false"
    >
      <div
        ref={modalRef}
        className={`modal modal-${type}`}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        aria-describedby="modal-message"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2 id="modal-title" className="modal-title">
            {title}
          </h2>
          <button
            className="modal-close"
            onClick={onCancel}
            aria-label="Close modal"
            type="button"
          >
            ✕
          </button>
        </div>

        <div className="modal-body">
          <p id="modal-message" className="modal-message">
            {message}
          </p>
          {children}
        </div>

        <div className="modal-footer">
          <button
            ref={cancelButtonRef}
            className="btn btn-secondary"
            onClick={onCancel}
            disabled={isLoading}
            type="button"
            aria-label={`${cancelText} this action`}
          >
            {cancelText}
          </button>
          <button
            ref={confirmButtonRef}
            className={`btn ${confirmButtonClass}`}
            onClick={handleConfirm}
            disabled={isLoading}
            aria-busy={isLoading}
            type="button"
            aria-label={`${confirmText}${isLoading ? ' - loading' : ''}`}
          >
            {isLoading ? (
              <>
                <span className="spinner-small" aria-hidden="true" />
                {confirmText}...
              </>
            ) : (
              confirmText
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;
