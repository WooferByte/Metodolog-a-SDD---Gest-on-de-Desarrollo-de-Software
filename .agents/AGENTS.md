# AGENTS.md — Food Store E-Commerce

**Food Store** es un e-commerce de alimentos con: React + FastAPI, RBAC (4 roles), integración MercadoPago, máquina de estados pedidos, ERD v5 (16 tablas), SDD con OPSX.

---

## 📍 UBICACIÓN Y USO DE ESTE ARCHIVO

> **CRÍTICO**: Este archivo DEBE estar en `.agents/AGENTS.md` (en el proyecto, versionado en Git).

### ¿Por qué aquí?

- ✅ **Parte del proyecto**: Versionado con Git, diferente por proyecto
- ✅ **Contexto específico Food Store**: Stack, skills, matriz CHANGEs, patrones
- ✅ **Accesible a todos los agentes**: Inyectado en contexto principal + delegaciones
- ✅ **Persistencia**: Engram guarda referencias a este archivo para futuras sesiones

### Cómo se usa:

**Yo (Orquestador)**:
- Leo este archivo al inicio de cada sesión
- Cargo skills especificados en la Matriz Skills vs. Changes
- Doy contexto a subagentes en cada delegación

**Subagentes** (delegados):
- Reciben referencia a este archivo en el prompt
- Leen la Matriz Skills vs. Changes para saber qué skills cargar
- Siguen los patrones documentados en "Decisiones Arquitectónicas Clave"
- Respetan el Checklist Antes de Commitear

**Si este archivo NO está aquí**:
- ❌ Los agentes NO tendrán contexto de proyecto
- ❌ Los skills NO serán cargados en orden correcto
- ❌ Los patrones NO serán seguidos uniformemente
- ❌ Las sesiones futuras perderán contexto

---

## 🎯 Stack Tecnológico

| Capa | Tecnologías |
|------|------------|
| **Frontend** | React 18, TypeScript, Vite, Zustand, TanStack Query, Axios, Tailwind CSS, React Router |
| **Backend** | FastAPI, SQLModel, Alembic, PostgreSQL, Passlib[bcrypt], python-jose, slowapi, MercadoPago SDK |

---

## 📁 Estructura

```
backend/           ← Feature-first (auth/, usuarios/, productos/, etc.)
frontend/          ← Feature-Sliced Design (app/, pages/, widgets/, features/, entities/, shared/)
docs/              ← Descripcion.txt, Historias_de_usuario.txt, CHANGES.md
openspec/          ← Changes y specs SDD
.agents/           ← AGENTS.md (ESTE ARCHIVO) + skills/ locales
```

---

## 🛠️ Skills Locales: Cuándo Usarlas

### 1. **python-fastapi-ddd-skill** ← SIEMPRE para backend
Pattern: Router → Service → UoW → Repository → Model (feature-first vertical)

### 2. **api-design** ← Nuevo endpoint REST
Pattern: `/api/v1/recurso`, métodos HTTP correctos, RFC 7807 errors, paginación

### 3. **jwt-security** ← Auth, tokens, refresh
Pattern: Access token 30min, refresh token 7días, rotación + replay attack detection

### 4. **rest-api-design-patterns** ← Estructura API global
Pattern: Versionado `/api/v1`, query params para filtros, HATEOAS

### 5. **supabase-postgres-best-practices** ← Optimizar queries
Pattern: Indexes en FK, SELECT FOR UPDATE para stock, CTE para jerárquico, EXPLAIN ANALYZE

### 6. **tailwind-design-system** ← Componentes reutilizables
Pattern: Design tokens (colores, espacios), dark mode, componentes atómicos

### 7. **ui-design-system** ← Accesibilidad + Radix/shadcn
Pattern: Radix primitivos, ARIA labels, keyboard nav, WCAG 2.1 AA

### 8. **vercel-react-best-practices** ← Performance frontend
Pattern: Code splitting (lazy load rutas), memoize si mide costo, TanStack Query staleTime, bundle < 200KB

### 9. **zustand-state-management** ← Stores cliente
Pattern: 4 stores (authStore, cartStore, paymentStore, uiStore), slice subscription, localStorage persist

