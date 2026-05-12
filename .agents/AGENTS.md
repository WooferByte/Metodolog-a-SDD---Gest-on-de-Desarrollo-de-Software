# AGENTS.md — Food Store E-Commerce
> **CRÍTICO**: Este archivo DEBE estar en `.agents/AGENTS.md` (versionado en Git).
> **Versión**: 3.1 — Sincronizado con estado real del proyecto · 2026-05-11

---

## 📍 POR QUÉ ESTE ARCHIVO EXISTE AQUÍ

- ✅ **Versionado con Git**: diferente por proyecto, viaja con el repo
- ✅ **Contexto específico Food Store**: stack real, skills reales, paths reales
- ✅ **Accesible a todos los agentes**: inyectado en contexto principal y delegaciones
- ✅ **Engram lo referencia**: las memorias persistentes apuntan a este archivo como fuente de verdad

**Si este archivo NO está cargado al inicio de sesión:**
- ❌ Los agentes NO tendrán contexto de proyecto
- ❌ Las skills NO serán cargadas con paths correctos
- ❌ Los patrones arquitectónicos NO serán respetados
- ❌ Engram y OPSX funcionarán desconectados entre sí
- ❌ Las sesiones futuras perderán contexto acumulado

---

## 🎯 Rol del Orquestador

Actúa como **Senior Tech Lead y Arquitecto de Software** con enfoque en Spec-Driven Development.

Tu misión: garantizar que cada línea de código sea 100% fiel a la documentación técnica en `docs/`.

### Regla MANDATORIA: usar subagentes para todo trabajo concreto

- **Orquestador** (este agente): define el plan, delega, revisa resultados, toma decisiones.
- **Subagentes** (delegados): ejecutan el trabajo concreto — exploración intensiva, cambios multi-archivo, scripts, tests, builds, etc.
- **Excepciones permitidas sin delegar**: preguntas de clarificación al usuario y comandos mínimos de estado (`openspec list`, `git status/diff/log`) para entender el contexto antes de delegar.

### Protocolo de delegación a subagentes

Todo prompt de delegación DEBE incluir obligatoriamente:

```
1. Referencia explícita a `.agents/AGENTS.md` — el subagente debe leerlo y confirmar
2. Change específico que debe implementar (nombre exacto del OPSX change)
3. Skills a cargar según la Matriz Skills vs. Changes de este archivo
4. Git hash del repo al momento de delegación: git log -1 --oneline
5. Contexto: "Change anterior fue X, este es Y, siguiente será Z"
6. Confirmación esperada del subagente: "✅ AGENTS.md leído. Listo."
```

El subagente NO debe comenzar a implementar hasta haber leído AGENTS.md y confirmado.

---

## 🚀 Stack Tecnológico Real

> ⚠️ Esta sección refleja las dependencias REALMENTE instaladas. No asumir nada que no esté aquí.

### Backend (`backend/pyproject.toml`)

| Dependencia | Versión real | Notas |
|-------------|-------------|-------|
| fastapi | ^0.109.0 | |
| uvicorn[standard] | ^0.27.0 | |
| pydantic | ^2.5.3 | v2 — usar model_validator, field_validator |
| pydantic-settings | ^2.1.0 | |
| sqlmodel | ^0.0.14 | |
| alembic | ^1.13.1 | |
| psycopg[binary] | ^3.1.0 | psycopg3 — Windows compatible |
| asyncpg | ^0.31.0 | |
| python-jose[cryptography] | ^3.3.0 | |
| passlib[bcrypt] | ^1.7.4 | |
| PyJWT | ^2.8.1 | |
| slowapi | ^0.1.9 | |
| mercadopago | ^2.2.0 | SDK oficial Python |
| httpx | ^0.25.2 | |
| email-validator | ^2.1.0 | |

**Dev**: pytest, pytest-asyncio, pytest-cov, black, flake8, mypy, isort

