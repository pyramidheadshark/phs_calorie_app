import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import ErrorBoundary from '../components/ErrorBoundary.jsx'

// Component that throws on render when prop is set
function Bomb({ shouldThrow }) {
  if (shouldThrow) throw new Error('Test render error')
  return <div>OK</div>
}

// Suppress React's error boundary console noise in tests
beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => {})
})
afterEach(() => {
  console.error.mockRestore()
})

describe('ErrorBoundary', () => {
  it('renders children when no error', () => {
    render(
      <ErrorBoundary>
        <div>Safe content</div>
      </ErrorBoundary>
    )
    expect(screen.getByText('Safe content')).toBeInTheDocument()
  })

  it('renders error UI when child throws', () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow />
      </ErrorBoundary>
    )
    expect(screen.getByText('Что-то пошло не так')).toBeInTheDocument()
    expect(screen.getByText('Test render error')).toBeInTheDocument()
    expect(screen.getByText('Попробовать снова')).toBeInTheDocument()
  })

  it('does not show children when in error state', () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow />
      </ErrorBoundary>
    )
    expect(screen.queryByText('OK')).not.toBeInTheDocument()
  })

  it('reset button is rendered and clickable', () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow />
      </ErrorBoundary>
    )
    const btn = screen.getByText('Попробовать снова')
    expect(btn).toBeInTheDocument()
    // Clicking should not throw
    expect(() => fireEvent.click(btn)).not.toThrow()
  })
})
