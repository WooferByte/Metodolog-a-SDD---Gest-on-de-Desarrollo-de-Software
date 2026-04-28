## ADDED Requirements

### Requirement: JWT access token generation
The system SHALL generate JWT access tokens for authenticated users with configurable expiration time.

#### Scenario: Generate access token for user
- **WHEN** user logs in with valid credentials
- **THEN** system generates JWT access token signed with HS256 algorithm, valid for 30 minutes by default

#### Scenario: Access token contains user ID
- **WHEN** JWT token is decoded
- **THEN** payload contains `sub` (subject, user ID) and `exp` (expiration timestamp)

#### Scenario: Access token includes issued-at claim
- **WHEN** JWT token is decoded
- **THEN** payload contains `iat` (issued at) timestamp

### Requirement: JWT refresh token generation
The system SHALL generate refresh tokens for long-lived sessions, separate from access tokens.

#### Scenario: Generate refresh token
- **WHEN** user logs in successfully
- **THEN** system generates unique refresh token (UUID4) with 7-day expiration

#### Scenario: Refresh token stored with user association
- **WHEN** refresh token is generated
- **THEN** token is associated with user ID and stored in database for later verification

### Requirement: JWT token validation
The system SHALL validate JWT tokens and extract user information from claims.

#### Scenario: Valid token verification
- **WHEN** endpoint receives valid JWT in Authorization header
- **THEN** token is verified using SECRET_KEY, decoded successfully, and user ID is extracted

#### Scenario: Expired token rejection
- **WHEN** endpoint receives expired JWT (exp timestamp is in past)
- **THEN** system raises HTTPException(401) with message "Token has expired"

#### Scenario: Invalid signature rejection
- **WHEN** endpoint receives JWT signed with wrong key
- **THEN** system raises HTTPException(401) with message "Invalid token signature"

#### Scenario: Malformed token rejection
- **WHEN** endpoint receives malformed token (not valid JWT format)
- **THEN** system raises HTTPException(401) with message "Invalid token format"

### Requirement: Password hashing with bcrypt
The system SHALL hash passwords using bcrypt with configurable cost factor before storage.

#### Scenario: Hash new password
- **WHEN** user registers with password
- **THEN** system hashes password using bcrypt (cost=10) before storing in database

#### Scenario: Different hash each time
- **WHEN** same password is hashed twice
- **THEN** resulting hashes are different (due to random salt) but both verify correctly

#### Scenario: Password verification succeeds
- **WHEN** user logs in and enters correct password
- **THEN** system verifies entered password against stored hash and returns True

#### Scenario: Password verification fails
- **WHEN** user logs in and enters incorrect password
- **THEN** system compares against stored hash and returns False

### Requirement: Minimum bcrypt cost factor
All passwords SHALL be hashed with bcrypt cost factor of at least 10 to prevent brute force attacks.

#### Scenario: Cost factor is sufficient
- **WHEN** password hashing is configured
- **THEN** bcrypt cost is set to 10 or higher (configurable via BCRYPT_COST env var)

#### Scenario: Hashing takes reasonable time
- **WHEN** single password is hashed
- **THEN** operation completes in ~100ms (cost=10 on modern hardware), making brute force impractical
