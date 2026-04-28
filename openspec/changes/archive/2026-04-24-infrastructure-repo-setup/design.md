# Design Document: Infrastructure Repository Setup

## Context

Food Store is a full-stack e-commerce platform being built with:
- **Backend**: FastAPI (Python) with SQLModel ORM, async/await patterns
- **Frontend**: React 18+ with TypeScript, Zustand for state management, Tailwind CSS for styling
- **Current State**: Repository already initialized with docs/ and openspec/ directories. No backend or frontend source code yet.
- **Stakeholders**: Full-stack team (backend + frontend developers), DevOps/CI-CD engineers

## Goals / Non-Goals

**Goals:**
1. Establish a monorepo structure that allows independent backend and frontend development
2. Define folder organization conventions that scale with the project (10-50 engineers eventually)
3. Enable clear code ownership (backend team owns /backend, frontend team owns /frontend)
4. Document environment setup so new developers can get running in < 5 minutes
5. Enforce git conventions to maintain readable commit history
6. Provide a foundation that unblocks all subsequent changes (FastAPI setup, React setup, auth, etc.)

**Non-Goals:**
- Actually implementing FastAPI or React code (that's BLOQUE 1 changes 2-5)
- Setting up CI/CD pipelines (that's a future infrastructure change)
- Database schema or ORM models (handled in backend-postgres-alembic-seed)
- Any business logic or features (all in subsequent changes)

## Decisions

### Decision 1: Monorepo over Multiple Repositories

**Choice**: Single Git repository with /backend and /frontend subdirectories

**Rationale**:
- Easier for junior developers (one clone, not two)
- Shared docs/ and configuration files naturally live in repo root
- Atomic commits across both backend and frontend (e.g., "Add user authentication" affects both)
- OPSX workflow is per-repo; one monorepo = one OPSX instance

**Alternatives Considered**:
- **Polyrepo** (separate repos): More flexibility, but teams end up managing dependency versions across repos, painful for monolithic apps
- **Monorepo with tools** (Nx, Turbo): Overkill for a 4-5 person team; adds complexity without current value

**Tradeoff**: Monorepo requires discipline with .gitignore and folder boundaries; we mitigate with clear ownership docs.

---

### Decision 2: Feature-First Backend over Layered Architecture

**Choice**: Organize backend by feature (auth/, produtos/, pedidos/, etc.) not by technical layer (models/, services/, routers/)

**Rationale**:
- When you need to work on "orders feature," all code lives in one place (pedidos/)
- Easier to parallelize work: Backend Team A works on auth/, Team B works on products/
- Clear code ownership: "Feature X is owned by Team X"
- When a feature is removed/deprecated, you just delete one folder
- Follows Domain-Driven Design principles (which we're enforcing via python-fastapi-ddd-skill)

**Alternatives Considered**:
- **Layered** (models/, services/, routers/): Common, but spreads "order feature" code across 3 folders
- **Hexagonal/Port-Adapter**: Excellent architecture, but complex to teach junior devs; more suitable after team stabilizes

**Tradeoff**: Requires clear internal organization within each feature folder (models.py, router.py, repository.py); mitigated by DDD patterns in python-fastapi-ddd-skill.

---

### Decision 3: Feature-Sliced Design for Frontend

**Choice**: FSD layering with app/ → pages/ → features/ → entities/ → shared/

**Rationale**:
- Prevents spaghetti imports and circular dependencies
- Scales well (FSD is designed for 50+ feature projects)
- Clear mental model: a Page is a composition of Features, which use Entities and Shared utilities
- Matches industry standard (Yandex created FSD for their 1000-dev teams)

**Alternatives Considered**:
- **Component-based** (all components/ folder): Fine for < 5 features; becomes unmaintainable at scale
- **Domain-driven** (users/, products/, orders/): Works for simple projects, but mixing business logic with React patterns

**Tradeoff**: Slightly more folder nesting than component-based, but enforces good discipline from day 1.

---

### Decision 4: .env.example Instead of Configuration Files

**Choice**: Use `.env.example` in Git, `.env` locally in .gitignore, no JSON/YAML config files

**Rationale**:
- Simple and widely understood (works the same in Python and Node.js)
- No accidental credential leaks (env vars are never committed)
- CI/CD naturally uses environment variables
- Matches DevOps best practices (12-Factor app principles)

**Alternatives Considered**:
- **YAML config files**: More structured, but Python and Node.js parse differently; hard to keep in sync
- **Python-only** (settings.py): Only works for backend, frontend needs separate solution
- **Hardcoded defaults**: Never acceptable for a multi-environment app

**Tradeoff**: .env files are not as structured as YAML; mitigated by clear comments and categorization in .env.example.

---

### Decision 5: Conventional Commits with Enforced Format

**Choice**: Require commit messages like `feat: add user login`, `fix: correct order total`, `docs: update setup guide`

**Rationale**:
- Enables automated changelog generation (future infrastructure change)
- Makes blame/history readable: `git log --oneline` tells the story of the project
- Catches mistakes early: if commit message doesn't start with `feat:/fix:/docs:/etc`, it might be incomplete
- Standard across the industry (Angular convention)

**Alternatives Considered**:
- **Free-form** commit messages: Harder to parse history, painful when hundreds of commits exist
- **Squash all to main**: Loses history detail

**Tradeoff**: Developers must be disciplined; mitigated by clear documentation in README and pre-commit hooks (added in a future infrastructure change).

---

### Decision 6: Directory Naming: kebab-case for Folders, snake_case for Python, camelCase for JS

**Choice**:
- Backend folders: `auth/`, `usuarios/`, `refresh_tokens/` (kebab-case)
- Backend files: `models.py`, `router.py`, `service.py` (snake_case)
- Frontend folders: `UserAuth/`, `ProductCatalog/` (PascalCase for features since they export components)
- Frontend files: `ProductCard.tsx`, `useAuth.ts` (camelCase/PascalCase per convention)

**Rationale**:
- Folders: kebab-case is URL-friendly (if we ever serve static assets from /auth/, it looks right)
- Python: PEP 8 standard (snake_case for files and modules)
- React: Components are PascalCase (class-like), hooks are camelCase

**Alternatives Considered**:
- **All snake_case**: Confuses React developers used to camelCase
- **All kebab-case**: Goes against Python conventions

**Tradeoff**: Multiple naming conventions across the repo; mitigated by clear examples in file structure comments and IDE templates.

---

## Risks / Trade-offs

### Risk 1: Monorepo becomes unmaintainable as the project grows
**Mitigation**: 
- Monitor folder sizes; if /backend grows beyond 50 features, consider splitting to polyrepo
- Use OPSX to enforce clear change boundaries (one change per feature)
- Regular code reviews to maintain folder discipline

### Risk 2: Feature-first organization doesn't scale to 200+ developer teams
**Mitigation**:
- This architecture is designed for teams up to 50 developers
- If Food Store grows beyond that, a future "refactor to microservices" change can split each feature into its own service
- For now, optimize for the team size we have

### Risk 3: Developers forget .env files and leak secrets
**Mitigation**:
- Document in README and on-boarding
- Pre-commit hooks (future infrastructure change) to scan for common secret patterns
- Educate team on never committing `.env`

### Risk 4: Developers create shortcuts and bypass folder structure
**Mitigation**:
- Code reviews (future change to add PR review template)
- Linting rules (future infrastructure change to add eslint/pylint)
- Lead by example: first few PRs follow the structure strictly

---

## Migration Plan

### Phase 1: Repository Initialization (This Change)
1. Create `/backend` with feature subdirectories (empty)
2. Create `/frontend/src` with FSD layer directories (empty)
3. Create `.gitignore` and `.env.example`
4. Create `README.md` with setup instructions and contribution guidelines
5. Commit as "feat: initialize monorepo structure"
6. Verify git history is clean (main branch, conventional commits documented)

### Phase 2: Backend Setup (BLOQUE 1 Change 2: backend-fastapi-core-setup)
- Populates `/backend` with main.py and `/backend/core`
- Depends on: infrastructure-repo-setup complete

### Phase 3: Frontend Setup (BLOQUE 1 Change 5: frontend-react-vite-setup)
- Populates `/frontend` with Vite scaffolding and package.json
- Depends on: infrastructure-repo-setup complete

---

## Open Questions

1. **Docker Compose for local development?** Should we add docker-compose.yml at repo root for easy `docker-compose up` development? (Decision: deferred to future infrastructure change)
2. **Pre-commit hooks?** Should we enforce .env.example checks and linting at commit time? (Decision: deferred to future infrastructure change, add in "linting-and-formatting" change)
3. **GitHub-specific files?** Should we include .github/workflows/ for CI/CD now or wait until we have code to test? (Decision: wait until BLOQUE 1 is done and code exists to run tests)

---

## Implementation Summary

| Item | Details |
|------|---------|
| **Root directories** | /backend, /frontend, /docs, /openspec |
| **Backend structure** | 10 feature folders + /core for infrastructure |
| **Frontend structure** | 6 FSD layers (app, pages, widgets, features, entities, shared) |
| **Config files** | .gitignore (Python + JS), .env.example with sections, README.md |
| **First commit** | "feat: initialize monorepo structure for Food Store" |
| **No code written yet** | All subdirectories are empty; populated by subsequent changes |

Next change (backend-fastapi-core-setup) builds on this foundation.
