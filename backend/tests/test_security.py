"""
Tests for core/security.py - JWT tokens and password hashing.
"""
import pytest
from datetime import timedelta
from fastapi import HTTPException

from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    extract_token_from_header,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_creates_different_hashes(self):
        """Same password hashed twice should create different hashes (due to salt)."""
        password = "my-secure-password-123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different (due to random salt)
        assert hash1 != hash2
        # But both should verify against the original password
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_verify_password_success(self):
        """Correct password should verify successfully."""
        password = "correct-password"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        """Wrong password should not verify."""
        password = "correct-password"
        wrong_password = "wrong-password"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False

    def test_hash_password_different_inputs(self):
        """Different passwords should produce different hashes."""
        hash1 = hash_password("password1")
        hash2 = hash_password("password2")
        
        assert hash1 != hash2
        assert not verify_password("password1", hash2)
        assert not verify_password("password2", hash1)


class TestAccessToken:
    """Tests for access token creation and validation."""

    def test_create_access_token(self):
        """Access token should be created successfully."""
        data = {"sub": "user-123"}
        token = create_access_token(data)
        
        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0
        # Token should be JWT (3 parts separated by dots)
        assert token.count(".") == 2

    def test_access_token_with_custom_expiration(self):
        """Access token should respect custom expiration time."""
        data = {"sub": "user-123"}
        expires_delta = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires_delta)
        
        # Token should be created
        assert token is not None

    def test_verify_access_token(self):
        """Verify token should decode and validate access token."""
        data = {"sub": "user-456"}
        token = create_access_token(data)
        
        # Decode token
        decoded = verify_token(token)
        
        # Check claims
        assert decoded["sub"] == "user-456"
        assert "exp" in decoded
        assert "iat" in decoded
        assert "nbf" in decoded
        assert "jti" in decoded
        assert decoded["iss"] == "foodstore-api"
        assert decoded["aud"] == "foodstore-client"

    def test_verify_token_invalid_signature(self):
        """Invalid signature should raise 401 Unauthorized."""
        data = {"sub": "user-123"}
        token = create_access_token(data)
        
        # Tamper with token
        tampered = token[:-10] + "tampered!!"
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_token(tampered)
        
        assert exc_info.value.status_code == 401

    def test_verify_token_malformed(self):
        """Malformed token should raise 401 Unauthorized."""
        with pytest.raises(HTTPException) as exc_info:
            verify_token("not.a.token")
        
        assert exc_info.value.status_code == 401

    def test_access_token_contains_custom_claims(self):
        """Access token should include custom claims."""
        data = {"sub": "user-123", "roles": ["admin", "user"], "email": "user@example.com"}
        token = create_access_token(data)
        
        decoded = verify_token(token)
        
        assert decoded["sub"] == "user-123"
        assert decoded["roles"] == ["admin", "user"]
        assert decoded["email"] == "user@example.com"


class TestRefreshToken:
    """Tests for refresh token creation and validation."""

    def test_create_refresh_token(self):
        """Refresh token should be created successfully."""
        token = create_refresh_token()
        
        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0
        # Token should be JWT (3 parts separated by dots)
        assert token.count(".") == 2

    def test_refresh_token_has_type_claim(self):
        """Refresh token should have 'type': 'refresh' claim."""
        token = create_refresh_token()
        
        decoded = verify_token(token)
        
        assert decoded.get("type") == "refresh"

    def test_refresh_token_has_jti(self):
        """Refresh token should have unique JTI for revocation."""
        token1 = create_refresh_token()
        token2 = create_refresh_token()
        
        decoded1 = verify_token(token1)
        decoded2 = verify_token(token2)
        
        # Each token should have unique JTI
        assert decoded1["jti"] != decoded2["jti"]


class TestTokenExtraction:
    """Tests for extracting token from Authorization header."""

    def test_extract_valid_bearer_token(self):
        """Should extract token from valid Bearer header."""
        data = {"sub": "user-123"}
        token = create_access_token(data)
        
        auth_header = f"Bearer {token}"
        extracted = extract_token_from_header(auth_header)
        
        assert extracted == token

    def test_extract_missing_header(self):
        """Missing Authorization header should raise 401."""
        with pytest.raises(HTTPException) as exc_info:
            extract_token_from_header(None)
        
        assert exc_info.value.status_code == 401

    def test_extract_empty_header(self):
        """Empty Authorization header should raise 401."""
        with pytest.raises(HTTPException) as exc_info:
            extract_token_from_header("")
        
        assert exc_info.value.status_code == 401

    def test_extract_invalid_bearer_format(self):
        """Invalid Bearer format should raise 401."""
        with pytest.raises(HTTPException) as exc_info:
            extract_token_from_header("InvalidFormat token123")
        
        assert exc_info.value.status_code == 401

    def test_extract_no_token_value(self):
        """Bearer without token should raise 401."""
        with pytest.raises(HTTPException) as exc_info:
            extract_token_from_header("Bearer")
        
        assert exc_info.value.status_code == 401

    def test_extract_case_insensitive(self):
        """Bearer prefix should be case-insensitive."""
        data = {"sub": "user-123"}
        token = create_access_token(data)
        
        # Test different cases
        for prefix in ["bearer", "Bearer", "BEARER"]:
            auth_header = f"{prefix} {token}"
            extracted = extract_token_from_header(auth_header)
            assert extracted == token
