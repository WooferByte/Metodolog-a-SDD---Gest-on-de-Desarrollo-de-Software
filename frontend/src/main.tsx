import React from 'react'
import ReactDOM from 'react-dom/client'
import App from '@/app/App'
import '@/index.css'

// Expose dev helpers on window for manual testing in browser console
if (import.meta.env.DEV) {
  import('@/shared/api/axios').then(({ apiClient }) => {
    ;(window as Window & { __apiClient?: typeof apiClient }).__apiClient = apiClient
  })
  import('@/store/uiStore').then(({ useUIStore }) => {
    ;(window as Window & { __uiStore?: typeof useUIStore }).__uiStore = useUIStore
  })
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
