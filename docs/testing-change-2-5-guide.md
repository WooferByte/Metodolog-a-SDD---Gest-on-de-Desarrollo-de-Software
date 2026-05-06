# 🧪 Testing Manual de CHANGE 2.5 (backend-dev-infrastructure)

## ✅ Guía Completa para Validar Todo está Funcionando Correctamente

Este documento te proporciona un **paso a paso detallado** para probar manualmente todo lo implementado en CHANGE 2.5 y confirmar que está funcionando correctamente.

---

## 📋 Pre-requisitos

Antes de comenzar, asegúrate de tener:

- ✅ **Docker Desktop** instalado y ejecutándose
- ✅ **Git** instalado
- ✅ **Python 3.9+** instalado
- ✅ **Terminal/PowerShell** con permisos para ejecutar comandos
- ✅ Haber clonado el repositorio

**Verificar instalaciones:**
```powershell
docker --version          # Debe mostrar versión de Docker
python --version          # Debe mostrar Python 3.9+
git --version             # Debe mostrar versión de Git
```

---

## 🚀 PASO 1: Iniciar PostgreSQL con Docker Compose

### Objetivo
Verificar que Docker Compose puede iniciar correctamente PostgreSQL 16.

### Comandos

**1.1 - Revisar el archivo docker-compose.yml**
```powershell
# Posiciónate en la raíz del proyecto
cd "D:\1. Juan\5. Tecnicatura\4. Año Dos (Segundo Semestre)\4. Gestión de Software\Proyecto Agéntico con SDD\RepositorioBaseFoodStore-SDD"

# Visualiza la configuración
cat docker-compose.yml
```

**Qué observar:**
- ✅ Debe mostrar servicio `postgres` con imagen `postgres:16-alpine`
- ✅ Puerto `5432` mapeado
- ✅ Volumen `postgres_data` para persistencia
- ✅ Health check con `pg_isready`

---

**1.2 - Verificar la sintaxis de docker-compose**
```powershell
docker-compose config
```

**Qué observar:**
- ✅ Debe completarse sin errores
- ✅ Debe mostrar la configuración parseada correctamente
- ❌ Si hay error: Verifica que `docker-compose.yml` no tenga caracteres especiales

---

**1.3 - Iniciar PostgreSQL en background**
```powershell
docker-compose up -d
```

**Qué observar:**
- ✅ Mensaje: `Creating foodstore-postgres ... done`
- ✅ Sin errores de red o permisos
- ❌ Si error "port 5432 already in use": Ejecuta `docker-compose down` primero

---

**1.4 - Verificar que el contenedor está corriendo**
```powershell
docker ps
```

**Qué observar:**
- ✅ Debe listar un contenedor llamado `foodstore-postgres`
- ✅ Status debe ser `Up` (ej: `Up 2 minutes`)
- ✅ Port mapping: `0.0.0.0:5432->5432/tcp`

---

**1.5 - Verificar el health check**
```powershell
docker ps --format "table {{.Names}}\t{{.Status}}"
```

**Qué observar:**
- ✅ Status debe incluir `(healthy)` después de ~10 segundos
- ⏳ Si está `(health: starting)`: Espera otros 10 segundos
- ❌ Si está `(unhealthy)` después de 30 segundos: Ver logs

---

**1.6 - Ver los logs del contenedor**
```powershell
docker logs foodstore-postgres
```

**Qué observar:**
- ✅ Debe ver líneas como:
  ```
  PostgreSQL Database system is ready to accept connections
  pg_isready: accepting connections
  ```
- ❌ Si hay errores: Anótalos para debugging

---

**1.7 - Verificar conectividad a PostgreSQL**
```powershell
docker exec foodstore-postgres pg_isready -U postgres -d foodstore_db
```

**Qué observar:**
- ✅ Debe mostrar: `accepting connections`
- ✅ Exit code: `0` (sin errores)
- ❌ Si muestra `rejecting connections`: Espera un poco más

---

## ✅ PASO 1 COMPLETADO

Si llegaste hasta aquí con todos los ✅, significa:
- PostgreSQL está corriendo correctamente
- Docker Compose está bien configurado
- La configuración de ambiente es correcta

---

