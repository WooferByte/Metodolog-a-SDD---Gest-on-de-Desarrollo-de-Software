# Implementation Tasks: Infrastructure Repository Setup

## 1. Directory Structure Creation

- [ ] 1.1 Create `/backend` directory at repository root
- [ ] 1.2 Create backend feature directories: `auth/`, `usuarios/`, `productos/`, `categorias/`, `ingredientes/`, `pedidos/`, `pagos/`, `direcciones/`, `admin/`, `refresh_tokens/`
- [ ] 1.3 Create `/backend/core` directory for infrastructure code
- [ ] 1.4 Verify all 11 backend directories exist with `ls -la backend/`
- [ ] 1.5 Create `/frontend` directory at repository root
- [ ] 1.6 Create `/frontend/src` directory
- [ ] 1.7 Create FSD layer directories: `app/`, `pages/`, `widgets/`, `features/`, `entities/`, `shared/`
- [ ] 1.8 Verify all 6 frontend FSD directories exist with `ls -la frontend/src/`
- [ ] 1.9 Create `.gitkeep` files in each empty directory so they are tracked by Git (empty directories are not tracked)

## 2. Configuration Files

- [ ] 2.1 Create `.gitignore` at repository root with Python-specific patterns:
  - `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`
  - `.Python`, `env/`, `venv/`, `ENV/`
  - `.pytest_cache/`, `.coverage`, `htmlcov/`
  - `.mypy_cache/`, `.dmypy.json`, `dmypy.json`

- [ ] 2.2 Add JavaScript/Node.js patterns to `.gitignore`:
  - `node_modules/`, `dist/`, `build/`, `.next/`
  - `*.tsbuildinfo`

- [ ] 2.3 Add environment and IDE patterns to `.gitignore`:
  - `.env`, `.env.local`, `.env.*.local`
  - `.vscode/`, `.idea/`, `*.swp`, `*.swo`
  - `.DS_Store`, `Thumbs.db`

- [ ] 2.4 Add OS/temp patterns to `.gitignore`:
  - `*.log`, `*.tmp`, `*.bak`
  - `.DS_Store` (already added)

- [ ] 2.5 Create `.env.example` at repository root with database configuration:
  - `# Database PostgreSQL`
  - `DATABASE_URL=postgresql://user:password@localhost:5432/foodstore_dev`

- [ ] 2.6 Add authentication variables to `.env.example`:
  - `# JWT Secret`
  - `JWT_SECRET_KEY=your-secret-key-change-in-production`
  - `JWT_ALGORITHM=HS256`
  - `ACCESS_TOKEN_EXPIRE_MINUTES=30`

- [ ] 2.7 Add MercadoPago variables to `.env.example`:
  - `# MercadoPago`
  - `MP_ACCESS_TOKEN=your-mp-access-token`
  - `MP_PUBLIC_KEY=your-mp-public-key`

- [ ] 2.8 Add frontend variables to `.env.example`:
  - `# Frontend`
  - `VITE_API_BASE_URL=http://localhost:8000`

- [ ] 2.9 Verify `.env.example` has clear comments explaining each section
- [ ] 2.10 Verify `.env.example` contains NO actual credentials or real values (all placeholders)

## 3. README and Documentation

- [ ] 3.1 Create `README.md` at repository root with project title and description (Food Store — Full-Stack E-Commerce Platform)
- [ ] 3.2 Add "Tech Stack" section to README listing:
  - Backend: Python, FastAPI, SQLModel, PostgreSQL
  - Frontend: React 18, TypeScript, Zustand, Tailwind CSS
  - Infrastructure: Docker (future), OPSX for change management

- [ ] 3.3 Add "Quick Start" section with steps:
  1. Clone repository
  2. Copy `.env.example` to `.env`
  3. Fill in `.env` with local credentials
  4. Run backend setup (BLOQUE 1 Change 2)
  5. Run frontend setup (BLOQUE 1 Change 5)

- [ ] 3.4 Add "Project Structure" section explaining:
  - `/backend` — Feature-first architecture
  - `/frontend/src` — Feature-Sliced Design
  - `/docs` — Documentation and specs
  - `/openspec` — OPSX change management

