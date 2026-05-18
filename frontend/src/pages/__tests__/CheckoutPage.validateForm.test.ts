/**
 * Unit tests for the validateForm() function extracted from CheckoutPage.
 *
 * Tests BUG 1 fix: phone validation must strip non-digits before testing
 * the 7-15 digit rule, and must treat empty/whitespace-only as valid (optional field).
 */

import { describe, it, expect } from 'vitest'

// ---------------------------------------------------------------------------
// Inline copy of validateForm (extracted from CheckoutPage for unit testing)
// Must stay in sync with frontend/src/pages/CheckoutPage.tsx
// ---------------------------------------------------------------------------

interface BuyerForm {
  nombre_comprador: string
  email_comprador: string
  telefono_comprador: string
}

interface FormErrors {
  nombre_comprador?: string
  email_comprador?: string
  telefono_comprador?: string
}

function validateForm(form: BuyerForm): FormErrors {
  const errors: FormErrors = {}

  if (!form.nombre_comprador.trim()) {
    errors.nombre_comprador = 'El nombre es obligatorio'
  } else if (form.nombre_comprador.trim().length < 3) {
    errors.nombre_comprador = 'El nombre debe tener al menos 3 caracteres'
  }

  if (!form.email_comprador.trim()) {
    errors.email_comprador = 'El email es obligatorio'
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email_comprador)) {
    errors.email_comprador = 'Ingresá un email válido'
  }

  const telefonoDigits = form.telefono_comprador.replace(/\D/g, '')
  if (form.telefono_comprador.trim() && !/^\d{7,15}$/.test(telefonoDigits)) {
    errors.telefono_comprador = 'El teléfono debe contener entre 7 y 15 dígitos (solo números)'
  }

  return errors
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const validBase: BuyerForm = {
  nombre_comprador: 'Juan Pérez',
  email_comprador: 'juan@example.com',
  telefono_comprador: '',
}

// ---------------------------------------------------------------------------
// BUG 1 — telefono_comprador validation
// ---------------------------------------------------------------------------

describe('validateForm — telefono_comprador (BUG 1 fix)', () => {
  it('vacío → sin error (campo opcional)', () => {
    const errors = validateForm({ ...validBase, telefono_comprador: '' })
    expect(errors.telefono_comprador).toBeUndefined()
  })

  it('solo espacios → sin error (no se considera valor ingresado)', () => {
    const errors = validateForm({ ...validBase, telefono_comprador: '   ' })
    expect(errors.telefono_comprador).toBeUndefined()
  })

  it('"abc" → error (no es un número)', () => {
    const errors = validateForm({ ...validBase, telefono_comprador: 'abc' })
    expect(errors.telefono_comprador).toBe(
      'El teléfono debe contener entre 7 y 15 dígitos (solo números)',
    )
  })

  it('"123456" (6 dígitos) → error (mínimo 7)', () => {
    const errors = validateForm({ ...validBase, telefono_comprador: '123456' })
    expect(errors.telefono_comprador).toBe(
      'El teléfono debe contener entre 7 y 15 dígitos (solo números)',
    )
  })

  it('"1234567" (7 dígitos) → sin error', () => {
    const errors = validateForm({ ...validBase, telefono_comprador: '1234567' })
    expect(errors.telefono_comprador).toBeUndefined()
  })

  it('"123456789012345" (15 dígitos) → sin error', () => {
    const errors = validateForm({
      ...validBase,
      telefono_comprador: '123456789012345',
    })
    expect(errors.telefono_comprador).toBeUndefined()
  })

  it('"1234567890123456" (16 dígitos) → error (máximo 15)', () => {
    const errors = validateForm({
      ...validBase,
      telefono_comprador: '1234567890123456',
    })
    expect(errors.telefono_comprador).toBe(
      'El teléfono debe contener entre 7 y 15 dígitos (solo números)',
    )
  })

  it('"+54 11 2345-6789" (número formateado) → sin error (strip non-digits = 12 dígitos)', () => {
    const errors = validateForm({
      ...validBase,
      telefono_comprador: '+54 11 2345-6789',
    })
    expect(errors.telefono_comprador).toBeUndefined()
  })
})

// ---------------------------------------------------------------------------
// nombre_comprador validation
// ---------------------------------------------------------------------------

describe('validateForm — nombre_comprador', () => {
  it('vacío → error "El nombre es obligatorio"', () => {
    const errors = validateForm({ ...validBase, nombre_comprador: '' })
    expect(errors.nombre_comprador).toBe('El nombre es obligatorio')
  })

  it('solo espacios → error "El nombre es obligatorio"', () => {
    const errors = validateForm({ ...validBase, nombre_comprador: '   ' })
    expect(errors.nombre_comprador).toBe('El nombre es obligatorio')
  })

  it('2 caracteres → error "al menos 3 caracteres"', () => {
    const errors = validateForm({ ...validBase, nombre_comprador: 'AB' })
    expect(errors.nombre_comprador).toBe(
      'El nombre debe tener al menos 3 caracteres',
    )
  })

  it('3 caracteres → sin error', () => {
    const errors = validateForm({ ...validBase, nombre_comprador: 'Ana' })
    expect(errors.nombre_comprador).toBeUndefined()
  })
})

// ---------------------------------------------------------------------------
// email_comprador validation
// ---------------------------------------------------------------------------

describe('validateForm — email_comprador', () => {
  it('vacío → error "El email es obligatorio"', () => {
    const errors = validateForm({ ...validBase, email_comprador: '' })
    expect(errors.email_comprador).toBe('El email es obligatorio')
  })

  it('"notanemail" → error "Ingresá un email válido"', () => {
    const errors = validateForm({ ...validBase, email_comprador: 'notanemail' })
    expect(errors.email_comprador).toBe('Ingresá un email válido')
  })

  it('"user@domain.com" → sin error', () => {
    const errors = validateForm({
      ...validBase,
      email_comprador: 'user@domain.com',
    })
    expect(errors.email_comprador).toBeUndefined()
  })
})
