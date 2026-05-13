/**
 * Profile page — Mi Perfil.
 *
 * Composites three feature components:
 *   - ProfileInfo: read-only account info card
 *   - EditProfileForm: edit nombre + telefono
 *   - ChangePasswordForm: change password
 *
 * Layout:
 *   - Mobile: single column (grid-cols-1)
 *   - Desktop (lg): two columns — info left, forms right (lg:grid-cols-2)
 *
 * React.lazy import: already configured in Router.tsx — do NOT modify Router.tsx.
 * usePerfil() is called here and data passed as props to children.
 *
 * Tokens: only semantic @theme tokens.
 */

import { usePerfil } from '@/features/profile/hooks/usePerfil'
import { ProfileInfo } from '@/features/profile/components/ProfileInfo'
import { EditProfileForm } from '@/features/profile/components/EditProfileForm'
import { ChangePasswordForm } from '@/features/profile/components/ChangePasswordForm'

export default function Profile() {
  const { data, isLoading } = usePerfil()

  return (
    <main className="p-4 sm:p-6 lg:p-8" aria-label="Mi Perfil">
      <h1 className="text-2xl font-bold text-foreground mb-6">Mi Perfil</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left column: read-only info */}
        <ProfileInfo perfil={data} isLoading={isLoading} />

        {/* Right column: edit forms stacked vertically */}
        <div className="flex flex-col gap-6">
          <EditProfileForm perfil={data} isLoading={isLoading} />
          <ChangePasswordForm />
        </div>
      </div>
    </main>
  )
}
