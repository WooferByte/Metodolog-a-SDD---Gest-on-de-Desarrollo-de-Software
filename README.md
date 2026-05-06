# 🍕 Food Store — Full-Stack E-Commerce Platform

A modern, scalable full-stack e-commerce platform built with Python FastAPI, React, and PostgreSQL. This is a demonstration project showcasing Domain-Driven Design (DDD), clean architecture, and modern web development practices.

## 📚 Documentation

For detailed documentation, design decisions, and setup guides, see **[`docs/INDEX.md`](./docs/INDEX.md)**.

> Includes: Architecture overview, database setup, skills guides, testing procedures, and OPSX change logs.

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL 12+
- **ORM**: SQLAlchemy
- **Authentication**: JWT (JSON Web Tokens)
- **Validation**: Pydantic
- **Payment**: MercadoPago API

### Frontend
- **Framework**: React 18+
- **Build Tool**: Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **HTTP Client**: Axios

### Infrastructure
- **Monorepo**: Organized backend and frontend in single repository
- **Version Control**: Git with Conventional Commits
- **Architecture**: Domain-Driven Design (DDD) + Clean Architecture

## Quick Start

### Prerequisites
- Python 3.9 or higher
- Node.js 16+ and npm/yarn
- PostgreSQL 12+ (OR Docker + Docker Compose)
- Git

### Getting Started - Option 1: Docker Compose (Recommended)

This is the fastest way to get a development environment running.

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd RepositorioBaseFoodStore-SDD
   ```

2. **Start PostgreSQL with Docker Compose**
   ```bash
   docker-compose up -d
   # This starts PostgreSQL 16 Alpine with health checks and persistence
   # Wait for the health check to pass (about 10 seconds)
   ```

3. **Verify PostgreSQL is running**
   ```bash
   docker exec foodstore-postgres pg_isready
   # Should show: "accepting connections"
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # The DATABASE_URL is already set for Docker: postgresql+psycopg://postgres:postgres@localhost:5432/foodstore_db
   ```

5. **Setup Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Seed initial data
   python scripts/seed.py
   
   # Start the backend
   python -m uvicorn main:app --reload
   ```

6. **Setup Frontend**
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```

Backend: `http://localhost:8000`  
Frontend: `http://localhost:5173`  
API Docs: `http://localhost:8000/docs`

---

### Getting Started - Option 2: Native PostgreSQL

If you already have PostgreSQL running locally, or prefer not to use Docker.

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd RepositorioBaseFoodStore-SDD
   ```

2. **Create PostgreSQL database**
   ```bash
   psql -U postgres
   CREATE DATABASE foodstore_db;
   \q
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and set DATABASE_URL for your PostgreSQL instance:
   # DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/foodstore_db
   ```

4. **Setup Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Seed initial data
   python scripts/seed.py
   
   # Start the backend
   python -m uvicorn main:app --reload
   ```

5. **Setup Frontend**
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```

Backend: `http://localhost:8000`  
Frontend: `http://localhost:5173`  
API Docs: `http://localhost:8000/docs`

---

### Troubleshooting

**Docker issues:**
- Port 5432 already in use: `docker ps` to see running containers, `docker kill <container>` if needed
- Docker daemon not running: Start Docker Desktop or the Docker service
- Permission denied on Linux: Add user to docker group: `sudo usermod -aG docker $USER`

**Database connection issues:**
- Database URL format: Must use `postgresql+psycopg://...` for async support
- Health check failing: Wait longer or check `docker logs foodstore-postgres`
- Authentication failed: Verify DATABASE_URL matches credentials in .env

**Backend startup issues:**
- Import errors: Ensure you're in venv and `pip install -r requirements.txt` completed
- Port 8000 in use: Change port in main.py or kill existing process
- Seed script errors: Check database is running and DATABASE_URL is correct

## Project Structure

```
RepositorioBaseFoodStore-SDD/
├── backend/
│   ├── auth/               # Authentication & authorization
│   ├── usuarios/           # User management
│   ├── productos/          # Product catalog
│   ├── categorias/         # Product categories
│   ├── ingredientes/       # Ingredients
│   ├── pedidos/            # Orders
│   ├── pagos/              # Payment processing
│   ├── direcciones/        # Addresses
│   ├── admin/              # Admin operations
│   ├── refresh_tokens/     # Token refresh logic
│   ├── core/               # Core utilities & configuration
│   └── requirements.txt    # Python dependencies
│
├── frontend/
│   └── src/
│       ├── app/            # Application entry & layout
│       ├── pages/          # Full pages/routes
│       ├── widgets/        # Complex UI components
│       ├── features/       # Feature-specific components
│       ├── entities/       # Domain entities
│       └── shared/         # Shared utilities & constants
│
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore patterns
└── README.md               # This file
```

## Contributing Guidelines

### Conventional Commits

All commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`

**Examples**:
```bash
git commit -m "feat(auth): implement JWT token generation"
git commit -m "fix(productos): resolve product filtering bug"
git commit -m "docs(README): update setup instructions"
```

### Best Practices
1. Create feature branches: `git checkout -b feat/feature-name`
2. Make atomic commits (one logical change per commit)
3. Push to feature branch and create a Pull Request
4. Ensure CI/CD checks pass before merging
5. Delete feature branch after merge

## Development

### Backend Development
- Domain modules follow DDD patterns
- Each module has: models, schemas, services, routers
- Use snake_case for Python files
- Use kebab-case for directory names

### Frontend Development
- Feature-Sliced Design (FSD) architecture
- Use PascalCase for React components
- Use camelCase for utility functions
- Organize by features, not technical layers

## Support & Documentation

For questions or issues:
1. Check existing documentation in `/docs`
2. Review code comments and docstrings
3. Check GitHub Issues for similar problems
4. Create a new issue with detailed reproduction steps

## License

This project is part of an educational initiative.

---

**Last Updated**: April 2026

<!-- Crear entorno -->
python -m venv .venv

## Activar entorno
En directorio: fastapi_backend
source .venv/Scripts/activate

<!-- Innstalar dependenciar -->
pip install -r requirements.txt


## Ir al directorio del ejercicio
Ej: (.venv) ➜ fastapi_backend cd u_01/u1_ej4/


## Ejecutar servidor de desarrollo con Endpints

(.venv) ➜ python -m fastapi dev ej_4_1.py