import { useState, useId } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/shared/api/axios'
import { useAuthStore } from '@/store/authStore'
import { useUIStore } from '@/store/uiStore'

interface RegisterResponse {
  access_token: string
  refresh_token: string
  token_type: string
  usuario: { id: number; email: string; nombre: string }
}

function rolesFromToken(token: string): string[] {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return Array.isArray(payload.roles) ? payload.roles : []
  } catch {
    return []
  }
}

async function registerUser(nombre: string, email: string, password: string): Promise<RegisterResponse> {
  const { data } = await apiClient.post<RegisterResponse>('/api/v1/auth/register', { nombre, email, password })
  return data
}

export default function Register() {
  const navigate = useNavigate()

  const [nombre, setNombre]     = useState('')
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [showPwd, setShowPwd]   = useState(false)

  const nombreId   = useId()
  const emailId    = useId()
  const passwordId = useId()
  const errorId    = useId()

  const updateTokens = useAuthStore((s) => s.updateTokens)
  const setUser      = useAuthStore((s) => s.setUser)
  const addToast     = useUIStore((s) => s.addToast)

  const { mutate, isPending, isError, error } = useMutation({
    mutationFn: () => registerUser(nombre, email, password),
    onSuccess: (data) => {
      updateTokens(data.access_token, data.refresh_token)
      setUser({
        id: String(data.usuario.id),
        email: data.usuario.email,
        name: data.usuario.nombre,
        roles: rolesFromToken(data.access_token),
      })
      addToast({ message: '¡Cuenta creada! Bienvenido/a.', type: 'success' })
      navigate('/', { replace: true })
    },
    onError: () => {
      addToast({ message: 'No se pudo crear la cuenta. Verificá los datos.', type: 'error' })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!nombre || !email || !password) return
    mutate()
  }

  const axiosError = error as { response?: { data?: { detail?: string } } } | null
  const detail = axiosError?.response?.data?.detail

  return (
    <main className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <div className="bg-card border border-border rounded-xl shadow-sm p-8">
          <h1 className="text-2xl font-bold text-foreground mb-2">Crear cuenta</h1>
          <p className="text-sm text-muted-foreground mb-6">
            ¿Ya tenés cuenta?{' '}
            <Link to="/login" className="text-primary underline underline-offset-4 hover:text-primary/80">
              Iniciá sesión
            </Link>
          </p>

          <form onSubmit={handleSubmit} noValidate aria-describedby={isError ? errorId : undefined}>
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label htmlFor={nombreId} className="text-sm font-medium text-foreground">
                  Nombre
                </label>
                <input
                  id={nombreId}
                  type="text"
                  autoComplete="name"
                  required
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  disabled={isPending}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
                  placeholder="Tu nombre"
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor={emailId} className="text-sm font-medium text-foreground">
                  Email
                </label>
                <input
                  id={emailId}
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={isPending}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
                  placeholder="vos@ejemplo.com"
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor={passwordId} className="text-sm font-medium text-foreground">
                  Contraseña
                </label>
                <div className="relative">
                  <input
                    id={passwordId}
                    type={showPwd ? 'text' : 'password'}
                    autoComplete="new-password"
                    required
                    minLength={8}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={isPending}
                    className="w-full px-3 py-2 pr-10 rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
                    placeholder="Mínimo 8 caracteres"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPwd((v) => !v)}
                    aria-pressed={showPwd}
                    aria-label={showPwd ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                    className="absolute inset-y-0 right-0 px-3 flex items-center text-muted-foreground hover:text-foreground"
                  >
                    {showPwd ? '🙈' : '👁'}
                  </button>
                </div>
              </div>

              {isError && (
                <p id={errorId} role="alert" className="text-sm text-destructive">
                  {typeof detail === 'string' ? detail : 'No se pudo crear la cuenta. Verificá los datos.'}
                </p>
              )}

              <button
                type="submit"
                disabled={isPending || !nombre || !email || !password}
                aria-busy={isPending}
                className="w-full py-2.5 px-4 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isPending ? 'Creando cuenta...' : 'Crear cuenta'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  )
}
