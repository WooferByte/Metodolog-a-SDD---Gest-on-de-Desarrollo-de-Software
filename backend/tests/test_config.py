"""
Tests for core/config.py - environment configuration loading.
"""
import os
import pytest
from pydantic import ValidationError

# We'll test config loading behavior


def test_config_loads_from_env():
    """Test that config loads required environment variables."""
    # This test requires .env to be present with valid values
    try:
        from core.config import settings
        
        # Check that critical values are loaded
        assert settings.database_url is not None
        assert settings.secret_key is not None
        assert settings.algorithm == "HS256"
        assert settings.access_token_expire_minutes == 30
        assert settings.refresh_token_expire_days == 7
    except ValidationError as e:
        pytest.fail(f"Config validation failed: {e}")


def test_config_environment_modes():
    """Test that config supports different environment modes."""
    from core.config import Settings
    
    # Should support dev/test/prod checks
    # Create a test instance with dev environment
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("ENV=development\n")
        f.write("DATABASE_URL=postgresql+asyncpg://test:test@localhost/test\n")
        f.write("SECRET_KEY=test-secret-key-minimum-256-bits-test\n")
        env_file = f.name
    
    try:
        settings = Settings(_env_file=env_file)
        assert settings.is_dev() is True
        assert settings.is_test() is False
        assert settings.is_prod() is False
    finally:
        os.unlink(env_file)


def test_config_cors_origins_parsing():
    """Test that CORS origins are parsed correctly."""
    from core.config import settings
    
    # CORS origins should be a list
    assert isinstance(settings.cors_origins, list)
    assert len(settings.cors_origins) > 0


def test_config_defaults():
    """Test that config has sensible defaults."""
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("DATABASE_URL=postgresql+asyncpg://test:test@localhost/test\n")
        f.write("SECRET_KEY=test-secret-key-minimum-256-bits-test\n")
        env_file = f.name
    
    try:
        from core.config import Settings
        settings = Settings(_env_file=env_file)
        
        # Check defaults
        assert settings.access_token_expire_minutes == 30
        assert settings.refresh_token_expire_days == 7
        assert settings.bcrypt_cost == 10
        assert settings.algorithm == "HS256"
    finally:
        os.unlink(env_file)