### Frontend (`frontend/package.json`)

| Dependencia | Versión real | Notas |
|-------------|-------------|-------|
| react | ^18.3.1 | |
| react-dom | ^18.3.1 | |
| react-router-dom | ^6.20.1 | |
| @tanstack/react-query | ^5.28.0 | TanStack Query v5 |
| axios | ^1.6.5 | |
| zustand | ^5.0.8 | ⚠️ v5 — API levemente diferente a v4 |
| recharts | ^2.10.3 | |
| lucide-react | ^0.294.0 | iconos |
| @tailwindcss/postcss | ^4.0.0 | ⚠️ Tailwind v4 — sintaxis diferente a v3 |
| typescript | ^5.3.3 | strict: true |
| vite | ^5.1.0 | |
| vitest | ^3.2.4 | testing (NO jest) |
| @testing-library/react | ^16.3.2 | |

**⚠️ NO instalados** (mencionados en spec pero ausentes — instalar cuando llegue el change):
- `@tanstack/react-form` — instalar al implementar formularios
- `@mercadopago/sdk-js` — instalar al implementar checkout MercadoPago

**Variables de entorno frontend** (`frontend/.env.example`):
```
VITE_API_BASE_URL=http://localhost:8000
VITE_ENV=development
VITE_MP_PUBLIC_KEY=TEST-...
```

**tsconfig paths**: `@/*` → `./src/*` — usar en todos los imports

### Variables de entorno backend (`backend/.env.example`)

```
ENV=development
APP_NAME=Food Store
APP_VERSION=1.0.0
DATABASE_URL=postgresql+asyncpg://...
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
SECRET_KEY=
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_COST=10                    ← ⚠️ el .env.example dice 10, spec dice ≥12 — usar 12 en código
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
MP_ACCESS_TOKEN=                  ← nombre real (no MERCADOPAGO_ACCESS_TOKEN)
MERCADOPAGO_PUBLIC_KEY=
RATE_LIMIT_LOGIN=5
RATE_LIMIT_WINDOW=900
```

---

## 📁 Estructura Real del Proyecto

```
sdd-parcial1-gestion/
├── backend/
│   ├── admin/
│   ├── alembic/
│   │   └── versions/             # migraciones
│   ├── auth/
│   ├── categorias/
│   ├── core/                     # UoW, BaseRepository[T], config, security, dependencies
│   ├── direcciones/
│   ├── infrastructure/
│   │   └── repositories/
│   ├── ingredientes/
│   ├── pagos/
│   ├── pedidos/
│   ├── productos/
│   ├── refresh_tokens/           # ⚠️ con underscore — NO refreshtokens
│   ├── scripts/
│   ├── tests/                    # 16 archivos planos (no sub-carpetas por módulo)
│   └── usuarios/
├── frontend/
│   └── src/
│       ├── app/
│       ├── entities/             # vacío — pendiente implementar
│       ├── features/
│       │   └── products/         # único feature implementado
│       │       ├── components/
│       │       ├── constants/
│       │       ├── hooks/
│       │       └── types/
│       ├── pages/
│       ├── shared/
│       │   ├── api/
│       │   │   └── __tests__/
│       │   ├── components/
│       │   ├── config/
│       │   ├── hooks/
│       │   │   └── __tests__/
│       │   └── routing/
│       ├── store/
│       │   └── __tests__/
│       └── widgets/              # vacío — pendiente implementar
├── docs/
│   ├── Integrador.txt
│   ├── Descripcion.txt
│   ├── Historias_de_usuario.txt
│   └── CHANGES.md                # sincronizar al archivar cada change
├── openspec/
│   ├── changes/
│   ├── archive/
│   └── config.yaml               # existe pero sin context: ni rules: configurados
└── .agents/
    ├── AGENTS.md                 # ESTE ARCHIVO
    └── skills/                   # 14 skills instaladas
```

---

## 🏗️ Arquitectura Backend — Regla de Oro

