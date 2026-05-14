/**
 * AddressForm — dual-mode form for creating and editing addresses.
 *
 * Modes:
 *   Create (initialData undefined): empty fields, title "Nueva Dirección", submit "Guardar"
 *   Edit   (initialData provided):  pre-populated fields, title "Editar Dirección", submit "Actualizar"
 *
 * Client-side validation:
 *   - alias: required, max 100 chars
 *   - linea1: required, max 200 chars
 *   - ciudad: required, max 100 chars
 *   - codigo_postal: required, 4–20 chars
 *   - piso, departamento, referencia: optional
 *
 * ARIA: aria-invalid on inputs with error, aria-describedby pointing to error message.
 * Tokens: only semantic @theme tokens — no raw Tailwind colors.
 */

import { useState, useEffect } from 'react'
import { Input } from '@/shared/components/ui/Input'
import { Button } from '@/shared/components/ui/Button'
import type { AddressFormData, DireccionCreate, DireccionResponse } from '@/features/addresses/types'

export interface AddressFormProps {
  initialData?: DireccionResponse
  onSubmit: (data: DireccionCreate) => void
  onCancel: () => void
  isLoading?: boolean
}

const EMPTY_FORM: AddressFormData = {
  alias: '',
  linea1: '',
  ciudad: '',
  codigo_postal: '',
  piso: '',
  departamento: '',
  referencia: '',
}

interface FormErrors {
  alias?: string
  linea1?: string
  ciudad?: string
  codigo_postal?: string
  piso?: string
  departamento?: string
  referencia?: string
}

export function AddressForm({
  initialData,
  onSubmit,
  onCancel,
  isLoading = false,
}: AddressFormProps) {
  const [form, setForm] = useState<AddressFormData>(EMPTY_FORM)
  const [errors, setErrors] = useState<FormErrors>({})

  const isEditMode = !!initialData

  // Pre-populate form when initialData changes (edit mode)
  useEffect(() => {
    if (initialData) {
      setForm({
        alias: initialData.alias,
        linea1: initialData.linea1,
        ciudad: initialData.ciudad,
        codigo_postal: initialData.codigo_postal,
        piso: initialData.piso ?? '',
        departamento: initialData.departamento ?? '',
        referencia: initialData.referencia ?? '',
      })
    } else {
      setForm(EMPTY_FORM)
    }
    setErrors({})
  }, [initialData])

  function setField(field: keyof AddressFormData, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }))
    // Clear field error on change
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }))
    }
  }

  function validate(): FormErrors {
    const newErrors: FormErrors = {}

    if (!form.alias.trim()) {
      newErrors.alias = 'El alias es requerido.'
    } else if (form.alias.trim().length > 100) {
      newErrors.alias = 'El alias no puede superar los 100 caracteres.'
    }

    if (!form.linea1.trim()) {
      newErrors.linea1 = 'La dirección es requerida.'
    } else if (form.linea1.trim().length > 200) {
      newErrors.linea1 = 'La dirección no puede superar los 200 caracteres.'
    }

    if (!form.ciudad.trim()) {
      newErrors.ciudad = 'La ciudad es requerida.'
    } else if (form.ciudad.trim().length > 100) {
      newErrors.ciudad = 'La ciudad no puede superar los 100 caracteres.'
    }

    if (!form.codigo_postal.trim()) {
      newErrors.codigo_postal = 'El código postal es requerido.'
    } else if (form.codigo_postal.trim().length < 4 || form.codigo_postal.trim().length > 20) {
      newErrors.codigo_postal = 'El código postal debe tener entre 4 y 20 caracteres.'
    }

    if (form.piso.length > 10) {
      newErrors.piso = 'El piso no puede superar los 10 caracteres.'
    }

    if (form.departamento.length > 10) {
      newErrors.departamento = 'El departamento no puede superar los 10 caracteres.'
    }

    if (form.referencia.length > 255) {
      newErrors.referencia = 'La referencia no puede superar los 255 caracteres.'
    }

    return newErrors
  }

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const newErrors = validate()
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }
    setErrors({})

    const payload: DireccionCreate = {
      alias: form.alias.trim(),
      linea1: form.linea1.trim(),
      ciudad: form.ciudad.trim(),
      codigo_postal: form.codigo_postal.trim(),
    }

    if (form.piso.trim()) payload.piso = form.piso.trim()
    if (form.departamento.trim()) payload.departamento = form.departamento.trim()
    if (form.referencia.trim()) payload.referencia = form.referencia.trim()

    onSubmit(payload)
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
      <Input
        id="address-alias"
        label="Alias *"
        type="text"
        value={form.alias}
        onChange={(e) => setField('alias', e.target.value)}
        error={errors.alias}
        disabled={isLoading}
        maxLength={100}
        placeholder="Ej: Casa, Trabajo"
        autoComplete="off"
      />

      <Input
        id="address-linea1"
        label="Dirección *"
        type="text"
        value={form.linea1}
        onChange={(e) => setField('linea1', e.target.value)}
        error={errors.linea1}
        disabled={isLoading}
        maxLength={200}
        placeholder="Ej: Av. Corrientes 1234"
        autoComplete="street-address"
      />

      <div className="grid grid-cols-2 gap-3">
        <Input
          id="address-piso"
          label="Piso"
          type="text"
          value={form.piso}
          onChange={(e) => setField('piso', e.target.value)}
          error={errors.piso}
          disabled={isLoading}
          maxLength={10}
          placeholder="Ej: 3"
        />

        <Input
          id="address-departamento"
          label="Departamento"
          type="text"
          value={form.departamento}
          onChange={(e) => setField('departamento', e.target.value)}
          error={errors.departamento}
          disabled={isLoading}
          maxLength={10}
          placeholder="Ej: A"
        />
      </div>

      <Input
        id="address-ciudad"
        label="Ciudad *"
        type="text"
        value={form.ciudad}
        onChange={(e) => setField('ciudad', e.target.value)}
        error={errors.ciudad}
        disabled={isLoading}
        maxLength={100}
        placeholder="Ej: Buenos Aires"
        autoComplete="address-level2"
      />

      <Input
        id="address-codigo-postal"
        label="Código Postal *"
        type="text"
        value={form.codigo_postal}
        onChange={(e) => setField('codigo_postal', e.target.value)}
        error={errors.codigo_postal}
        disabled={isLoading}
        maxLength={20}
        placeholder="Ej: 1043"
        autoComplete="postal-code"
      />

      <Input
        id="address-referencia"
        label="Referencia"
        type="text"
        value={form.referencia}
        onChange={(e) => setField('referencia', e.target.value)}
        error={errors.referencia}
        disabled={isLoading}
        maxLength={255}
        placeholder="Ej: Timbre 3B, portón azul"
      />

      <div className="flex justify-end gap-3 pt-2">
        <Button
          type="button"
          variant="outline"
          size="md"
          onClick={onCancel}
          disabled={isLoading}
        >
          Cancelar
        </Button>

        <Button
          type="submit"
          variant="primary"
          size="md"
          loading={isLoading}
          disabled={isLoading}
        >
          {isEditMode ? 'Actualizar' : 'Guardar'}
        </Button>
      </div>
    </form>
  )
}