### 10. **web-payments** ← MercadoPago checkout
Pattern: Tarjeta tokenizada en cliente (SDK), webhook IPN, idempotency_key, PCI DSS SAQ-A

### 11. **frontend-state-management** ← Eligir estado
Pattern: Zustand (cliente) + TanStack Query (servidor), NO duplicar datos

### 12. **expo-tailwind-setup**
⚫ NO usar (proyecto es web-only, habilitar si pivota mobile)

---

## 📊 Matriz Skills vs. Changes

| Change | fastapi-ddd | api-design | jwt | rest-api | postgres | tailwind | ui | react-perf | zustand | payments |
|--------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| backend-fastapi-core | ✅ | ✅ | - | ✅ | - | - | - | - | - | - |
| auth-login/register | ✅ | ✅ | ✅ | ✅ | - | - | - | - | - | - |
| products-crud | ✅ | ✅ | - | ✅ | ✅ | - | - | - | - | - |
| orders-fsm | ✅ | ✅ | - | ✅ | ✅ | - | - | - | - | - |
| payments-mp | ✅ | ✅ | - | ✅ | ✅ | - | - | - | - | ✅ |
| frontend-catalog | - | - | - | - | - | ✅ | ✅ | ✅ | - | - |
| frontend-cart | - | - | - | - | - | ✅ | ✅ | - | ✅ | - |
| frontend-checkout | - | - | - | - | - | ✅ | ✅ | ✅ | ✅ | ✅ |
| admin-dashboard | - | - | - | - | ✅ | ✅ | - | ✅ | - | - |

---

## 🚀 Guía por Escenario

### Implementar módulo backend nuevo
```
1. Cargar python-fastapi-ddd-skill
2. Crear carpeta modulo/ → model.py, schemas.py, repository.py, service.py, router.py
3. Repository hereda BaseRepository[T]
4. Service contiene lógica negocio
5. Router con require_role() para autorización
6. Cargar api-design para validar endpoints
```

### Implementar endpoint pagos
```
1. Cargar python-fastapi-ddd-skill + web-payments
2. Modelo Pago + schema
3. Router: POST /pagos/crear + POST /pagos/webhook
4. UoW atómico: PENDIENTE → CONFIRMADO + decremento stock
5. Validar webhook signature MercadoPago
```

### Componente UI accesible
```
1. Cargar ui-design-system + tailwind-design-system
2. Radix primitivos, Tailwind utilities, ARIA labels
3. Validar WCAG 2.1 AA (contrast, keyboard nav)
4. Cargar vercel-react-best-practices si needed
```

### Optimizar performance
```
1. Profiler / Lighthouse
2. Cargar vercel-react-best-practices
3. Lazy load rutas (React.lazy + Suspense)
4. TanStack Query staleTime para caching
5. Revisar bundle size
```

### Indexar BD
```
1. EXPLAIN ANALYZE query lenta
2. Cargar supabase-postgres-best-practices
3. Crear index en FK, WHERE, JOIN
4. SELECT FOR UPDATE para stock decrement
```

---

## ✅ Checklist Antes de Commitear

- [ ] ¿Requiere JWT? ¿Validado?
- [ ] ¿Requiere rol? ¿require_role() aplicado?
- [ ] ¿Validación Pydantic?
- [ ] ¿Queries parametrizadas (no SQL concat)?
- [ ] ¿.env NO commiteado? (solo .env.example)
- [ ] ¿Passwords hasheadas bcrypt cost >= 10?
- [ ] ¿JWT refresh rotated?
- [ ] ¿Rate limiting en endpoints sensibles?
- [ ] ¿UoW commit/rollback correcto?
- [ ] ¿Tests escritos?

---

## 🎓 Workflow SDD

```
1. Usuario solicita cambio
   ↓
2. Identificar skill(s) necesaria(s)
   ↓
3. Cargar skill() antes de escribir código
   ↓
4. Implementar siguiendo guidance + patrones
   ↓
5. Tests >= 60% (backend), >= 40% (frontend)
   ↓
6. Commitear + Archivar change OPSX
```

---

## 🔗 Referencia Documentación