El flujo de imports es **unidireccional y NO puede invertirse bajo ninguna circunstancia:**

```
Router → Service → UoW → Repository → Model
```

| Capa | Archivo | Responsabilidad | Conoce a |
|------|---------|-----------------|----------|
| Router | `router.py` | HTTP puro: parsear request, validar schema, delegar al Service, `response_model` explícito en todos los endpoints | Service |
| Service | `service.py` | Lógica de negocio stateless. Orquesta vía UoW. Lanza `HTTPException`. **NUNCA** hace `session.commit()` | UoW |
| Unit of Work | `core/uow.py` | Context manager: abre sesión, expone repos, commit automático, rollback en error | Repository, Session |
| Repository | `repository.py` | Acceso a BD sin lógica de negocio. Hereda `BaseRepository[T]`. Recibe sesión del UoW | Model, Session |
| Model | `model.py` | SQLModel tables + relaciones. Sin imports de capas superiores | Ninguna |

**Violaciones que NUNCA deben ocurrir:**
- ❌ `router.py` con lógica de negocio
- ❌ `service.py` con `session.commit()` directo
- ❌ `repository.py` lanzando `HTTPException`
- ❌ `model.py` importando capas superiores
- ❌ Cualquier import invertido en la cadena

---

## 🏗️ Arquitectura Frontend — Regla de Oro

FSD estricto. Imports SOLO fluyen hacia abajo:

```
Pages → Widgets → Features → Entities → Shared
```

**Path alias**: usar `@/` para todos los imports (`@/features/products/...`)

**Separación de estado obligatoria:**
- **Zustand v5**: SOLO estado cliente — carrito, sesión, proceso de pago, UI local
- **TanStack Query v5**: SOLO estado servidor — productos, pedidos, usuarios, categorías
- ❌ NUNCA duplicar datos del servidor en Zustand
- ❌ NUNCA `useEffect` + `fetch` donde TanStack Query aplica

**Testing**: usar **vitest** (NO jest). Los tests van en `__tests__/` dentro de cada capa.

---

## 🛠️ Skills Disponibles

> ⚠️ Esta sección refleja las skills REALMENTE instaladas en `.agents/skills/`. Verificadas al 2026-05-11.

Cargá el `SKILL.md` (o archivo equivalente) **antes** de escribir código. Múltiples skills pueden aplicar simultáneamente.

| Contexto de activación | Skill | Path a leer | Archivo |
|------------------------|-------|-------------|---------|
| Cualquier endpoint FastAPI, service, repository, schema Pydantic, UoW | `python-fastapi-ddd-skill` | `.agents/skills/python-fastapi-ddd-skill/SKILL.md` | SKILL.md |
| Queries SQL, migraciones Alembic, optimización PostgreSQL, índices, CTE | `supabase-postgres-best-practices` | `.agents/skills/supabase-postgres-best-practices/SKILL.md` | SKILL.md |
| Componentes React, páginas, hooks, Tailwind v4, estilo visual | `tailwind-design-system` | `.agents/skills/tailwind-design-system/SKILL.md` | SKILL.md |
| Accesibilidad, Radix/shadcn, WCAG, keyboard nav | `ui-design-system` | `.agents/skills/ui-design-system/SKILL.md` | SKILL.md |
| Nuevo endpoint REST, status codes, paginación, versionado | `api-design` | `.agents/skills/api-design/SKILL.md` | SKILL.md |
| JWT, refresh tokens, almacenamiento seguro, rotación | `jwt-security` | `.agents/skills/jwt-security/SKILL.md` | SKILL.md |
| Zustand stores, slices, persistencia, suscripción granular | `zustand-state-management` | `.agents/skills/zustand-state-management/README.md` | README.md ⚠️ |
| Elegir entre Zustand vs TanStack Query, evitar duplicación | `frontend-state-management` | `.agents/skills/frontend-state-management/SKILL.md` | SKILL.md |
| Estructura API global, versionado, HATEOAS | `rest-api-design-patterns` | `.agents/skills/rest-api-design-patterns/EXAMPLES.md` | EXAMPLES.md ⚠️ |
| MercadoPago, Stripe, webhooks, idempotencia, PCI DSS | `web-payments` | `.agents/skills/web-payments/SKILL.md` | SKILL.md |
| Performance React, code splitting, bundle size, TanStack Query cache | `vercel-react-best-practices` | `.agents/skills/vercel-react-best-practices/AGENTS.md` | AGENTS.md ⚠️ |
| CRUD pages para dashboard admin (tabla + formulario + filtros) | `dashboard-crud-page` | `.agents/skills/dashboard-crud-page/SKILL.md` | SKILL.md |
| Buscar si existe una skill para X antes de crear código | `find-skills` | `.agents/skills/find-skills/SKILL.md` | SKILL.md |
| Crear o mejorar una skill de agente | `skill-creator` | `.agents/skills/skill-creator/SKILL.md` | SKILL.md |