## 🔧 PASO 2: Configurar Variables de Ambiente

### Objetivo
Verificar que el archivo `.env` está correctamente configurado y puede ser leído por la aplicación.

### Comandos

**2.1 - Copiar el template .env.example a .env**
```powershell
cp .env.example .env
```

**Qué observar:**
- ✅ Archivo `.env` creado sin errores
- ✅ Debe estar en la raíz del proyecto

---

**2.2 - Revisar el contenido de .env**
```powershell
cat .env
```

**Qué observar:**
- ✅ Debe ver líneas como:
  ```
  DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/foodstore_db
  POSTGRES_USER=postgres
  POSTGRES_PASSWORD=postgres
  POSTGRES_DB=foodstore_db
  ```
- ✅ DATABASE_URL usa el driver `psycopg` (NO `asyncpg` ni `psycopg2`)

---

**2.3 - Verificar que .env está en .gitignore**
```powershell
cat .gitignore | grep -E "^\.env"
```

**Qué observar:**
- ✅ Debe ver línea `.env` (sin incluir `.env.example`)
- ✅ Esto previene que subas secretos a Git

---

## ✅ PASO 2 COMPLETADO

Si llegaste aquí con todos los ✅, significa:
- Variables de ambiente están configuradas correctamente
- DATABASE_URL usa el driver psycopg moderno

---

## 📦 PASO 3: Instalar Dependencias del Backend

### Objetivo
Verificar que todas las dependencias de Python se instalan correctamente con el driver psycopg[binary].

### Comandos

**3.1 - Entrar al directorio backend**
```powershell
cd backend
```

---

