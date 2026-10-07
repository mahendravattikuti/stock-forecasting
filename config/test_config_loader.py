"""
Unit tests for ConfigLoader class.

Tests cover:
- Loading and parsing JSON configuration
- Schema validation
- Nested key access with dot notation
- Environment variable substitution
- Error handling for missing files and invalid JSON
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

from config.config_loader import ConfigLoader, ConfigError


class TestConfigLoaderBasics:
    """Test basic ConfigLoader functionality."""

    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        return {
            "pipeline_metadata": {
                "execution_timestamp": "2024-01-19T10:00:00Z",
                "pipeline_version": "1.0",
                "stage": "Stage_1"
            },
            "environment": {
                "python_version": "3.10.12",
                "numpy_version": "1.24.3"
            },
            "random_seeds": {
                "numpy_seed": 42,
                "random_seed": 42,
                "tensorflow_seed": 42
            },
            "data_acquisition": {
                "primary_source": "iex_cloud",
                "iex_api_token": "test_token"
            },
            "data_cleaning": {},
            "feature_engineering": {},
            "data_splitting": {},
            "preprocessing_artifacts": {},
            "baseline_models": {},
            "ablation_studies": {},
            "evaluation": {},
            "reporting": {}
        }

    @pytest.fixture
    def config_file(self, sample_config):
        """Create a temporary config file."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump(sample_config, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if Path(temp_path).exists():
            os.unlink(temp_path)

    def test_init_with_valid_file(self, config_file):
        """Test initialization with existing config file."""
        loader = ConfigLoader(config_file)
        assert loader.config_path == config_file
        assert loader.config == {}

    def test_init_with_missing_file(self):
        """Test initialization with non-existent config file."""
        with pytest.raises(ConfigError, match="Configuration file not found"):
            ConfigLoader('/nonexistent/path/config.json')

    def test_load_config(self, config_file, sample_config):
        """Test loading configuration from file."""
        loader = ConfigLoader(config_file)
        loaded_config = loader.load_config()
        
        assert loaded_config == sample_config
        assert loader.config == sample_config

    def test_load_config_invalid_json(self):
        """Test loading invalid JSON file."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(ConfigError, match="Failed to parse JSON"):
                loader.load_config()
        finally:
            if Path(temp_path).exists():
                os.unlink(temp_path)


class TestSchemaValidation:
    """Test configuration schema validation."""

    @pytest.fixture
    def valid_config_file(self):
        """Create a temporary valid config file."""
        config = {
            "pipeline_metadata": {},
            "environment": {},
            "random_seeds": {},
            "data_acquisition": {},
            "data_cleaning": {},
            "feature_engineering": {},
            "data_splitting": {},
            "preprocessing_artifacts": {},
            "baseline_models": {},
            "ablation_studies": {},
            "evaluation": {},
            "reporting": {}
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump(config, f)
            temp_path = f.name
        
        yield temp_path
        
        if Path(temp_path).exists():
            os.unlink(temp_path)

    @pytest.fixture
    def invalid_config_file(self):
        """Create a temporary config file missing required keys."""
        config = {
            "pipeline_metadata": {},
            "environment": {}
            # Missing other required keys
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump(config, f)
            temp_path = f.name
        
        yield temp_path
        
        if Path(temp_path).exists():
            os.unlink(temp_path)

    def test_validate_schema_valid(self, valid_config_file):
        """Test schema validation with valid config."""
        loader = ConfigLoader(valid_config_file)
        loader.load_config()
        
        assert loader.validate_schema() is True

    def test_validate_schema_missing_keys(self, invalid_config_file):
        """Test schema validation with missing required keys."""
        loader = ConfigLoader(invalid_config_file)
        loader.load_config()
        
        with pytest.raises(ConfigError, match="missing required keys"):
            loader.validate_schema()

    def test_validate_schema_before_load(self, valid_config_file):
        """Test schema validation before load raises error."""
        loader = ConfigLoader(valid_config_file)
        
        with pytest.raises(ConfigError, match="Configuration not loaded"):
            loader.validate_schema()


class TestNestedKeyAccess:
    """Test nested key access with dot notation."""

    @pytest.fixture
    def config_file(self):
        """Create config file with nested structure."""
        config = {
            "pipeline_metadata": {
                "execution_timestamp": "2024-01-19T10:00:00Z",
                "nested": {
                    "deep_value": "found"
                }
            },
            "environment": {
                "python_version": "3.10.12"
            },
            "random_seeds": {
                "numpy_seed": 42
            },
            "data_acquisition": {},
            "data_cleaning": {},
            "feature_engineering": {},
            "data_splitting": {},
            "preprocessing_artifacts": {},
            "baseline_models": {},
            "ablation_studies": {},
            "evaluation": {},
            "reporting": {}
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump(config, f)
            temp_path = f.name
        
        yield temp_path
        
        if Path(temp_path).exists():
            os.unlink(temp_path)

    def test_get_top_level_key(self, config_file):
        """Test retrieval of top-level key."""
        loader = ConfigLoader(config_file)
        loader.load_config()
        
        result = loader.get('pipeline_metadata')
        assert isinstance(result, dict)
        assert 'execution_timestamp' in result

    def test_get_nested_key(self, config_file):
        """Test retrieval of nested key with dot notation."""
        loader = ConfigLoader(config_file)
        loader.load_config()
        
        result = loader.get('pipeline_metadata.execution_timestamp')
        assert result == "2024-01-19T10:00:00Z"

    def test_get_deep_nested_key(self, config_file):
        """Test retrieval of deeply nested key."""
        loader = ConfigLoader(config_file)
        loader.load_config()
        
        result = loader.get('pipeline_metadata.nested.deep_value')
        assert result == "found"

    def test_get_missing_key_returns_default(self, config_file):
        """Test that missing key returns default value."""
        loader = ConfigLoader(config_file)
        loader.load_config()
        
        result = loader.get('nonexistent.key', default='default_value')
        assert result == 'default_value'

    def test_get_missing_key_no_default(self, config_file):
        """Test that missing key without default returns None."""
        loader = ConfigLoader(config_file)
        loader.load_config()
        
        result = loader.get('nonexistent.key')
        assert result is None

    def test_get_before_load(self, config_file):
        """Test get before load raises error."""
        loader = ConfigLoader(config_file)
        
        with pytest.raises(ConfigError, match="Configuration not loaded"):
            loader.get('pipeline_metadata.execution_timestamp')

    def test_get_with_numeric_default(self, config_file):
        """Test get with numeric default value."""
        loader = ConfigLoader(config_file)
        loader.load_config()
        
        result = loader.get('random_seeds.numpy_seed')
        assert result == 42
        
        result = loader.get('random_seeds.missing_seed', default=100)
        assert result == 100


class TestEnvironmentVariableSubstitution:
    """Test environment variable substitution."""

    @pytest.fixture
    def config_with_env_vars(self):
        """Create config file with environment variable placeholders."""
        config = {
            "pipeline_metadata": {},
            "environment": {},
            "random_seeds": {},
            "data_acquisition": {
                "iex_api_token": "${IEX_CLOUD_TOKEN}",
                "api_key_backup": "static_value"
            },
            "data_cleaning": {},
            "feature_engineering": {},
            "data_splitting": {},
            "preprocessing_artifacts": {},
            "baseline_models": {},
            "ablation_studies": {},
            "evaluation": {},
            "reporting": {}
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump(config, f)
            temp_path = f.name
        
        yield temp_path
        
        if Path(temp_path).exists():
            os.unlink(temp_path)

    def test_override_from_env_success(self, config_with_env_vars):
        """Test successful environment variable substitution."""
        os.environ['IEX_CLOUD_TOKEN'] = 'sk_live_test_token_123'
        
        try:
            loader = ConfigLoader(config_with_env_vars)
            loader.load_config()
            loader.override_from_env()
            
            token = loader.get('data_acquisition.iex_api_token')
            assert token == 'sk_live_test_token_123'
            
            static_value = loader.get('data_acquisition.api_key_backup')
            assert static_value == 'static_value'
        finally:
            if 'IEX_CLOUD_TOKEN' in os.environ:
                del os.environ['IEX_CLOUD_TOKEN']

    def test_override_from_env_missing_var(self, config_with_env_vars):
        """Test that missing environment variable raises error."""
        # Ensure variable doesn't exist
        if 'IEX_CLOUD_TOKEN' in os.environ:
            del os.environ['IEX_CLOUD_TOKEN']
        
        loader = ConfigLoader(config_with_env_vars)
        loader.load_config()
        
        with pytest.raises(ConfigError, match="Environment variable 'IEX_CLOUD_TOKEN' is not set"):
            loader.override_from_env()

    def test_override_with_multiple_env_vars(self):
        """Test substitution with multiple environment variables."""
        config = {
            "pipeline_metadata": {},
            "environment": {},
            "random_seeds": {},
            "data_acquisition": {
                "token1": "${VAR1}",
                "token2": "${VAR2}",
                "nested": {
                    "token3": "${VAR3}"
                }
            },
            "data_cleaning": {},
            "feature_engineering": {},
            "data_splitting": {},
            "preprocessing_artifacts": {},
            "baseline_models": {},
            "ablation_studies": {},
            "evaluation": {},
            "reporting": {}
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump(config, f)
            temp_path = f.name
        
        try:
            os.environ['VAR1'] = 'value1'
            os.environ['VAR2'] = 'value2'
            os.environ['VAR3'] = 'value3'
            
            loader = ConfigLoader(temp_path)
            loader.load_config()
            loader.override_from_env()
            
            assert loader.get('data_acquisition.token1') == 'value1'
            assert loader.get('data_acquisition.token2') == 'value2'
            assert loader.get('data_acquisition.nested.token3') == 'value3'
        finally:
            for var in ['VAR1', 'VAR2', 'VAR3']:
                if var in os.environ:
                    del os.environ[var]
            
            if Path(temp_path).exists():
                os.unlink(temp_path)

    def test_override_with_prefix_suffix(self):
        """Test environment variable substitution with prefix/suffix."""
        config = {
            "pipeline_metadata": {},
            "environment": {},
            "random_seeds": {},
            "data_acquisition": {
                "database_url": "postgresql://${DB_USER}:${DB_PASS}@localhost/stock_db"
            },
            "data_cleaning": {},
            "feature_engineering": {},
            "data_splitting": {},
            "preprocessing_artifacts": {},
            "baseline_models": {},
            "ablation_studies": {},
            "evaluation": {},
            "reporting": {}
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump(config, f)
            temp_path = f.name
        
        try:
            os.environ['DB_USER'] = 'admin'
            os.environ['DB_PASS'] = 'secret123'
            
            loader = ConfigLoader(temp_path)
            loader.load_config()
            loader.override_from_env()
            
            url = loader.get('data_acquisition.database_url')
            assert url == "postgresql://admin:secret123@localhost/stock_db"
        finally:
            for var in ['DB_USER', 'DB_PASS']:
                if var in os.environ:
                    del os.environ[var]
            
            if Path(temp_path).exists():
                os.unlink(temp_path)

    def test_override_before_load(self, config_with_env_vars):
        """Test override_from_env before load raises error."""
        loader = ConfigLoader(config_with_env_vars)
        
        with pytest.raises(ConfigError, match="Configuration not loaded"):
            loader.override_from_env()


class TestSaveConfig:
    """Test configuration saving."""

    @pytest.fixture
    def config_file(self):
        """Create config file for testing."""
        config = {
            "pipeline_metadata": {
                "execution_timestamp": "2024-01-19T10:00:00Z"
            },
            "environment": {},
            "random_seeds": {},
            "data_acquisition": {},
            "data_cleaning": {},
            "feature_engineering": {},
            "data_splitting": {},
            "preprocessing_artifacts": {},
            "baseline_models": {},
            "ablation_studies": {},
            "evaluation": {},
            "reporting": {}
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump(config, f)
            temp_path = f.name
        
        yield temp_path
        
        if Path(temp_path).exists():
            os.unlink(temp_path)

    def test_save_config(self, config_file):
        """Test saving configuration to file."""
        loader = ConfigLoader(config_file)
        loader.load_config()
        
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            output_path = f.name
        
        try:
            loader.save_config(output_path)
            
            # Verify saved file
            with open(output_path, 'r') as f:
                saved_config = json.load(f)
            
            assert saved_config == loader.config
        finally:
            if Path(output_path).exists():
                os.unlink(output_path)

    def test_save_config_before_load(self, config_file):
        """Test save_config before load raises error."""
        loader = ConfigLoader(config_file)
        
        with pytest.raises(ConfigError, match="Configuration not loaded"):
            loader.save_config('/tmp/output.json')


class TestIntegration:
    """Integration tests for ConfigLoader."""

    def test_full_workflow(self):
        """Test complete workflow: load -> validate -> get -> override -> save."""
        config = {
            "pipeline_metadata": {
                "execution_timestamp": "2024-01-19T10:00:00Z"
            },
            "environment": {
                "python_version": "3.10.12"
            },
            "random_seeds": {
                "numpy_seed": 42
            },
            "data_acquisition": {
                "iex_api_token": "${IEX_CLOUD_TOKEN}",
                "lookback_years": 10
            },
            "data_cleaning": {},
            "feature_engineering": {},
            "data_splitting": {},
            "preprocessing_artifacts": {},
            "baseline_models": {},
            "ablation_studies": {},
            "evaluation": {},
            "reporting": {}
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump(config, f)
            temp_path = f.name
        
        try:
            os.environ['IEX_CLOUD_TOKEN'] = 'test_token_xyz'
            
            # Load
            loader = ConfigLoader(temp_path)
            loader.load_config()
            
            # Validate
            assert loader.validate_schema() is True
            
            # Get values
            assert loader.get('random_seeds.numpy_seed') == 42
            assert loader.get('data_acquisition.lookback_years') == 10
            
            # Override
            loader.override_from_env()
            assert loader.get('data_acquisition.iex_api_token') == 'test_token_xyz'
            
            # Save
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False
            ) as f:
                output_path = f.name
            
            loader.save_config(output_path)
            
            # Verify saved config has substituted values
            with open(output_path, 'r') as f:
                saved = json.load(f)
            
            assert saved['data_acquisition']['iex_api_token'] == 'test_token_xyz'
            
            if Path(output_path).exists():
                os.unlink(output_path)
        finally:
            if 'IEX_CLOUD_TOKEN' in os.environ:
                del os.environ['IEX_CLOUD_TOKEN']
            
            if Path(temp_path).exists():
                os.unlink(temp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