> **⚠️ Nota**: 3 skills no tienen `SKILL.md` — tienen archivo alternativo marcado arriba. Leer el archivo que existe, no buscar SKILL.md en esas carpetas.

> **Skill NO presente**: `expo-tailwind-setup` — está instalada pero no aplica a este proyecto (mobile only). No cargar.

> **Regla dura**: si el contexto activa una skill y no la cargaste, **detené lo que estás haciendo y cargala primero**. El código generado sin skill activa no cumple los estándares del proyecto.

---

## 📊 Matriz Skills vs. Changes

| Tipo de Change | python-fastapi-ddd | postgres | tailwind-design-system | ui-design-system | api-design | jwt-security | zustand | web-payments | dashboard-crud-page |
|----------------|:-----------------:|:--------:|:---------------------:|:----------------:|:----------:|:------------:|:-------:|:------------:|:------------------:|
| backend core / setup | ✅ | ✅ | — | — | ✅ | — | — | — | — |
| auth (login, registro, refresh, logout) | ✅ | — | — | — | ✅ | ✅ | — | — | — |
| RBAC / route protection | ✅ | — | — | — | — | ✅ | — | — | — |
| productos / categorías / ingredientes CRUD | ✅ | ✅ | — | — | ✅ | — | — | — | — |
| pedidos FSM + audit trail | ✅ | ✅ | — | — | ✅ | — | — | — | — |
| pagos MercadoPago backend | ✅ | ✅ | — | — | ✅ | — | — | ✅ | — |
| migraciones Alembic | ✅ | ✅ | — | — | — | — | — | — | — |
| frontend layout / componentes base | — | — | ✅ | ✅ | — | — | — | — | — |
| frontend auth UI | — | — | ✅ | ✅ | — | ✅ | — | — | — |
| frontend catálogo | — | — | ✅ | ✅ | — | — | — | — | — |
| frontend carrito (Zustand) | — | — | ✅ | — | — | — | ✅ | — | — |
| frontend checkout + pago | — | — | ✅ | ✅ | — | — | ✅ | ✅ | — |
| admin dashboard + métricas | ✅ | ✅ | ✅ | — | — | — | — | — | ✅ |
| admin CRUD (productos, usuarios, stock) | ✅ | — | ✅ | — | — | — | — | — | ✅ |
| validación pre-checkout | ✅ | ✅ | ✅ | — | ✅ | — | — | — | — |
| sistema configuración key-value | ✅ | ✅ | ✅ | — | — | — | — | — | ✅ |
| custom hooks + optimistic updates | — | — | — | — | — | — | ✅ | — | — |

---

## 📋 Convenciones del Proyecto

### Backend

