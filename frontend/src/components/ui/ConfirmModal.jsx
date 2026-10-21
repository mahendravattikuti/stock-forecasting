import React, { useEffect } from 'react';

/**
 * ConfirmModal Component
 * 
 * A reusable confirmation dialog for destructive or important actions.
 * Features keyboard support (Enter to confirm, Escape to cancel) and focus management.
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
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onCancel?.();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
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
    <div className="modal-overlay" onClick={onCancel} role="presentation">
      <div
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
            className="btn btn-secondary"
            onClick={onCancel}
            disabled={isLoading}
          >
            {cancelText}
          </button>
          <button
            className={`btn ${confirmButtonClass}`}
            onClick={handleConfirm}
            disabled={isLoading}
            aria-busy={isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner-small" />
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
