---
name: post-change-verification
description: >
  Health check automático después de cada change implementado en Food Store.
  Verifica: pytest sin regresiones, alembic upgrade head, uvicorn levanta,
  vitest sin regresiones, npm run build compila, imports @/ sin errores TypeScript,
  y flujo de auth completo funciona con el backend real.
  Trigger: después de opsx:apply y antes de opsx:archive, cuando el usuario
  pide verificar un change, o antes de hacer merge a main.
license: Apache-2.0
metadata:
  author: food-store-team
  version: "1.0"
---

## When to Use

- Después de `opsx:apply` — antes de pedir aprobación al usuario para archivar
- Cuando el usuario dice "verificá", "corré los tests", "health check"
- Antes de cada `opsx:archive` para confirmar que no hay regresiones
- Cuando se instalan nuevas dependencias (pip o npm)

## Checklist Completo

Ejecutar en orden. Si algún paso falla → corregir antes de continuar.

### NIVEL 1 — Backend estático (sin DB ni servidor)

```bash
# 1.1 Lint y tipos
cd backend
.venv/Scripts/black --check .
.venv/Scripts/flake8 .

# 1.2 Tests unitarios + cobertura
.venv/Scripts/pytest --cov=. --cov-report=term-missing -x -q
# -x = parar al primer fallo, -q = output compacto
# Threshold mínimo: ≥ 60% backend coverage
```

### NIVEL 2 — Backend con base de datos

```bash
# 2.1 Verificar Docker corriendo
docker ps | grep foodstore-postgres

# 2.2 Migraciones al día
cd backend
.venv/Scripts/alembic upgrade head
# Debe terminar sin error. Si dice "already up to date" → OK

# 2.3 Verificar estado de migraciones
.venv/Scripts/alembic current
# Debe mostrar el hash de la última migración con "(head)"
```

### NIVEL 3 — Backend servidor

```bash
# 3.1 Levantar uvicorn y verificar startup
cd backend
.venv/Scripts/uvicorn main:app --reload &
sleep 3

# 3.2 Health check HTTP
curl -s http://localhost:8000/docs | grep -q "swagger" && echo "✅ Swagger OK" || echo "❌ Swagger FAIL"

# 3.3 Verificar endpoint auth
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@foodstore.com","password":"admin123456"}' \
  | python -c "import sys,json; d=json.load(sys.stdin); print('✅ Login OK, token:', d.get('access_token','')[:20]+'...')" \
  2>/dev/null || echo "❌ Login FAIL"
```

### NIVEL 4 — Frontend estático

```bash
# 4.1 TypeScript sin errores
cd frontend
npx tsc --noEmit
# Debe terminar con exit 0 y sin output

# 4.2 Tests unitarios
npx vitest run
# Todos los tests deben pasar. Threshold mínimo: ≥ 40% frontend coverage

# 4.3 Build de producción
npm run build
# Debe generar dist/ sin errores
# Warning sobre chunk size es OK, ERROR no es OK
```

### NIVEL 5 — Integración frontend + backend

```bash
# 5.1 Dev server arranca
cd frontend
npm run dev &
sleep 5
curl -s http://localhost:5173 | grep -q "root" && echo "✅ Dev server OK" || echo "❌ Dev server FAIL"
```

## Comandos Rápidos (copiar-pegar)

```bash
# ── BACKEND completo ──────────────────────────────────────────
cd "C:/workspace/University/2026/gestion/food-store/Metodolog-a-SDD---Gest-on-de-Desarrollo-de-Software/backend"
.venv/Scripts/pytest -x -q && echo "✅ Tests OK"
.venv/Scripts/alembic upgrade head && echo "✅ Migraciones OK"

# ── FRONTEND completo ─────────────────────────────────────────
cd "C:/workspace/University/2026/gestion/food-store/Metodolog-a-SDD---Gest-on-de-Desarrollo-de-Software/frontend"
npx tsc --noEmit && echo "✅ TypeScript OK"
npx vitest run && echo "✅ Tests OK"
npm run build && echo "✅ Build OK"
```

## Paths Críticos del Proyecto

| Recurso | Path |
|---------|------|
| Venv Python (Windows) | `backend/.venv/Scripts/` |
| Venv Python (Unix) | `backend/.venv/bin/` |
| Pytest config | `backend/pyproject.toml` |
| Alembic config | `backend/alembic.ini` |
| Migraciones | `backend/alembic/versions/` |
| Vitest config | `frontend/vite.config.ts` |
| TS config | `frontend/tsconfig.json` |
| Path alias `@/` | `frontend/src/` |
| Admin seed | `admin@foodstore.com` / `admin123456` |
| Backend URL | `http://localhost:8000` |
| Frontend URL | `http://localhost:5173` |

## Criterios de Aprobación por Change

| Change type | Criterio mínimo |
|-------------|----------------|
| Backend puro | pytest ≥60% cov, alembic head, uvicorn arranca |
| Frontend puro | vitest ≥40% cov, tsc sin errores, build sin errores |
| Full-stack | Todos los niveles 1-5 |
| Solo migración | alembic upgrade head + alembic current muestra (head) |
| Solo tests | pytest/vitest pasan, coverage no baja respecto al anterior |

## Errores Comunes y Fix Rápido

| Error | Causa | Fix |
|-------|-------|-----|
| `MissingBackendError: bcrypt` | Venv no activo o bcrypt no instalado | `cd backend && .venv/Scripts/pip install bcrypt==3.2.2` |
| `pydantic_core` no compila | pydantic<2.8.2 en Python 3.13 | `pip install "pydantic>=2.8.2"` |
| `alembic: Can't locate revision` | Migración fuera de orden | `alembic history` → verificar cadena |
| `Cannot find module '@/...'` | tsconfig paths no configurado | Verificar `tsconfig.json` paths `@/*` → `./src/*` |
| `VITE_API_BASE_URL undefined` | `.env` no existe | Copiar `.env.example` a `.env` y completar |
| Tests fallan por `import.meta.env` | vitest no define env vars | Agregar `define: { 'import.meta.env.VITE_...': '"..."' }` en vite.config.ts |

## Integración con OPSX

Antes de invocar `opsx:archive`, el agente debe confirmar:

```
✅ pytest: X/X passing, Y% coverage
✅ alembic: at head (hash XXXXXXXX)
✅ vitest: X/X passing
✅ tsc: 0 errors
✅ build: compiled successfully
```

Si algún ítem falla → corregir primero, NO archivar con errores.