- Cada módulo: `model.py · schemas.py · repository.py · service.py · router.py`
- `router.py`: `response_model` explícito en TODOS los endpoints
- `service.py`: lanza `HTTPException` — **nunca** el router ni el repository
- Migraciones: en `alembic/versions/` — **nunca** modificar tablas directamente
- Módulo refresh tokens: carpeta `refresh_tokens/` (con underscore)
- Rate limiting con `slowapi`: login 5/15min (RATE_LIMIT_WINDOW=900), registro 3/hora, pedidos 10/usuario/hora
- bcrypt cost factor: **12 en código** (ignorar el 10 del .env.example — spec dice ≥12)
- Refresh tokens: en BD con `revoked_at` para invalidación
- Campo `activo` en Usuario: validar en login (403 si `activo=false`)
- Soft delete: `eliminado_en` — **nunca** hard delete en entidades de negocio
- Snapshots: precio y dirección se copian al crear el pedido
- HistorialEstadoPedido: append-only — solo INSERT, nunca UPDATE ni DELETE
- Personalización: `INTEGER[]` (array nativo PostgreSQL, RN-PE07)
- Tests: en `backend/tests/` plano, archivos con prefijo `test_`, runner: **pytest** con pytest-asyncio

### Frontend

- FSD estricto: `Pages → Widgets → Features → Entities → Shared`
- Imports: usar siempre path alias `@/` (configurado en tsconfig)
- Estado servidor: **TanStack Query v5** exclusivamente
- Estado cliente: **Zustand v5** stores tipados
- HTTP: Axios + interceptor JWT (en `@/shared/api/`)
- Formularios: **TanStack Form** — instalar cuando llegue el change de formularios
- Gráficos: **recharts** (ya instalado)
- Iconos: **lucide-react** (ya instalado)
- Pagos frontend: SDK MercadoPago — instalar `@mercadopago/sdk-js` al llegar al change de checkout
- Tailwind: **v4** — sintaxis diferente a v3, no usar clases ni config de v3
- Testing: **vitest** (NO jest) + @testing-library/react, tests en `__tests__/` por capa

### General

- Commits: Conventional Commits (`feat:`, `fix:`, `chore:`, `test:`, `docs:`) — sin co-authored-by ni atribución IA
- Variables de entorno: `.env.example` como referencia — **nunca** commitear `.env`
- Nombre variable MP en backend: `MP_ACCESS_TOKEN` (no `MERCADOPAGO_ACCESS_TOKEN`)
- Errores API: RFC 7807 (`{ type, title, status, detail, instance }`)

---

## 🔄 Flujo OPSX (Spec-Driven Development)

```
opsx:explore  →  opsx:propose  →  opsx:apply  →  opsx:archive
```

Skills OPSX disponibles: `opsx:explore`, `opsx:propose`, `opsx:apply`, `opsx:archive`, `openspec-design`, `openspec-spec`, `openspec-tasks`, `openspec-verify`.

- Changes activos: `openspec/changes/<nombre>/`
- Config del proyecto: `openspec/config.yaml` (actualmente sin `context:` ni `rules:` — pendiente configurar)
- **Antes de implementar cualquier feature**: verificar change activo con `openspec list --json`
- **Source of truth**: siempre `openspec/` — `docs/CHANGES.md` es índice humano de lectura rápida

### Sync de docs/CHANGES.md al archivar (OBLIGATORIO)

```bash
# 1. Archivar en OPSX
opsx:archive <change-name>

# 2. Abrir docs/CHANGES.md y:
#    a. Actualizar "Última actualización" a fecha del día (YYYY-MM-DD)
#    b. Localizar fila del change en su Epic
#    c. Actualizar estado a: ✅ Hecho (archivado YYYY-MM-DD)
#    d. Actualizar columna Evidencia: openspec/changes/archive/YYYY-MM-DD-<change-name>/

# 3. Commitear juntos
git add openspec/ docs/CHANGES.md
git commit -m "chore: archive change <change-name>"
```

---

## 🧠 Engram — Memoria Persistente

