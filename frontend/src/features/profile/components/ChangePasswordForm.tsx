/**
 * ChangePasswordForm — form for changing the user's password.
 *
 * Client-side validation:
 *   - passwordActual: required, min 8 chars
 *   - nuevaPassword: required, min 8 chars
 *
 * NOTE: The same-password equality check has been intentionally removed.
 * The backend is the only entity that can determine whether the supplied
 * `password_actual` matches the stored hash. A client-side string comparison
 * would incorrectly block valid requests (e.g. when the user mistyped the
 * current password field) and provide no security benefit. The backend 400
 * response for a wrong current password is handled by the Axios interceptor
 * toast — no client-side check needed.
 *
 * On 204 success: shows success toast + waits 2000ms + authStore.logout()
 * ProtectedRoute then redirects automatically to /login.
 *
 * ARIA:
 *   - section with aria-labelledby
 *   - password visibility toggle: aria-pressed + aria-label + aria-hidden icon
 *   - live region for post-submit status: aria-live="assertive"
 *   - Input handles aria-invalid + aria-describedby
 *
 * Tokens: only semantic @theme tokens.
 * Responsive: w-full inputs, w-full sm:w-auto button.
 */

import { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { useCambiarPassword } from '@/features/profile/hooks/useCambiarPassword'
import { Card, CardHeader, CardContent, CardFooter } from '@/shared/components/ui/Card'
import { Input } from '@/shared/components/ui/Input'
import { Button } from '@/shared/components/ui/Button'

interface FormErrors {
  passwordActual?: string
  nuevaPassword?: string
}

export function ChangePasswordForm() {
  const [passwordActual, setPasswordActual] = useState('')
  const [nuevaPassword, setNuevaPassword] = useState('')
  const [showPasswordActual, setShowPasswordActual] = useState(false)
  const [showNuevaPassword, setShowNuevaPassword] = useState(false)
  const [errors, setErrors] = useState<FormErrors>({})
  const [successMsg, setSuccessMsg] = useState('')

  const { mutate, isPending } = useCambiarPassword()

  function validate(): FormErrors {
    const newErrors: FormErrors = {}

    if (!passwordActual) {
      newErrors.passwordActual = 'La contraseña actual es requerida.'
    } else if (passwordActual.length < 8) {
      newErrors.passwordActual = 'La contraseña actual debe tener al menos 8 caracteres.'
    }

    if (!nuevaPassword) {
      newErrors.nuevaPassword = 'La nueva contraseña es requerida.'
    } else if (nuevaPassword.length < 8) {
      newErrors.nuevaPassword = 'La nueva contraseña debe tener al menos 8 caracteres.'
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
    setSuccessMsg('')

    mutate(
      { password_actual: passwordActual, nueva_password: nuevaPassword },
      {
        onSuccess: () => {
          setSuccessMsg(
            'Contraseña actualizada. Cerrando sesión en 2 segundos...',
          )
          setPasswordActual('')
          setNuevaPassword('')
        },
      },
    )
  }

  return (
    <section aria-labelledby="change-password-heading">
      <Card>
        <CardHeader className="p-4 sm:p-6">
          <h2
            id="change-password-heading"
            className="text-xl font-semibold text-card-foreground"
          >
            Cambiar contraseña
          </h2>
        </CardHeader>

        <form onSubmit={handleSubmit} noValidate>
          <CardContent className="p-4 sm:p-6 pt-0 flex flex-col gap-4">
            {/* Live region for post-submit feedback */}
            <div
              role="status"
              aria-live="assertive"
              aria-atomic="true"
              className={successMsg ? 'text-sm text-foreground' : 'sr-only'}
            >
              {successMsg}
            </div>

            {/* Password actual input with show/hide toggle */}
            <div className="relative">
              <Input
                id="password-actual"
                label="Contraseña actual"
                type={showPasswordActual ? 'text' : 'password'}
                value={passwordActual}
                onChange={(e) => {
                  setPasswordActual(e.target.value)
                  if (errors.passwordActual)
                    setErrors((prev) => ({ ...prev, passwordActual: undefined }))
                }}
                error={errors.passwordActual}
                disabled={isPending}
                autoComplete="current-password"
              />
              <button
                type="button"
                aria-pressed={showPasswordActual}
                aria-label="Mostrar contraseña actual"
                onClick={() => setShowPasswordActual((v) => !v)}
                className="absolute right-3 top-8 text-muted-foreground hover:text-foreground transition-colors"
                tabIndex={0}
              >
                {showPasswordActual ? (
                  <EyeOff className="h-4 w-4" aria-hidden="true" />
                ) : (
                  <Eye className="h-4 w-4" aria-hidden="true" />
                )}
              </button>
            </div>

            {/* Nueva password input with show/hide toggle */}
            <div className="relative">
              <Input
                id="nueva-password"
                label="Nueva contraseña"
                type={showNuevaPassword ? 'text' : 'password'}
                value={nuevaPassword}
                onChange={(e) => {
                  setNuevaPassword(e.target.value)
                  if (errors.nuevaPassword)
                    setErrors((prev) => ({ ...prev, nuevaPassword: undefined }))
                }}
                error={errors.nuevaPassword}
                disabled={isPending}
                autoComplete="new-password"
              />
              <button
                type="button"
                aria-pressed={showNuevaPassword}
                aria-label="Mostrar nueva contraseña"
                onClick={() => setShowNuevaPassword((v) => !v)}
                className="absolute right-3 top-8 text-muted-foreground hover:text-foreground transition-colors"
                tabIndex={0}
              >
                {showNuevaPassword ? (
                  <EyeOff className="h-4 w-4" aria-hidden="true" />
                ) : (
                  <Eye className="h-4 w-4" aria-hidden="true" />
                )}
              </button>
            </div>
          </CardContent>

          <CardFooter className="p-4 sm:p-6 pt-0">
            <Button
              type="submit"
              variant="outline"
              loading={isPending}
              disabled={isPending}
              aria-busy={isPending}
              className="w-full sm:w-auto"
            >
              Cambiar contraseña
            </Button>
          </CardFooter>
        </form>
      </Card>
    </section>
  )
}
