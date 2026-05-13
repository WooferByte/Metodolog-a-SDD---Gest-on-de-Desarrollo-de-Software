/**
 * EditProfileForm — form for editing nombre and telefono.
 *
 * Client-side validation before mutation:
 *   - At least one field must be changed (dirty check)
 *   - nombre: 1–100 chars if provided
 *   - telefono: max 20 chars if provided
 *
 * ARIA:
 *   - section with aria-labelledby
 *   - Input component handles aria-invalid + aria-describedby + role="alert"
 *   - Button has aria-busy during isPending
 *
 * Tokens: only semantic @theme tokens — no raw Tailwind colors.
 * Responsive: inputs w-full, button w-full sm:w-auto, card p-4 sm:p-6.
 */

import { useState, useEffect } from 'react'
import { useUpdatePerfil } from '@/features/profile/hooks/useUpdatePerfil'
import { Card, CardHeader, CardContent, CardFooter } from '@/shared/components/ui/Card'
import { Input } from '@/shared/components/ui/Input'
import { Button } from '@/shared/components/ui/Button'
import type { PerfilData } from '@/features/profile/types/profile'

interface EditProfileFormProps {
  perfil: PerfilData | undefined
  isLoading: boolean
}

interface FormErrors {
  nombre?: string
  telefono?: string
  form?: string
}

export function EditProfileForm({ perfil, isLoading }: EditProfileFormProps) {
  const [nombre, setNombre] = useState('')
  const [telefono, setTelefono] = useState('')
  const [errors, setErrors] = useState<FormErrors>({})

  const { mutate, isPending } = useUpdatePerfil()

  // Pre-populate form when perfil data becomes available
  // ONLY when perfil changes — not on every render
  useEffect(() => {
    if (perfil) {
      setNombre(perfil.nombre)
      setTelefono(perfil.telefono ?? '')
    }
  }, [perfil])

  function validate(): FormErrors {
    const newErrors: FormErrors = {}

    // Dirty check — at least one field must differ from current perfil
    const isDirty =
      nombre !== (perfil?.nombre ?? '') ||
      telefono !== (perfil?.telefono ?? '')

    if (!isDirty) {
      newErrors.form = 'Modificá al menos un campo antes de guardar.'
    }

    // Nombre validation (if provided)
    if (nombre.trim().length > 0 && nombre.trim().length > 100) {
      newErrors.nombre = 'El nombre no puede superar los 100 caracteres.'
    }
    if (nombre.trim().length === 0 && nombre !== (perfil?.nombre ?? '')) {
      // Only error if user explicitly cleared a pre-filled nombre
      // (backend requires min_length=1 if provided)
      if (nombre.trim() === '' && perfil?.nombre) {
        newErrors.nombre = 'El nombre no puede estar vacío.'
      }
    }

    // Teléfono validation (optional — max 20 chars)
    if (telefono.length > 20) {
      newErrors.telefono = 'El teléfono no puede superar los 20 caracteres.'
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

    const payload: { nombre?: string; telefono?: string } = {}
    if (nombre !== (perfil?.nombre ?? '')) payload.nombre = nombre
    if (telefono !== (perfil?.telefono ?? '')) payload.telefono = telefono

    mutate(payload)
  }

  const isDisabled = isLoading || isPending

  return (
    <section aria-labelledby="edit-profile-heading">
      <Card>
        <CardHeader className="p-4 sm:p-6">
          <h2
            id="edit-profile-heading"
            className="text-xl font-semibold text-card-foreground"
          >
            Editar perfil
          </h2>
        </CardHeader>

        <form onSubmit={handleSubmit} noValidate>
          <CardContent className="p-4 sm:p-6 pt-0 flex flex-col gap-4">
            {/* Form-level error */}
            {errors.form && (
              <div role="alert" aria-live="polite" className="text-sm text-destructive">
                {errors.form}
              </div>
            )}

            <Input
              id="edit-nombre"
              label="Nombre"
              type="text"
              value={nombre}
              onChange={(e) => {
                setNombre(e.target.value)
                if (errors.nombre) setErrors((prev) => ({ ...prev, nombre: undefined }))
              }}
              error={errors.nombre}
              disabled={isDisabled}
              maxLength={100}
              placeholder="Tu nombre"
              autoComplete="name"
            />

            <Input
              id="edit-telefono"
              label="Teléfono"
              type="tel"
              value={telefono}
              onChange={(e) => {
                setTelefono(e.target.value)
                if (errors.telefono) setErrors((prev) => ({ ...prev, telefono: undefined }))
              }}
              error={errors.telefono}
              disabled={isDisabled}
              maxLength={20}
              placeholder="Ej: 011-1234-5678"
              autoComplete="tel"
            />
          </CardContent>

          <CardFooter className="p-4 sm:p-6 pt-0">
            <Button
              type="submit"
              variant="primary"
              loading={isPending}
              disabled={isDisabled}
              aria-busy={isPending}
              className="w-full sm:w-auto"
            >
              Guardar cambios
            </Button>
          </CardFooter>
        </form>
      </Card>
    </section>
  )
}
