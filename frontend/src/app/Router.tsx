import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { ProtectedRoute } from '@/shared/routing/ProtectedRoute'
import { Spinner } from '@/shared/components/ui/Spinner'

// Lazy-loaded pages — each becomes a separate chunk (code splitting)
const Catalog       = lazy(() => import('@/pages/Catalog'))
const Login         = lazy(() => import('@/pages/Login'))
const Register      = lazy(() => import('@/pages/Register'))
const NotFound      = lazy(() => import('@/pages/NotFound'))
const ForbiddenPage = lazy(() => import('@/pages/ForbiddenPage'))
const Profile       = lazy(() => import('@/pages/Profile'))
const Orders        = lazy(() => import('@/pages/Orders'))
const Admin         = lazy(() => import('@/pages/Admin'))

/**
 * Router — defines all application routes.
 *
 * Route access control:
 *   Public:  /  /catalog  /login  /register
 *   CLIENT:  /cart  /orders  /profile  /addresses  (CLIENT or ADMIN)
 *   STOCK:   /admin/productos  /admin/categorias  /admin/ingredientes  (STOCK or ADMIN)
 *   PEDIDOS: /admin/pedidos  (PEDIDOS or ADMIN)
 *   ADMIN:   /admin/usuarios  /admin/metricas  /admin/configuracion  (ADMIN only)
 */
export default function Router() {
  return (
    <Suspense fallback={<Spinner />}>
      <Routes>
        {/* ── Public routes ─────────────────────────────────── */}
        <Route path="/" element={<Catalog />} />
        <Route path="/catalog" element={<Catalog />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* ── Error pages ───────────────────────────────────── */}
        <Route path="/403" element={<ForbiddenPage />} />
        <Route path="/404" element={<NotFound />} />

        {/* ── CLIENT routes: require CLIENT or ADMIN ────────── */}
        <Route element={<ProtectedRoute requiredRoles={['CLIENT', 'ADMIN']} />}>
          <Route path="/profile" element={<Profile />} />
          <Route path="/orders" element={<Orders />} />
          {/* /cart and /addresses — placeholder until dedicated pages exist */}
          <Route path="/cart" element={<Admin />} />
          <Route path="/addresses" element={<Admin />} />
        </Route>

        {/* ── STOCK routes: require STOCK or ADMIN ──────────── */}
        <Route element={<ProtectedRoute requiredRoles={['STOCK', 'ADMIN']} />}>
          <Route path="/admin/productos" element={<Admin />} />
          <Route path="/admin/categorias" element={<Admin />} />
          <Route path="/admin/ingredientes" element={<Admin />} />
        </Route>

        {/* ── PEDIDOS routes: require PEDIDOS or ADMIN ──────── */}
        <Route element={<ProtectedRoute requiredRoles={['PEDIDOS', 'ADMIN']} />}>
          <Route path="/admin/pedidos" element={<Admin />} />
        </Route>

        {/* ── ADMIN-only routes ─────────────────────────────── */}
        <Route element={<ProtectedRoute requiredRoles={['ADMIN']} />}>
          <Route path="/admin/usuarios" element={<Admin />} />
          <Route path="/admin/metricas" element={<Admin />} />
          <Route path="/admin/configuracion" element={<Admin />} />
          {/* General admin dashboard */}
          <Route path="/admin" element={<Admin />} />
        </Route>

        {/* ── Catch-all ─────────────────────────────────────── */}
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Routes>
    </Suspense>
  )
}
