## ADDED Requirements

### Requirement: Environment configuration with .env.example template

The system SHALL provide a `.env.example` file at the repository root that documents all required environment variables for local development. The file SHALL NOT contain actual credentials or secrets — only placeholders with descriptive comments.

#### Scenario: .env.example exists and is documented
- **WHEN** a developer clones the repository
- **THEN** they find `.env.example` at the root level with all required variables documented with comments

#### Scenario: Variables are clearly categorized
- **WHEN** a developer reads `.env.example`
- **THEN** they see sections for: Database, Authentication, MercadoPago, API, and Frontend configuration

#### Scenario: Developers can safely commit .env.example
- **WHEN** a developer runs `git status`
- **THEN** `.env.example` is tracked and committed, but `.env` (local) is ignored by .gitignore

#### Scenario: Example contains plausible defaults
- **WHEN** a developer copies `.env.example` to `.env` for local development
- **THEN** they get reasonable defaults or clear instructions on what to fill in (e.g., DATABASE_URL=postgresql://user:pass@localhost:5432/foodstore_dev)

### Requirement: Local .env file is never committed

The system SHALL ensure that `.env` (the actual local environment file with secrets) is always in `.gitignore` and never committed to version control, even by accident.

#### Scenario: .gitignore protects .env
- **WHEN** a developer accidentally tries to `git add .env`
- **THEN** git warns that the file is in .gitignore (depending on git config)

#### Scenario: CI/CD instructions are documented
- **WHEN** setting up automated tests or deployment
- **THEN** the README explains how to inject environment variables securely (via CI/CD secrets, not repo files)

### Requirement: Clear instructions for environment setup

The system SHALL document in README.md how to:
1. Copy `.env.example` to `.env`
2. Fill in required credentials (database URL, API keys, etc.)
3. Verify the setup is correct

#### Scenario: New contributor can set up locally in 5 minutes
- **WHEN** a new developer follows the "Quick Start" section in README.md
- **THEN** they successfully copy `.env.example` to `.env`, fill in placeholders, and understand what each variable does
