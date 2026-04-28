## ADDED Requirements

### Requirement: Environment-based configuration
The system SHALL load configuration from environment variables with support for multiple deployment environments (development, test, production).

#### Scenario: Development mode configuration
- **WHEN** ENV variable is set to "development"
- **THEN** DEBUG mode is enabled, CORS allows localhost:3000, database uses PostgreSQL with dev credentials

#### Scenario: Production mode configuration
- **WHEN** ENV variable is set to "production"
- **THEN** DEBUG mode is disabled, CORS restricted to approved domains, database uses production connection string, SECRET_KEY is loaded from env

#### Scenario: Test mode configuration
- **WHEN** ENV variable is set to "test"
- **THEN** database uses SQLite in-memory, secrets are test defaults, no external dependencies (MercadoPago sandbox mode)

### Requirement: Environment variable validation
All required environment variables SHALL be validated at application startup; missing or invalid values SHALL cause immediate failure with clear error messages.

#### Scenario: Missing required variable
- **WHEN** application starts without DATABASE_URL environment variable
- **THEN** application fails with ValidationError indicating `DATABASE_URL` is required

#### Scenario: Invalid variable format
- **WHEN** APPLICATION starts with invalid DATABASE_URL format (e.g., malformed connection string)
- **THEN** application fails with ValidationError indicating format requirements

#### Scenario: All variables present and valid
- **WHEN** all required variables (DATABASE_URL, SECRET_KEY, ENV, ALGORITHM, etc.) are set correctly
- **THEN** application starts successfully and config is available to all modules

### Requirement: Configuration values
The system SHALL define and expose the following configuration values:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: HMAC secret for JWT signing
- `ENV`: Deployment environment (development|test|production)
- `ALGORITHM`: JWT signing algorithm (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: TTL for access tokens (default 30)
- `REFRESH_TOKEN_EXPIRE_DAYS`: TTL for refresh tokens (default 7)
- `BCRYPT_COST`: Bcrypt hashing cost factor (default 10)
- `DEBUG`: Boolean enabling/disabling debug mode
- `CORS_ORIGINS`: Comma-separated list of allowed CORS origins
- `MERCADOPAGO_API_KEY`: API key for MercadoPago integration
- `RATE_LIMIT_ENABLED`: Boolean to enable/disable rate limiting

#### Scenario: All config values are accessible
- **WHEN** application code accesses `settings.DATABASE_URL` or any other config value
- **THEN** correct value is returned without raising exceptions

### Requirement: .env file template
A `.env.example` file SHALL be provided documenting all required environment variables with sample values.

#### Scenario: Developer creates .env from template
- **WHEN** developer copies `.env.example` to `.env` and fills in values
- **THEN** application can start successfully with those values