**3.2 - Crear y activar virtual environment**
```powershell
# Crear venv
python -m venv venv

# Activar (en PowerShell)
.\venv\Scripts\Activate.ps1

# Si da error de permisos, ejecuta:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Qué observar:**
- ✅ Terminal debe mostrar `(venv)` al inicio
- ✅ Sin errores de permisos
- ✅ `python --version` debe mostrar la versión correcta

---

**3.3 - Instalar dependencias desde requirements.txt**
```powershell
pip install -r requirements.txt
```

**Qué observar:**
- ✅ Debe completarse sin errores
- ✅ Debe instalar `psycopg[binary]==3.1.17` (busca en el output)
- ❌ Si hay errores: Verifica que Python 3.9+ está instalado
- ⏳ Puede tomar 2-3 minutos en la primera instalación

---

**3.4 - Verificar que psycopg está instalado**
```powershell
pip show psycopg
```

**Qué observar:**
- ✅ Debe mostrar:
  ```
  Name: psycopg
  Version: 3.1.17 (o similar)
  Summary: PostgreSQL adapter for Python
  ```
- ✅ Location debe ser algo como `...\venv\lib\site-packages`

---

**3.5 - Verificar todas las dependencias críticas**
```powershell
pip list | grep -E "fastapi|sqlmodel|psycopg|pydantic"
```

**Qué observar:**
- ✅ fastapi (versión reciente)
- ✅ sqlmodel
- ✅ psycopg 3.1.17
- ✅ pydantic

---

## ✅ PASO 3 COMPLETADO

Si llegaste aquí con todos los ✅, significa:
- Todas las dependencias se instalaron correctamente
- psycopg[binary] está disponible para conexiones async
- El ambiente Python está listo

---

## 🌱 PASO 4: Ejecutar el Script de Seed

### Objetivo
Verificar que el script de seed puede conectarse a PostgreSQL e inyectar datos iniciales de forma idempotente.

### Comandos

**4.1 - Revisar el script de seed**
```powershell
cat scripts/seed.py | head -50
```

**Qué observar:**
- ✅ Debe ver docstring explicando qué hace el script
- ✅ Debe importar `Rol`, `EstadoPedido`, `FormaPago`, `Usuario`
- ✅ Funciones `get_or_create_*` para idempotencia

---

**4.2 - Ejecutar el script de seed (PRIMERA VEZ)**
```powershell
python scripts/seed.py
```

**Qué observar - Output esperado:**
```
🌱 Starting database seed...
[CREATE] Created Rol 'ADMIN' (id=1)
[CREATE] Created Rol 'STOCK' (id=2)
[CREATE] Created Rol 'PEDIDOS' (id=3)
[CREATE] Created Rol 'CLIENT' (id=4)
[CREATE] Created EstadoPedido 'PENDIENTE' (id=1)
[CREATE] Created EstadoPedido 'CONFIRMADO' (id=2)
[CREATE] Created EstadoPedido 'EN_PREPARACIÓN' (id=3)
[CREATE] Created EstadoPedido 'EN_CAMINO' (id=4)
[CREATE] Created EstadoPedido 'ENTREGADO' (id=5)
[CREATE] Created EstadoPedido 'CANCELADO' (id=6)
[CREATE] Created FormaPago 'MERCADOPAGO' (id=1)
[CREATE] Created FormaPago 'EFECTIVO' (id=2)
[CREATE] Created FormaPago 'TRANSFERENCIA' (id=3)
[CREATE] Created Usuario 'admin@foodstore.com' (id=1)
✅ Database seeded successfully!
```

**Checklist:**
- ✅ Sin errores de conexión
- ✅ Se crearon 4 Roles
- ✅ Se crearon 6 EstadoPedidos
- ✅ Se crearon 3 FormaPagos
- ✅ Se creó 1 Usuario admin
- ❌ Si hay error de conexión: Verifica que Docker está corriendo y DATABASE_URL es correcto

---

**4.3 - Ejecutar el script de seed (SEGUNDA VEZ - Prueba Idempotencia)**
```powershell
python scripts/seed.py
```

**Qué observar - Output esperado:**
```
🌱 Starting database seed...
[EXISTS] Rol 'ADMIN' already exists (id=1)
[EXISTS] Rol 'STOCK' already exists (id=2)
[EXISTS] Rol 'PEDIDOS' already exists (id=3)
[EXISTS] Rol 'CLIENT' already exists (id=4)
[EXISTS] EstadoPedido 'PENDIENTE' already exists (id=1)
[EXISTS] EstadoPedido 'CONFIRMADO' already exists (id=2)
...
[EXISTS] Usuario 'admin@foodstore.com' already exists (id=1)
✅ Database seeded successfully!
```

**Checklist - MUY IMPORTANTE:**
- ✅ Todos los items muestran `[EXISTS]` (NO `[CREATE]`)
- ✅ Los IDs son los mismos que la primera ejecución
- ✅ Sin errores de duplicado o constraint violation
- ✅ **Esto confirma que el script es idempotente**

---

**4.4 - Verificar datos en PostgreSQL directamente**
```powershell
# Conectarse a la base de datos
docker exec -it foodstore-postgres psql -U postgres -d foodstore_db

# Dentro de psql, ejecuta:
SELECT * FROM rol;
SELECT * FROM estado_pedido;
SELECT * FROM forma_pago;
SELECT * FROM usuario;

# Salir
\q
```

**Qué observar:**
- ✅ Tabla `rol`: 4 registros (ADMIN, STOCK, PEDIDOS, CLIENT)
- ✅ Tabla `estado_pedido`: 6 registros (PENDIENTE, CONFIRMADO, etc.)
- ✅ Tabla `forma_pago`: 3 registros (MERCADOPAGO, EFECTIVO, TRANSFERENCIA)
- ✅ Tabla `usuario`: 1 admin user con email `admin@foodstore.com`

---

## ✅ PASO 4 COMPLETADO

Si llegaste aquí con todos los ✅, significa:
- Script de seed conecta correctamente a PostgreSQL
- Datos iniciales se inyectaron correctamente
- **El script es idempotente** (puede ejecutarse múltiples veces sin problemas)

---

## 🚀 PASO 5: Iniciar el Backend FastAPI

### Objetivo
Verificar que FastAPI puede iniciar, conectar a PostgreSQL, y que la API está disponible.

### Comandos

**5.1 - Iniciar el servidor FastAPI**
```powershell
python -m uvicorn main:app --reload
```

**Qué observar - Output esperado:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
```

**Checklist:**
- ✅ Sin errores de import o módulo faltante
- ✅ Sin errores de conexión a base de datos
- ✅ Puerto 8000 disponible
- ❌ Si hay error "Address already in use": Cambia puerto con `--port 8001`

