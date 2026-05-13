/**
 * ProfileInfo — read-only profile information card.
 *
 * Shows: email (from authStore), nombre, telefono, roles (badges), creado_en.
 * While loading: renders Skeleton placeholders with aria-busy="true" (no layout shift).
 *
 * ARIA: section with aria-labelledby, h2 as section heading.
 * Tokens: only semantic tokens from @theme — no raw Tailwind colors.
 */

import { useAuthStore } from '@/store/authStore'
import { Card, CardHeader, CardContent } from '@/shared/components/ui/Card'
import { Badge } from '@/shared/components/ui/Badge'
import { Skeleton } from '@/shared/components/ui/Skeleton'
import type { PerfilData } from '@/features/profile/types/profile'

interface ProfileInfoProps {
  perfil: PerfilData | undefined
  isLoading: boolean
}

function getBadgeVariant(role: string): 'success' | 'info' | 'warning' | 'default' {
  switch (role) {
    case 'CLIENT':  return 'success'
    case 'ADMIN':   return 'info'
    case 'STOCK':   return 'warning'
    case 'PEDIDOS': return 'warning'
    default:        return 'default'
  }
}

function formatDate(isoString: string): string {
  return new Intl.DateTimeFormat('es-AR', { dateStyle: 'long' }).format(
    new Date(isoString),
  )
}

export function ProfileInfo({ perfil, isLoading }: ProfileInfoProps) {
  // Email from authStore — already available client-side, no duplication needed
  const email = useAuthStore((s) => s.user?.email)

  return (
    <section aria-labelledby="profile-info-heading">
      <Card>
        <CardHeader>
          <h2
            id="profile-info-heading"
            className="text-xl font-semibold text-card-foreground"
          >
            Información de cuenta
          </h2>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div
              aria-busy="true"
              aria-label="Cargando perfil"
              className="flex flex-col gap-3"
            >
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-5 w-24" />
              <Skeleton className="h-4 w-36" />
            </div>
          ) : (
            <dl className="flex flex-col gap-4 text-sm">
              {/* Email — from authStore (static, no duplication of server state) */}
              <div className="flex flex-col gap-0.5">
                <dt className="text-muted-foreground font-medium">Email</dt>
                <dd className="text-foreground">{email ?? '—'}</dd>
              </div>

              {/* Nombre */}
              <div className="flex flex-col gap-0.5">
                <dt className="text-muted-foreground font-medium">Nombre</dt>
                <dd className="text-foreground">{perfil?.nombre ?? '—'}</dd>
              </div>

              {/* Teléfono */}
              <div className="flex flex-col gap-0.5">
                <dt className="text-muted-foreground font-medium">Teléfono</dt>
                <dd className="text-foreground">
                  {perfil?.telefono ?? 'No especificado'}
                </dd>
              </div>

              {/* Roles */}
              <div className="flex flex-col gap-1.5">
                <dt className="text-muted-foreground font-medium">Roles</dt>
                <dd>
                  <ul aria-label="Roles" className="flex flex-wrap gap-2 list-none p-0 m-0">
                    {perfil?.roles.map((role) => (
                      <li key={role}>
                        <Badge variant={getBadgeVariant(role)}>{role}</Badge>
                      </li>
                    )) ?? (
                      <li>
                        <span className="text-muted-foreground">—</span>
                      </li>
                    )}
                  </ul>
                </dd>
              </div>

              {/* Miembro desde */}
              <div className="flex flex-col gap-0.5">
                <dt className="text-muted-foreground font-medium">Miembro desde</dt>
                <dd className="text-foreground">
                  {perfil?.creado_en ? formatDate(perfil.creado_en) : '—'}
                </dd>
              </div>
            </dl>
          )}
        </CardContent>
      </Card>
    </section>
  )
}