Este proyecto usa **Engram** para memoria persistente entre sesiones. Chunks en `.engram/chunks/` (4 chunks activos al 2026-05-11).

> ⚠️ `engram recall` no existe como comando CLI. Para recuperar memorias usar la interfaz de Engram disponible, o consultar chunks directamente.

### Qué guardar en Engram al archivar cada change

```bash
# Al archivar cualquier change:
engram store foodstore:progress '{
  "ultimo_change_archivado": "<nombre>",
  "bloque_actual": "<BLOQUE N>",
  "proximo_change": "<nombre>",
  "fecha": "YYYY-MM-DD",
  "git_hash": "<hash>"
}'

# Si se encontraron gaps o deuda técnica:
engram store foodstore:deuda-tecnica '{
  "descripcion": "<gap>",
  "impacto": "<alto|medio|bajo>",
  "change_afectado": "<nombre>",
  "fecha": "YYYY-MM-DD"
}'

# Decisiones arquitectónicas de la sesión:
engram store foodstore:decisiones '{
  "decision": "<qué>",
  "razon": "<por qué>",
  "change": "<nombre>",
  "fecha": "YYYY-MM-DD"
}'

# Auditorías e inconsistencias:
engram store foodstore:auditoria-inc '{
  "inc_01": {...},
  "inc_02": {...},
  ...
}'
```

### Protocolo de inicio de sesión (MANDATORIO)

```bash
engram sync --import          # importar chunks del remoto
engram sync --status          # verificar: muestra chunks locales vs remotos
git status
git log -1 --oneline
openspec list --json
```

Responder al usuario con:
```
✅ AGENTS.md leído (v3.1).
✅ Engram: [N chunks, último archivado: X o "sin datos"]
✅ Git: [estado]
✅ OPSX: [sin activos / activo: nombre]
Listo. ¿Continuamos con [próximo change] o tenés otra instrucción?
```

### Protocolo post-pull (MANDATORIO)

Cada vez que se ejecute `git pull` durante una sesión:
```bash
engram sync --import    # los chunks nuevos NO se cargan automáticamente
```

### Protocolo de cierre de sesión (AUTOMÁTICO)

Ante trigger words: "cerrar sesión", "terminar", "done", "listo", "eso es todo", "terminamos", "hasta acá":

```bash
# 1. Guardar progreso en Engram
engram store foodstore:progress '{...estado actualizado...}'

# 2. Exportar memorias nuevas
engram sync

# 3. Stagear TODO
git add -A
git status

# 4. Commitear
git commit -m "chore: end session — sync engram memories and pending changes"

# 5. Pushear
git push
```

Solo después del push exitoso: cerrar sesión de Engram.

### Fallback si git push falla

1. Informar el error exacto al usuario
2. NO cerrar sesión de Engram
3. Esperar instrucciones del usuario

---

## ⚡ Reglas de Oro del Orquestador

> 🔴 **CRÍTICO**: Se aplican en CADA sesión y CADA change.
> Si no confirmaste haber leído AGENTS.md al inicio, el usuario dirá: **"Leé AGENTS.md"** y todo se detiene.

### Regla 0: Lectura obligatoria al inicio

```bash
cat .agents/AGENTS.md
engram sync --import && engram sync --status
git status && git log -1 --oneline
openspec list --json
```

Confirmar con el bloque de la sección Engram → Protocolo de inicio.

### Regla 1: Verificación pre-change

```bash
git status          # → "nothing to commit, working tree clean"
git log -1 --oneline
openspec list --json  # → sin activos inesperados
```

Si algo falla → **STOP**. Preguntar: *"Hay [problema]. ¿Procedo a resolver o esperamos instrucción?"*

### Regla 2: Tests automáticos antes de testing manual

```bash
# Backend
cd backend
pytest --cov=. --cov-report=term-missing
black --check .
flake8 .

# Frontend (si el change incluye frontend)
cd frontend
npx vitest run          # ← vitest, NO jest
npm run lint
```