---

**5.2 - En otra terminal, verificar la salud de la API**
```powershell
# Abre una NUEVA terminal PowerShell (no cierres la que está ejecutando uvicorn)
curl http://localhost:8000/health
```

**Qué observar:**
- ✅ Debe recibir respuesta HTTP 200
- ✅ Respuesta JSON (si existe endpoint `/health`)
- ❌ Si error "connection refused": Uvicorn no inició correctamente

---

**5.3 - Acceder a la documentación interactiva (Swagger UI)**
```
Abre en tu navegador:
http://localhost:8000/docs
```

**Qué observar:**
- ✅ Swagger UI carga correctamente (interfaz interactiva)
- ✅ Muestra todos los endpoints disponibles
- ✅ Panel de "Authorize" visible (para JWT auth)
- ✅ Sin errores en la consola del navegador

---

**5.4 - Verificar logs de conexión a base de datos**
```powershell
# En la terminal donde corre uvicorn, revisa el output
# Debe haber mensajes similares a:
# INFO: Connection pool initialized
# INFO: Database connected successfully
```

**Qué observar:**
- ✅ Logs sin errores de conexión
- ✅ Pool de conexiones inicializado
- ❌ Si hay "connection timeout": DATABASE_URL es incorrecto o PostgreSQL no está listo

---

## ✅ PASO 5 COMPLETADO

Si llegaste aquí con todos los ✅, significa:
- FastAPI inicia correctamente
- Conexión a PostgreSQL es exitosa
- API está accesible y documentada

---

## 🔐 PASO 6: Probar Autenticación (Endpoint /login)

### Objetivo
Verificar que el endpoint de login funciona con el usuario admin creado por el seed script.

### Comandos

**6.1 - Obtener JWT Token (desde Swagger UI)**
```
1. Ve a http://localhost:8000/docs
2. Busca el endpoint POST /auth/login (o similar, depende de tu implementación)
3. Haz clic en "Try it out"
4. Ingresa credenciales:
   - email: admin@foodstore.com
   - password: Admin123!
5. Haz clic en "Execute"
```

**Qué observar:**
- ✅ Response Code: 200 (OK)
- ✅ Response body contiene `access_token` y `token_type`
- ✅ Token es un JWT válido (formato: `eyJhbGciOiJIUzI1NiI...`)

---

**6.2 - Alternativa: Probar login con curl**
```powershell
curl -X POST "http://localhost:8000/auth/login" `
  -H "Content-Type: application/json" `
  -d @- <<EOF
{
  "email": "admin@foodstore.com",
  "password": "Admin123!"
}
EOF
```

**Qué observar:**
- ✅ Response JSON con `access_token`
- ✅ Sin errores 401 o 403

---

## ✅ PASO 6 COMPLETADO

Si llegaste aquí con todos los ✅, significa:
- Autenticación JWT funciona
- Usuario admin fue creado correctamente por el seed script
- Backend está totalmente operacional

---

## 📊 PASO 7: Verificar Persistencia de Datos

### Objetivo
Confirmar que los datos en PostgreSQL persisten incluso después de detener y reiniciar el contenedor.

### Comandos

**7.1 - Detener el backend (Presiona CTRL+C en la terminal de uvicorn)**
```powershell
# En la terminal donde corre uvicorn:
CTRL+C
```

---

**7.2 - Detener el contenedor de PostgreSQL (SIN eliminar datos)**
```powershell
docker-compose down
# Nota: NO uses 'docker-compose down -v' (eso sí elimina los datos)
```

**Qué observar:**
- ✅ Contenedor se detiene correctamente
- ✅ Volumen `postgres_data` permanece (con los datos)

---

**7.3 - Reiniciar PostgreSQL**
```powershell
docker-compose up -d
```

**Qué observar:**
- ✅ Contenedor inicia correctamente
- ✅ Health check pasa después de ~10 segundos

---

**7.4 - Verificar que los datos persisten**
```powershell
docker exec foodstore-postgres psql -U postgres -d foodstore_db -c "SELECT COUNT(*) FROM rol;"
```

**Qué observar:**
- ✅ Debe retornar `4` (los 4 roles que seeded anteriormente)
- ✅ Los datos NO se borraron al detener el contenedor