| Documento | Ubicación | Qué |
|-----------|-----------|-----|
| Visión + Stack + Arquitectura | `docs/Descripcion.txt` | Completo del sistema |
| Historias de usuario + Reglas negocio | `docs/Historias_de_usuario.txt` | Todas las US, criterios aceptación |
| Mapeo completo changes OPSX | `docs/CHANGES.md` | 30+ changes + dependencias + orden |
| ERD v5 (16 tablas) | `docs/Descripcion.txt` § 4 | Modelo datos |
| API REST endpoints | `docs/Descripcion.txt` § 7 | Todos los endpoints |

---

## 🏗️ Decisiones Arquitectónicas Clave

**Backend**: DDD + Onion (Router → Service → UoW → Repository → Model). UoW = context manager para transacciones ACID. Soft delete = nunca hard-delete, solo `eliminado_en = now()`.

**Frontend**: FSD (rutas → pages → widgets → features → entities → shared). Zustand (cliente) + TanStack Query (servidor). NUNCA duplicar datos entre stores.

**BD**: PostgreSQL 3NF, 16 tablas, 3 dominios. Snapshots para inmutabilidad (precio_snapshot, direccion_snapshot). HistorialEstadoPedido append-only (solo INSERT).

**Seguridad**: RBAC 4 roles (ADMIN, STOCK, PEDIDOS, CLIENT). JWT 30min access + 7días refresh con rotación. PCI DSS SAQ-A: tarjeta tokenizada en cliente (SDK MP), nunca en servidor.

---

# ⚡ REGLAS DE ORO PARA TODOS LOS AGENTES (SDD)

> **🔴 CRÍTICO**: Estas reglas DEBEN ser leídas y aplicadas en CADA SESIÓN.
> **⚠️ NOTA PARA FUTURAS SESIONES**: Si no ves esta confirmación al inicio, el agente NO leyó AGENTS.md. Pide que lo haga.

---

## Regla 0: LECTURA OBLIGATORIA AL INICIO DE CADA SESIÓN

**ANTES de hacer CUALQUIER cosa en un Change nuevo:**

1. Lee este archivo AGENTS.md completo (especialmente las Reglas de Oro)
2. Ejecuta `git status` para verificar estado limpio
3. Responde con: **"✅ AGENTS.md leído. Estado limpio. Listo para continuar."**

Si saltás este paso, el usuario DEBE decir: "Leé AGENTS.md" y parar todo hasta que lo hagas.

---

## Regla 1: Verificación pre-CHANGE

**ANTES de comenzar CUALQUIER CHANGE N:**

```bash
1. git status                    # → "nothing to commit, working tree clean"
2. git log -1 --oneline         # → verificar hash = último checkpoint
3. openspec list                # → sin cambios activos
```

Si algo falla → **STOP**. NO continúes. Pregunta: "¿Procedo a limpiar/commitear o esperamos tu instrucción?"

---

## Regla 2: Tests Automáticos ANTES de Archive

**DESPUÉS de implementar, y ANTES de pasar a testing manual:**

```bash
# Backend
cd backend && pytest --cov=. --cov-report=term-missing
poetry run ruff check .
poetry run black --check .

# Frontend (si aplica)
cd frontend && npm run test
npm run lint

# Build
cd backend && python -m pip check
cd frontend && npm run build
```

**Si algo falla:**
- ❌ NO generes guía de testing manual
- ❌ NO pidas confirmación
- ✅ CORRIGE el error
- ✅ Corre tests de nuevo
- ✅ Recién entonces → Regla 3

**Si TODO pasa:**
- ✅ Procede a Regla 3

---

## Regla 3: Guía de Testing Manual (EL PASO CRÍTICO)

**ESTO ES LO MÁS IMPORTANTE.** El usuario va a testear MANUALMENTE y confirmar.

### Formato EXACTO que SIEMPRE debes usar:

---

### 📋 PASOS PARA TESTEO MANUAL - CHANGE [NOMBRE]

**Tu responsabilidad:** Ejecutar tests automáticos, luego generar esta guía ANTES de pedir confirmación.

**Mi responsabilidad (usuario):** Seguir los pasos al pie de la letra y confirmar.

---

#### 🔧 **PASO 1: Preparar el entorno**

