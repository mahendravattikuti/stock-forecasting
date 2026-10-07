"""
Reproducibility utilities for Stock Forecasting System.

Manages random seed initialization and reproducibility artifact tracking.
"""

import os
import json
import numpy as np
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class ReproducibilityManager:
    """
    Manager for reproducibility settings and seed initialization.
    
    Ensures that all randomized operations use fixed seeds for reproducibility.
    
    Examples
    --------
    >>> rm = ReproducibilityManager(seed=42)
    >>> rm.initialize_seeds()
    >>> config = rm.document_seeds({})
    """
    
    def __init__(self, seed: int = 42):
        """
        Initialize ReproducibilityManager.
        
        Parameters
        ----------
        seed : int
            Random seed value (default: 42)
        """
        self.seed = seed
        self.seeds_initialized = False
        self.initialization_timestamp = None
        self.seeds_log: Dict[str, Any] = {}
    
    def initialize_seeds(self) -> Dict[str, Any]:
        """
        Initialize all random seeds for reproducibility.
        
        Sets seeds for:
        - numpy.random
        - random (Python standard library)
        - TensorFlow (if available)
        - PYTHONHASHSEED environment variable
        
        Returns
        -------
        Dict[str, Any]
            Dictionary of initialized seeds with status
        
        Raises
        ------
        RuntimeError
            If seed initialization fails
        """
        try:
            # Set Python standard library seed
            random.seed(self.seed)
            
            # Set numpy seed
            np.random.seed(self.seed)
            
            # Set PYTHONHASHSEED environment variable
            os.environ['PYTHONHASHSEED'] = str(self.seed)
            
            # Try to set TensorFlow seeds if available
            tf_status = 'not_installed'
            try:
                import tensorflow as tf
                tf.random.set_seed(self.seed)
                tf.config.run_functions_eagerly(True)
                os.environ['TF_DETERMINISTIC_OPS'] = '1'
                tf_status = 'initialized'
            except ImportError:
                pass
            except Exception as e:
                tf_status = f'error: {str(e)}'
            
            self.seeds_log = {
                'seed_value': self.seed,
                'timestamp': datetime.now().isoformat(),
                'numpy_seed': self.seed,
                'random_seed': self.seed,
                'tensorflow_seed': self.seed if tf_status == 'initialized' else tf_status,
                'pythonhashseed': self.seed,
                'deterministic_ops': os.environ.get('TF_DETERMINISTIC_OPS', 'not_set'),
                'status': 'success'
            }
            
            self.seeds_initialized = True
            self.initialization_timestamp = datetime.now()
            
            return self.seeds_log
            
        except Exception as e:
            self.seeds_log['status'] = f'error: {str(e)}'
            raise RuntimeError(f"Failed to initialize seeds: {e}")
    
    def document_seeds(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add seeds information to configuration dictionary.
        
        Parameters
        ----------
        config : Dict[str, Any]
            Configuration dictionary to augment
        
        Returns
        -------
        Dict[str, Any]
            Configuration with seeds documentation added
        """
        if not self.seeds_initialized:
            raise RuntimeError("Seeds not initialized. Call initialize_seeds() first.")
        
        if 'random_seeds' not in config:
            config['random_seeds'] = {}
        
        config['random_seeds'].update(self.seeds_log)
        
        return config
    
    def save_seeds_log(self, output_path: str = 'reproducibility_artifacts/v1_seeds.json') -> None:
        """
        Save seeds information to JSON file for reproducibility tracking.
        
        Parameters
        ----------
        output_path : str
            Path where to save seeds log
        """
        if not self.seeds_initialized:
            raise RuntimeError("Seeds not initialized. Call initialize_seeds() first.")
        
        # Create directory if needed
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.seeds_log, f, indent=2)


def initialize_reproducibility(seed: int = 42, config: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Initialize reproducibility settings.
    
    Convenience function to initialize seeds and optionally update config.
    
    Parameters
    ----------
    seed : int
        Random seed value (default: 42)
    config : Dict, optional
        Configuration dictionary to update
    
    Returns
    -------
    Dict[str, Any]
        Seeds log
    
    Examples
    --------
    >>> seeds_log = initialize_reproducibility(seed=42)
    >>> config = initialize_reproducibility(seed=42, config={})
    """
    rm = ReproducibilityManager(seed=seed)
    seeds_log = rm.initialize_seeds()
    
    if config is not None:
        rm.document_seeds(config)
    
    return seeds_log


if __name__ == '__main__':
    # Example usage
    rm = ReproducibilityManager(seed=42)
    seeds = rm.initialize_seeds()
    print("Seeds initialized:", json.dumps(seeds, indent=2))