- [ ] 3.5 Add "Contributing Guidelines" section with Conventional Commits documentation:
  - Examples: `feat: add user login`, `fix: correct order total`, `docs: update README`
  - Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

- [ ] 3.6 Add section on reporting bugs and feature requests (GitHub issues or local process)
- [ ] 3.7 Add development prerequisites (Python 3.9+, Node.js 16+, PostgreSQL 12+)
- [ ] 3.8 Verify README is clear enough for a new developer to understand the project in 2 minutes

## 4. Python Placeholder Files

- [ ] 4.1 Create `/backend/requirements.txt` (empty or with comment: `# Python dependencies will be added in backend-fastapi-core-setup`)
- [ ] 4.2 Verify `/backend/requirements.txt` is tracked by Git

## 5. Git Configuration and First Commit

- [ ] 5.1 Verify current Git branch is `main` (run `git branch`)
- [ ] 5.2 Stage all new files: `git add .`
- [ ] 5.3 Verify staged files include:
  - All `/backend/feature/` directories (via .gitkeep)
  - `/backend/core/` directory
  - All `/frontend/src/layer/` directories
  - `.gitignore`
  - `.env.example`
  - `README.md`
  - `/docs/CHANGES.md` (already exists)

- [ ] 5.4 Create first infrastructural commit: `git commit -m "feat: initialize monorepo structure for Food Store"`
- [ ] 5.5 Verify commit message follows Conventional Commits format (starts with `feat:`)
- [ ] 5.6 Verify commit is on `main` branch: `git log --oneline` should show the commit
- [ ] 5.7 Verify Git history is clean (no dangling merges or conflicts): `git status` shows "nothing to commit"

## 6. Verification and Cleanup

- [ ] 6.1 Run `tree` or `find . -type d -name .git -prune -o -type d -print | head -30` to visualize directory structure
- [ ] 6.2 Verify `/backend` contains exactly 11 feature directories + `/core`
- [ ] 6.3 Verify `/frontend/src` contains exactly 6 FSD layer directories
- [ ] 6.4 Verify no `.py` or `.jsx` files exist at repo root (only config files)
- [ ] 6.5 Verify `.env.example` exists and is committed
- [ ] 6.6 Verify `.env` does NOT exist (or exists only locally and is in .gitignore)
- [ ] 6.7 Run `git status` and confirm output is "On branch main, nothing to commit"

## 7. Documentation of Conventions

- [ ] 7.1 Document in README or CONTRIBUTING.md that:
  - Backend features use kebab-case: `/backend/auth/`, `/backend/refresh_tokens/`
  - Backend Python files use snake_case: `models.py`, `router.py`, `service.py`
  - Frontend features use PascalCase: `/frontend/src/features/UserAuth/`, `/frontend/src/features/ProductCatalog/`
  - Frontend React files use PascalCase for components: `ProductCard.tsx`, `useAuth.ts` for hooks

- [ ] 7.2 Verify conventions are clear enough that new developers don't have to ask

## Completion Criteria

✅ All tasks checked  
✅ `git status` shows "nothing to commit"  
✅ `git log` shows commit with message "feat: initialize monorepo structure for Food Store"  
✅ Directory structure matches design doc  
✅ All `.gitkeep` files in place to track empty directories  
✅ Next change (backend-fastapi-core-setup) can now depend on this foundation  

## Estimated Time

- **Time**: 30-45 minutes (mostly creating directories and writing documentation)
- **Complexity**: Low (no code logic, just structure and config)
- **Dependencies**: Git, bash/PowerShell, text editor
- **Blockers**: None (this is the foundation change)

## Notes for Implementation

- Use `mkdir -p` to create nested directories efficiently
- Use `.gitkeep` files (empty files) so Git tracks empty directories
- Commit early (after directories), commit often (after each logical group)
- README should be friendly to new developers; avoid jargon
- If working in a team, coordinate on Git branch names and push strategy (not covered here; is future CI/CD change)
