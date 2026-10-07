"""
Structured logging configuration for Stock Forecasting System.

Provides dual-output logging: console (INFO level) and file (DEBUG level).
"""

import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON for machine readability."""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Parameters
        ----------
        record : logging.LogRecord
            Log record to format
        
        Returns
        -------
        str
            JSON-formatted log message
        """
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line_number': record.lineno
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def configure_logging(
    log_dir: str = 'logs',
    log_name: Optional[str] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG
) -> logging.Logger:
    """
    Configure structured logging with console and file handlers.
    
    Creates a logger that outputs to:
    - Console: INFO level and above
    - File: DEBUG level and above (JSON format for machine readability)
    
    Parameters
    ----------
    log_dir : str
        Directory to save log files (default: 'logs')
    log_name : str, optional
        Name for logger (default: 'stock_forecasting')
    console_level : int
        Console handler log level (default: logging.INFO)
    file_level : int
        File handler log level (default: logging.DEBUG)
    
    Returns
    -------
    logging.Logger
        Configured logger instance
    
    Examples
    --------
    >>> logger = configure_logging(log_dir='logs')
    >>> logger.info("Pipeline started")
    >>> logger.debug("Detailed debug information")
    """
    
    if log_name is None:
        log_name = 'stock_forecasting'
    
    # Create logs directory if it doesn't exist
    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)  # Capture all messages
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Create console handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Create file handler (DEBUG and above, JSON format)
    log_filename = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_filepath = log_dir_path / log_filename
    
    file_handler = logging.FileHandler(log_filepath)
    file_handler.setLevel(file_level)
    json_formatter = JSONFormatter()
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    
    # Log initial message
    logger.info(f"Logging initialized. Log file: {log_filepath}")
    
    return logger


class StructuredLogger:
    """
    Wrapper around standard logger for structured logging with metadata.
    
    Examples
    --------
    >>> slog = StructuredLogger(configure_logging())
    >>> slog.log_event('INFO', 'data_acquisition', symbol='AAPL', rows=2523)
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize StructuredLogger.
        
        Parameters
        ----------
        logger : logging.Logger
            Configured logger instance
        """
        self.logger = logger
    
    def log_event(
        self,
        level: str,
        event_type: str,
        message: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log a structured event with metadata.
        
        Parameters
        ----------
        level : str
            Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        event_type : str
            Type of event (e.g., 'data_acquisition', 'feature_engineering')
        message : str, optional
            Human-readable message
        **kwargs
            Additional metadata to include in log
        
        Examples
        --------
        >>> slog.log_event('INFO', 'data_acquisition', 
        ...                symbol='AAPL', rows=2523, 
        ...                message='Data acquisition complete')
        """
        log_data = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        log_message = message or event_type
        if kwargs:
            log_message += f" | {json.dumps(log_data)}"
        
        log_level = getattr(logging, level.upper())
        self.logger.log(log_level, log_message)


# Create default logger for module-level usage
_default_logger = None


def get_logger(name: str = 'stock_forecasting') -> logging.Logger:
    """
    Get or create logger instance.
    
    Parameters
    ----------
    name : str
        Logger name
    
    Returns
    -------
    logging.Logger
        Logger instance
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = configure_logging()
    return logging.getLogger(name)


if __name__ == '__main__':
    # Example usage
    logger = configure_logging()
    slog = StructuredLogger(logger)
    
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    slog.log_event('INFO', 'test_event', symbol='AAPL', rows=100)
