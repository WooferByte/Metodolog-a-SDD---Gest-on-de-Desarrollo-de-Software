/**
 * Payment method options for the PaymentMethodSelector component.
 *
 * MVP configuration:
 *   - MercadoPago: enabled (integrated)
 *   - Tarjeta: disabled (future)
 *   - Efectivo: disabled (future)
 */

import type { PaymentMethodOption } from '../types/payment.types'

export const PAYMENT_METHODS: PaymentMethodOption[] = [
  {
    id: 'mercadopago',
    label: 'MercadoPago',
    description: 'Pagá con tarjeta, débito, Mercado Crédito o saldo en tu cuenta',
    icon: '💳',
    enabled: true,
  },
  {
    id: 'card',
    label: 'Tarjeta de crédito/débito',
    description: 'Próximamente disponible',
    icon: '🏦',
    enabled: false,
  },
  {
    id: 'cash',
    label: 'Efectivo',
    description: 'Próximamente disponible',
    icon: '💵',
    enabled: false,
  },
]