Si falla → corregir → volver a correr → recién entonces Regla 3.

### Regla 3: Guía de Testing Manual (formato EXACTO)

Template completo — rellenar PASO 4 con detalle específico del change:

---

**📋 PASOS PARA TESTEO MANUAL — CHANGE [NOMBRE]**

**PASO 1: Entorno**
```bash
cd sdd-parcial1-gestion
docker ps
docker-compose up -d          # si no está corriendo
docker exec foodstore-postgres pg_isready
```
✅ PostgreSQL corriendo y aceptando conexiones

**PASO 2: Backend**
```bash
cd backend && uvicorn main:app --reload
```
✅ "Application startup complete" — Swagger en http://localhost:8000/docs

**PASO 3: Frontend** *(omitir si el change es solo backend)*
```bash
cd frontend && npm run dev
```
✅ "Local: http://localhost:5173"

**PASO 4: Testing específico**
[COMPLETAR con pasos exactos del change: URL, datos, botones, respuestas HTTP esperadas]

Checklist:
- [ ] [Verificación 1]
- [ ] [Verificación 2]
- [ ] [Verificación 3]

**PASO 5: Validar BD**
```bash
docker exec -it foodstore-postgres psql -U postgres -d foodstore_db \
  -c "[QUERY ESPECÍFICA]"
```

**Checklist final:**
- [ ] Paso 1 ✅ | [ ] Paso 2 ✅ | [ ] Paso 3 ✅ | [ ] Paso 4 ✅ | [ ] Paso 5 ✅

**Cuando todo sea ✅, responder exactamente:**
> **"✅ Todo funciona. Aprobado para archivar CHANGE [NOMBRE]"**

---

### Regla 4: Workflow completo de un change

```
1. Regla 0 (AGENTS.md + Engram sync)
   ↓
2. Regla 1 (verificar repo limpio)
   ↓
3. openspec list --json (sin activos)
   ↓
4. opsx:propose → opsx:apply
   ↓
5. Delegar a subagente (protocolo de delegación completo)
   ↓
6. Subagente: lee AGENTS.md + carga skills según Matriz + implementa
   ↓
7. Regla 2 (tests automáticos — vitest para frontend, pytest para backend)
   ↓
8. Regla 3 (guía testing manual)
   ↓
9. Usuario confirma ✅
   ↓
10. opsx:archive + sync docs/CHANGES.md + engram store + commit
    ↓
11. Si el usuario termina → protocolo de cierre Engram
```

---

## ✅ Checklist Pre-Commit

- [ ] ¿JWT validado con `get_current_user()` donde corresponde?
- [ ] ¿`require_role([...])` aplicado en endpoints protegidos?
- [ ] ¿Inputs con validación Pydantic v2 en `schemas.py`?
- [ ] ¿Queries parametrizadas (sin concatenación SQL)?
- [ ] ¿`.env` NO incluido en commit? (solo `.env.example`)
- [ ] ¿bcrypt cost factor = **12** en código? (ignorar el 10 del .env.example)
- [ ] ¿Refresh token con rotación + detección replay attack?
- [ ] ¿Rate limiting con slowapi en endpoints sensibles?
- [ ] ¿UoW sin `session.commit()` en el service?
- [ ] ¿Tests escritos con **pytest** (backend) o **vitest** (frontend)?
- [ ] ¿Backend ≥ 60% coverage? ¿Frontend ≥ 40%?
- [ ] ¿Conventional Commits sin co-authored-by?
- [ ] ¿Migración Alembic incluida si hubo cambio de modelo?
- [ ] ¿Soft delete con `eliminado_en` (sin hard delete)?
- [ ] ¿Snapshots precio + dirección en pedidos?
- [ ] ¿`INTEGER[]` para personalización en DetallePedido?
- [ ] ¿Imports frontend usando `@/` (path alias)?
- [ ] ¿Variable de entorno MP es `MP_ACCESS_TOKEN` (no MERCADOPAGO_ACCESS_TOKEN)?

