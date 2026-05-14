/**
 * MyAddressesPage — page for managing the authenticated user's addresses.
 *
 * Route: /direcciones (CLIENT or ADMIN)
 *
 * States:
 *   Loading → 3 skeleton cards
 *   Empty   → empty state message + "Agregar tu primera dirección" button
 *   Filled  → responsive grid of AddressCards
 *   Error   → handled by Axios interceptor toast; no extra UI needed
 *
 * Modal state (local — not server state, not Zustand):
 *   modalOpen       — controls the AddressForm modal
 *   editingAddress  — null for create mode, DireccionResponse for edit mode
 *   deleteTarget    — null or DireccionResponse to delete (controls DeleteAddressDialog)
 *
 * Tokens: only semantic @theme tokens — no raw Tailwind colors.
 * Responsive: grid 1-col on mobile, 2-col on md+.
 */

import { useState } from 'react'
import { Modal } from '@/shared/components/ui/Modal'
import { Button } from '@/shared/components/ui/Button'
import { Skeleton } from '@/shared/components/ui/Skeleton'
import { AddressCard } from '@/features/addresses/components/AddressCard'
import { AddressForm } from '@/features/addresses/components/AddressForm'
import { DeleteAddressDialog } from '@/features/addresses/components/DeleteAddressDialog'
import { useAddresses } from '@/features/addresses/hooks/useAddresses'
import { useCreateAddress } from '@/features/addresses/hooks/useCreateAddress'
import { useUpdateAddress } from '@/features/addresses/hooks/useUpdateAddress'
import { useSetPredeterminada } from '@/features/addresses/hooks/useSetPredeterminada'
import { useDeleteAddress } from '@/features/addresses/hooks/useDeleteAddress'
import type { DireccionCreate, DireccionResponse } from '@/features/addresses/types'

export default function MyAddressesPage() {
  const { data: addresses, isLoading } = useAddresses()
  const createAddress = useCreateAddress()
  const updateAddress = useUpdateAddress()
  const setPredeterminada = useSetPredeterminada()
  const deleteAddress = useDeleteAddress()

  // Modal state — local UI state, not persisted
  const [modalOpen, setModalOpen] = useState(false)
  const [editingAddress, setEditingAddress] = useState<DireccionResponse | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<DireccionResponse | null>(null)

  function openCreateModal() {
    setEditingAddress(null)
    setModalOpen(true)
  }

  function openEditModal(address: DireccionResponse) {
    setEditingAddress(address)
    setModalOpen(true)
  }

  function closeModal() {
    setModalOpen(false)
    setEditingAddress(null)
  }

  function handleFormSubmit(data: DireccionCreate) {
    if (editingAddress) {
      updateAddress.mutate(
        { id: editingAddress.id, data },
        { onSuccess: closeModal },
      )
    } else {
      createAddress.mutate(data, { onSuccess: closeModal })
    }
  }

  function openDeleteDialog(address: DireccionResponse) {
    setDeleteTarget(address)
  }

  function closeDeleteDialog() {
    setDeleteTarget(null)
  }

  function handleConfirmDelete() {
    if (!deleteTarget) return
    deleteAddress.mutate({ id: deleteTarget.id }, { onSuccess: closeDeleteDialog })
  }

  const isFormPending = createAddress.isPending || updateAddress.isPending
  const isDeletePending = deleteAddress.isPending

  const modalTitle = editingAddress ? 'Editar Dirección' : 'Nueva Dirección'

  return (
    <main className="container mx-auto max-w-4xl px-4 py-8">
      {/* ── Page header ─────────────────────────────────────── */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-foreground">Mis Direcciones</h1>

        <Button
          variant="primary"
          size="md"
          onClick={openCreateModal}
          aria-label="Agregar dirección"
        >
          Agregar dirección
        </Button>
      </div>

      {/* ── Loading state: skeleton cards ───────────────────── */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4" aria-busy="true" aria-label="Cargando direcciones">
          {[1, 2, 3].map((i) => (
            <div key={i} className="rounded-xl border border-border bg-card p-4 flex flex-col gap-3">
              <Skeleton variant="text" className="h-5 w-1/2" />
              <Skeleton variant="text" className="h-4 w-3/4" />
              <Skeleton variant="text" className="h-4 w-1/2" />
              <div className="flex gap-2 mt-2">
                <Skeleton variant="text" className="h-8 w-16" />
                <Skeleton variant="text" className="h-8 w-20" />
                <Skeleton variant="text" className="h-8 w-16" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Empty state ─────────────────────────────────────── */}
      {!isLoading && addresses?.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
          <p className="text-muted-foreground text-base">
            No tenés direcciones guardadas.
          </p>
          <Button variant="primary" size="md" onClick={openCreateModal}>
            Agregar tu primera dirección
          </Button>
        </div>
      )}

      {/* ── Address grid ─────────────────────────────────────── */}
      {!isLoading && addresses && addresses.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {addresses.map((address) => (
            <AddressCard
              key={address.id}
              address={address}
              onEdit={() => openEditModal(address)}
              onDelete={() => openDeleteDialog(address)}
              onSetPredeterminada={() => setPredeterminada.mutate({ id: address.id })}
              isPending={setPredeterminada.isPending}
            />
          ))}
        </div>
      )}

      {/* ── AddressForm modal ────────────────────────────────── */}
      <Modal
        isOpen={modalOpen}
        onClose={closeModal}
        title={modalTitle}
        className="max-w-md"
      >
        <AddressForm
          initialData={editingAddress ?? undefined}
          onSubmit={handleFormSubmit}
          onCancel={closeModal}
          isLoading={isFormPending}
        />
      </Modal>

      {/* ── Delete confirmation dialog ───────────────────────── */}
      {deleteTarget && (
        <DeleteAddressDialog
          isOpen={!!deleteTarget}
          alias={deleteTarget.alias}
          onCancel={closeDeleteDialog}
          onConfirm={handleConfirmDelete}
          isPending={isDeletePending}
        />
      )}
    </main>
  )
}