**Qué hacer:**
```bash
# Asegúrate de estar en la raíz del proyecto
cd RepositorioBaseFoodStore-SDD

# Verifica Docker
docker ps
# Debería listar contenedores. Si está vacío, ejecuta:
docker-compose up -d

# Verifica conexión BD
docker exec foodstore-postgres pg_isready
# Debería mostrar: "accepting connections"
```

**Qué observar:**
- ✅ Docker lista PostgreSQL corriendo
- ✅ `pg_isready` responde "accepting connections"

**Si ves esto → ✅ Paso 1 OK**

---

#### 🚀 **PASO 2: Levantar Backend**

**Qué hacer:**
```bash
cd backend
poetry shell
poetry install  # Si faltan dependencias
uvicorn main:app --reload
```

**Qué observar:**
- ✅ No errores en la consola
- ✅ Ves "Application startup complete"
- ✅ La URL local es http://localhost:8000

**Prueba inmediata:**
```bash
# En otra terminal:
curl http://localhost:8000/docs
```

**Qué observar:**
- ✅ Se abre Swagger UI (documentación interactiva)
- ✅ Ves todos los endpoints listados

**Si ves esto → ✅ Paso 2 OK**

---

#### 🎨 **PASO 3: Levantar Frontend** (si el Change es frontend)

**Qué hacer:**
```bash
cd frontend
npm install  # Si faltan dependencias
npm run dev
```

**Qué observar:**
- ✅ No errores en la consola
- ✅ Ves "Local: http://localhost:5173"
- ✅ Abre el navegador automáticamente a esa URL

**Si ves esto → ✅ Paso 3 OK**

---

#### ✔️ **PASO 4: Testing específico del Change**

> [AQUÍ VA EL PASO A PASO DETALLADO PARA CADA CHANGE]
> Ejemplo: "Click en botón X, espera respuesta Y, verifica que Z aparezca en consola"

**Qué hacer:**
[Instrucciones detalladas por feature]

**Qué observar:**
[Descripción exacta de qué debe aparecer en pantalla/consola/BD]

**Checklist de validación:**
- [ ] Observación 1 presente
- [ ] Observación 2 presente
- [ ] Observación 3 presente

**Si TODAS las observaciones están presentes → ✅ Paso 4 OK**

---

#### 📊 **PASO 5: Validar en Base de Datos**

**Qué hacer:**
```bash
docker exec -it foodstore-postgres psql -U postgres -d foodstore_db -c "[QUERY ESPECÍFICA]"
```

**Qué observar:**
[Descripción de qué datos debería haber en la BD]

**Si ves esto → ✅ Paso 5 OK**

---

### ✅ **CHECKLIST FINAL**

Si TODOS estos puntos son ✅, entonces el Change funciona correctamente:

- [ ] Paso 1: Entorno preparado
- [ ] Paso 2: Backend levantado sin errores
- [ ] Paso 3: Frontend levantado (si aplica)
- [ ] Paso 4: Feature funciona como se describió
- [ ] Paso 5: BD tiene los datos esperados

---

### 🎯 **CUANDO VEAS ESTO, RESPONDE:**

**"✅ Todo funciona correctamente. Aprobado para archivar CHANGE [NOMBRE]"**

**RECIÉN ENTONCES** yo ejecuto:
```bash
openspec archive change "[nombre-del-change]"
git add .
git commit -m "chore: archive CHANGE [nombre]"
```

---

## Regla 4: Workflow Completo de un Change

```
1. Usuario pide nuevo Change
   ↓
2. Yo: Leo AGENTS.md (Regla 0) + Regla 1
   ↓
3. Yo: Creo Change (openspec new change)
   ↓
4. Yo: Cumplo Regla 2 (tests automáticos)
   ↓
5. Yo: Genero Regla 3 (guía testing manual)
   ↓
6. Usuario: Sigue pasos de Regla 3 y confirma ✅
   ↓
7. Yo: Ejecuto Regla 4 (archive change)
```

---

## 📝 **Última actualización**: 5 de mayo de 2026
## 📌 **Versión**: 2.1 — Ubicación y acceso de AGENTS.md documentado. Listo para delegaciones con contexto completo.