---

**7.5 - Opcional: Iniciar backend nuevamente y verificar**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload
```

**Qué observar:**
- ✅ FastAPI inicia sin errores
- ✅ Puede conectar a PostgreSQL sin problemas
- ✅ `http://localhost:8000/docs` funciona

---

## ✅ PASO 7 COMPLETADO

Si llegaste aquí con todos los ✅, significa:
- **Persistencia de datos funciona correctamente**
- El volumen Docker mantiene los datos entre reinicios
- Infraestructura es robusta para desarrollo

---

## 🎯 CHECKLIST FINAL - ¿CHANGE 2.5 Está Bien?

Marca todo lo que confirmaste:

### Infraestructura Docker
- [ ] `docker-compose config` sin errores
- [ ] `docker-compose up -d` inicia el contenedor
- [ ] `docker ps` muestra contenedor `foodstore-postgres` corriendo
- [ ] Health check muestra `(healthy)` después de ~10 segundos
- [ ] `docker exec foodstore-postgres pg_isready` retorna `accepting connections`

### Configuración de Ambiente
- [ ] Archivo `.env` existe con DATABASE_URL correcto
- [ ] DATABASE_URL usa driver `psycopg` (no asyncpg ni psycopg2)
- [ ] `.env` está en `.gitignore`

### Dependencias Python
- [ ] `pip install -r requirements.txt` completó sin errores
- [ ] `psycopg[binary]==3.1.17` está instalado
- [ ] FastAPI, SQLModel, Pydantic están instalados

### Seed Script
- [ ] Primera ejecución: Todos los items muestran `[CREATE]`
- [ ] Segunda ejecución: Todos los items muestran `[EXISTS]`
- [ ] Se crearon 4 Roles, 6 EstadoPedidos, 3 FormaPagos, 1 Usuario admin
- [ ] Datos verificados directamente en PostgreSQL

### Backend FastAPI
- [ ] `python -m uvicorn main:app --reload` inicia sin errores
- [ ] `http://localhost:8000/docs` (Swagger UI) carga correctamente
- [ ] Endpoint login funciona con admin@foodstore.com / Admin123!
- [ ] JWT token se genera correctamente

### Persistencia
- [ ] `docker-compose down` seguido de `docker-compose up -d` retiene datos
- [ ] Los 4 roles siguen en la base de datos después del reinicio
- [ ] Backend se reconecta sin problemas después del reinicio de PostgreSQL

---

## ✅ ¿TODOS LOS CHECKBOXES MARCADOS?

**SI** → **CHANGE 2.5 está 100% funcionando correctamente** ✨

**NO** → Revisa la sección correspondiente y ejecuta los comandos nuevamente

---

## 🆘 Troubleshooting Rápido

### Error: "Port 5432 already in use"
```powershell
docker ps
docker kill <container-id>
docker-compose up -d
```

### Error: "Connection refused" en seed script
```powershell
# Verifica que PostgreSQL está healthy
docker ps --format "table {{.Names}}\t{{.Status}}"
# Espera a que muestre "(healthy)"
# Luego ejecuta seed script nuevamente
```

### Error: "ModuleNotFoundError: No module named 'psycopg'"
```powershell
# Verifica que estás en el venv
.\venv\Scripts\Activate.ps1
# Reinstala dependencias
pip install -r requirements.txt
```

### Error: "DATABASE_URL format incorrect"
```powershell
# Verifica .env tiene:
# DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/foodstore_db
# (NO asyncpg, NO psycopg2)
cat .env | grep DATABASE_URL
```

---

## 📝 Próximos Pasos

Una vez que CHANGE 2.5 está validado:
1. ✅ **Backend está listo** para CHANGE 3 (frontend-setup)
2. ✅ **PostgreSQL está funcional** con datos iniciales
3. ✅ **Autenticación JWT funciona** con usuario admin
4. ✅ **Persistencia de datos funciona** entre reinicios

**¿Listo para CHANGE 3?** El backend está 100% listo.

---

**Last Updated**: April 24, 2026
**Version**: 1.0
**CHANGE**: 2.5 (backend-dev-infrastructure)
