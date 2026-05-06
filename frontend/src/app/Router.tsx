import { Routes, Route, Navigate } from 'react-router-dom'
import { withAuth } from '@/shared/routing/withAuth'

// Page imports
import Catalog from '@/pages/Catalog'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import Profile from '@/pages/Profile'
import Orders from '@/pages/Orders'
import Admin from '@/pages/Admin'
import NotFound from '@/pages/NotFound'

// Protected routes
const ProtectedProfile = withAuth(Profile)
const ProtectedOrders = withAuth(Orders)
const ProtectedAdmin = withAuth(Admin, ['ADMIN'])

/**
 * Router component - defines all routes for the application
 * Public routes: /, /login, /register
 * Private routes: /profile, /orders (CLIENT+), /admin/* (ADMIN only)
 */
export default function Router() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Catalog />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Protected routes */}
      <Route path="/profile" element={<ProtectedProfile />} />
      <Route path="/orders" element={<ProtectedOrders />} />
      <Route path="/admin/*" element={<ProtectedAdmin />} />

      {/* Fallback routes */}
      <Route path="/404" element={<NotFound />} />
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  )
}
