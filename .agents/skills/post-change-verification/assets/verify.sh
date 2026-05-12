#!/usr/bin/env bash
# post-change-verification/assets/verify.sh
# Health check completo para Food Store.
# Uso: bash .agents/skills/post-change-verification/assets/verify.sh [backend|frontend|all]

set -e
ROOT="$(git rev-parse --show-toplevel)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
MODE="${1:-all}"
PASS=0
FAIL=0

green() { echo -e "\033[32m✅ $1\033[0m"; ((PASS++)); }
red()   { echo -e "\033[31m❌ $1\033[0m"; ((FAIL++)); }

# ── BACKEND ────────────────────────────────────────────────────
if [[ "$MODE" == "backend" || "$MODE" == "all" ]]; then
  echo -e "\n── BACKEND ──────────────────────────"

  # Pytest
  if cd "$BACKEND" && .venv/Scripts/pytest -x -q --tb=no 2>/dev/null; then
    green "pytest OK"
  else
    red "pytest FAIL"
  fi

  # Alembic
  if cd "$BACKEND" && .venv/Scripts/alembic upgrade head 2>/dev/null; then
    green "alembic upgrade head OK"
  else
    red "alembic upgrade head FAIL"
  fi

  # Uvicorn import check (sin levantar servidor)
  if cd "$BACKEND" && .venv/Scripts/python -c "from main import app; print('OK')" 2>/dev/null | grep -q "OK"; then
    green "main.py imports OK"
  else
    red "main.py imports FAIL"
  fi
fi

# ── FRONTEND ───────────────────────────────────────────────────
if [[ "$MODE" == "frontend" || "$MODE" == "all" ]]; then
  echo -e "\n── FRONTEND ─────────────────────────"

  # TypeScript
  if cd "$FRONTEND" && npx tsc --noEmit 2>/dev/null; then
    green "tsc --noEmit OK"
  else
    red "tsc --noEmit FAIL"
  fi

  # Vitest
  if cd "$FRONTEND" && npx vitest run --reporter=verbose 2>/dev/null | tail -5 | grep -q "passed"; then
    green "vitest OK"
  else
    red "vitest FAIL"
  fi

  # Build
  if cd "$FRONTEND" && npm run build 2>/dev/null | tail -3 | grep -q "built in\|dist/"; then
    green "npm run build OK"
  else
    red "npm run build FAIL"
  fi
fi

# ── RESUMEN ────────────────────────────────────────────────────
echo -e "\n── RESULTADO ────────────────────────"
echo "  Pasaron: $PASS"
echo "  Fallaron: $FAIL"

if [[ $FAIL -eq 0 ]]; then
  echo -e "\033[32m\n✅ CHANGE LISTO PARA ARCHIVAR\033[0m"
  exit 0
else
  echo -e "\033[31m\n❌ CORREGIR ANTES DE ARCHIVAR\033[0m"
  exit 1
fi
