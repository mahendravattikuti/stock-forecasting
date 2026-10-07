"""
Configuration management package for the Stock Forecasting System.

This package provides utilities for loading, validating, and managing
the master configuration file with support for environment variable
substitution.
"""

from .config_loader import ConfigLoader, ConfigError

__all__ = ["ConfigLoader", "ConfigError"]
