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
 *
 * In development mode: shows full stack trace for debugging
 * In production mode: shows a friendly generic message only
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
        <div className="flex min-h-screen flex-col items-center justify-center bg-gray-100 p-8">
          <div className="w-full max-w-xl rounded-lg bg-white p-8 shadow-sm">
            <h1 className="mb-4 text-2xl font-bold text-red-600">
              ¡Algo salió mal!
            </h1>

            {isDevelopment ? (
              <>
                <h2 className="mt-4 text-lg font-semibold text-gray-800">
                  {this.state.error?.toString()}
                </h2>
                <pre className="mt-4 mb-4 overflow-auto rounded-md bg-gray-50 p-4 text-sm text-gray-700">
                  {this.state.errorInfo?.componentStack}
                </pre>
              </>
            ) : (
              <p className="mb-4 text-gray-500">
                Lo sentimos, ocurrió un error inesperado. Por favor, intenta
                recargar la página.
              </p>
            )}

            <div className="flex flex-wrap gap-3">
              <button
                onClick={this.handleReload}
                className="rounded-md bg-blue-500 px-6 py-3 text-base font-medium text-white transition-colors hover:bg-blue-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
              >
                Recargar Página
              </button>
              <a
                href="/"
                className="rounded-md border border-gray-300 bg-white px-6 py-3 text-base font-medium text-gray-700 transition-colors hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 focus-visible:ring-offset-2"
              >
                Ir al inicio
              </a>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