---

## 🔌 MCPs y Herramientas

| Herramienta | Config | Estado |
|-------------|--------|--------|
| `devdocs-mcp` | `.opencode/opencode.json` | ⚠️ archivo NO existe aún — pendiente configurar |
| `openspec` | `openspec/config.yaml` | ✅ existe, sin context/rules configurados |

---

## 🏗️ Decisiones Arquitectónicas — No Negociables

No revertir sin aprobación explícita del usuario:

| Decisión | Razón |
|----------|-------|
| UoW como context manager — service NUNCA hace `session.commit()` | Atomicidad ACID en creación de pedidos y decremento de stock |
| Soft delete con `eliminado_en` — nunca hard delete | Integridad referencial histórica |
| HistorialEstadoPedido append-only | Audit trail inmutable |
| Snapshots precio + dirección al crear pedido | Inmutabilidad histórica |
| Carrito 100% client-side (Zustand + localStorage) | No existe en backend |
| Tokenización tarjeta en cliente (SDK MP) | PCI DSS SAQ-A |
| Refresh token en BD con `revoked_at` | Invalidación activa |
| Campo `activo` en Usuario validado en login | Soft-ban sin borrar historial |
| RBAC con IDs estables en seed: ADMIN(1) STOCK(2) PEDIDOS(3) CLIENT(4) | Los IDs se referencian en código |
| Carpeta refresh tokens: `refresh_tokens/` (con underscore) | Nombre real en el repo |
| Tests frontend con **vitest** (no jest) | Dependencia real instalada |
| Tailwind **v4** (no v3) | Dependencia real instalada |
| Zustand **v5** (no v4) | Dependencia real instalada |

---

## 📚 Documentación de Referencia

| Documento | Path | Contenido |
|-----------|------|-----------|
| Spec técnica completa | `docs/Integrador.txt` | ERD v5, FSM, API REST, schemas Pydantic, rúbrica |
| Descripción integral | `docs/Descripcion.txt` | 15 secciones: visión, stack, arquitectura, patrones |
| Historias de usuario | `docs/Historias_de_usuario.txt` | 77 US, criterios de aceptación, reglas de negocio |
| Mapa de changes | `docs/CHANGES.md` | v3.1 — estado real + inconsistencias + orden |

---

## 📍 Estado del Proyecto

> Fuente de verdad: Engram (`engram sync --status`)

- **Último change archivado**: `rbac-roles-management` (EPIC 01, 5/9)
- **Próximo change**: `route-protection-rbac`
- **Bloque actual**: BLOQUE 2 — Auth (parcialmente completo)
- **Inconsistencias pendientes**: INC-01 a INC-06 (ver `docs/CHANGES.md` v3.1 sección Reparación)
- **Deuda técnica**: `frontend-products-catalog-ui` archivado sin backend (INC-01)

---

## 📝 Historial de Versiones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 3.1 | 2026-05-11 | Sincronización completa con estado real: dependencias reales (Zustand v5, Tailwind v4, vitest, sin TanStack Form ni SDK MP), estructura real de carpetas (refresh_tokens con underscore, tests planos, widgets/entities vacíos), skills reales con paths y archivos correctos (14 skills, 3 sin SKILL.md, dashboard-crud-page y find-skills nuevas), variables de entorno reales (MP_ACCESS_TOKEN, BCRYPT_COST discrepancia), engram recall eliminado (comando no existe), devdocs-mcp sin config, openspec config.yaml vacío, decisiones arquitectónicas extendidas con realidad del repo |
| 3.0 | 2026-05-11 | Fusión AGENTS.md tuyo + profesor: protocolo Engram, delegación subagentes, paths skills, matriz, checklist, decisiones |
| 2.1 | 2026-05-05 | Ubicación y acceso documentado |
| 1.0 | — | Versión inicial |
