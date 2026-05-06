import React, { ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
}

/**
 * Global Error Boundary component
 * Catches React component rendering errors and displays fallback UI
 * Does NOT catch: event handler errors, async errors, SSR errors
 */
export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(_error: Error): Partial<State> {
    return { hasError: true }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    this.setState({
      error: error || null,
      errorInfo,
    })
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      const isDevelopment = import.meta.env.MODE === 'development'

      return (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            backgroundColor: '#f3f4f6',
            padding: '2rem',
            fontFamily: 'system-ui, sans-serif',
          }}
        >
          <div
            style={{
              maxWidth: '600px',
              backgroundColor: '#fff',
              padding: '2rem',
              borderRadius: '0.5rem',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            }}
          >
            <h1 style={{ color: '#dc2626', marginBottom: '1rem' }}>
              ¡Algo salió mal!
            </h1>

            {isDevelopment ? (
              <>
                <h2 style={{ fontSize: '1.125rem', marginTop: '1rem' }}>
                  {this.state.error?.toString()}
                </h2>
                <pre
                  style={{
                    backgroundColor: '#f9fafb',
                    padding: '1rem',
                    borderRadius: '0.375rem',
                    overflow: 'auto',
                    fontSize: '0.875rem',
                    marginTop: '1rem',
                    marginBottom: '1rem',
                  }}
                >
                  {this.state.errorInfo?.componentStack}
                </pre>
              </>
            ) : (
              <p style={{ color: '#6b7280', marginBottom: '1rem' }}>
                Lo sentimos, ocurrió un error inesperado. Por favor, intenta
                recargar la página.
              </p>
            )}

            <button
              onClick={this.handleReload}
              style={{
                backgroundColor: '#3b82f6',
                color: '#fff',
                padding: '0.75rem 1.5rem',
                borderRadius: '0.375rem',
                border: 'none',
                cursor: 'pointer',
                fontSize: '1rem',
              }}
            >
              Recargar Página
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
