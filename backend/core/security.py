"""
Security utilities for JWT tokens and password hashing.

Implements:
- JWT token creation (access + refresh tokens)
- JWT token validation
- Password hashing and verification using bcrypt
- RFC compliance for JWT claims
"""
from datetime import datetime, timedelta, UTC
from typing import Any
import uuid

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


# ============================================================================
# Password Hashing
# ============================================================================


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    
    Args:
        password: Plaintext password to hash
        
    Returns:
        str: Hashed password (can be stored in database)
        
    Example:
        >>> hashed = hash_password("my-secure-password")
        >>> verify_password("my-secure-password", hashed)
        True
    """
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against its bcrypt hash.
    
    Args:
        password: Plaintext password to verify
        hashed_password: Bcrypt hash from database
        
    Returns:
        bool: True if password matches, False otherwise
        
    Example:
        >>> hashed = hash_password("password123")
        >>> verify_password("password123", hashed)
        True
        >>> verify_password("wrong", hashed)
        False
    """
    return pwd_context.verify(password, hashed_password)


# ============================================================================
# JWT Token Management
# ============================================================================


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.
    
    RFC 7519 compliant with standard claims:
    - iss (issuer): API identifier
    - sub (subject): User ID
    - aud (audience): API audience
    - exp (expiration): Token expiration time
    - iat (issued at): Token creation time
    - nbf (not before): Token not valid before this time
    - jti (JWT ID): Unique token identifier for revocation
    
    Args:
        data: Dictionary with claims (must include 'sub' for user ID)
        expires_delta: Custom expiration time; defaults to ACCESS_TOKEN_EXPIRE_MINUTES
        
    Returns:
        str: Encoded JWT token
        
    Example:
        >>> token = create_access_token({"sub": "user-123"})
        >>> decoded = verify_token(token)
        >>> decoded["sub"]
        'user-123'
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    # Standard JWT claims per RFC 7519
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(UTC),
        "nbf": datetime.now(UTC),
        "iss": "foodstore-api",
        "aud": "foodstore-client",
        "jti": str(uuid.uuid4()),  # JWT ID for revocation support
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def create_refresh_token() -> str:
    """
    Create a refresh token for obtaining new access tokens.
    
    Refresh tokens:
    - Live longer than access tokens (7 days vs 30 min)
    - Are rotated on use (old token invalidated when new one issued)
    - Can be revoked via JWT ID (jti) in token revocation list
    
    Returns:
        str: Encoded JWT refresh token
        
    Example:
        >>> refresh_token = create_refresh_token()
        >>> decoded = verify_token(refresh_token, is_refresh=True)
        >>> decoded["sub"]  # Contains user ID
    """
    jti = str(uuid.uuid4())
    
    to_encode = {
        "type": "refresh",
        "jti": jti,
    }
    
    expire = datetime.now(UTC) + timedelta(
        days=settings.refresh_token_expire_days
    )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(UTC),
        "nbf": datetime.now(UTC),
        "iss": "foodstore-api",
        "aud": "foodstore-client",
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def verify_token(token: str) -> dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Validates:
    - Signature (using SECRET_KEY and algorithm)
    - Expiration (exp claim)
    - Not before time (nbf claim)
    - Standard claims (iss, aud)
    
    Args:
        token: JWT token string from Authorization header
        
    Returns:
        dict: Decoded token payload with all claims
        
    Raises:
        HTTPException: 401 Unauthorized if token is invalid, expired, or malformed
        
    Example:
        >>> token = create_access_token({"sub": "user-123"})
        >>> payload = verify_token(token)
        >>> payload["sub"]
        'user-123'
        
        >>> expired_token = "eyJ..."
        >>> try:
        ...     verify_token(expired_token)
        ... except HTTPException as e:
        ...     print(f"Token invalid: {e.detail}")  # 401 Unauthorized
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_nbf": True,
                "verify_iss": True,
                "verify_aud": True,
            },
            audience="foodstore-client",
            issuer="foodstore-api",
            # Allow 30 seconds clock skew tolerance between servers
            access_options={"leeway": 30},
        )
        return payload
    except JWTError as e:
        print(f"JWT verification failed: {e}")
        raise credentials_exception


def extract_token_from_header(auth_header: str | None) -> str:
    """
    Extract JWT token from Authorization header.
    
    Expected format: "Bearer <token>"
    
    Args:
        auth_header: Authorization header value (e.g., "Bearer eyJ...")
        
    Returns:
        str: Extracted token
        
    Raises:
        HTTPException: 401 Unauthorized if header is malformed or missing
        
    Example:
        >>> auth_header = "Bearer eyJhbGc..."
        >>> token = extract_token_from_header(auth_header)
        >>> token
        'eyJhbGc...'
    """
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Use 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return parts[1]
