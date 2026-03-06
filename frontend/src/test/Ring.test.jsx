import { render, screen } from '@testing-library/react'
import Ring from '../components/Ring.jsx'

describe('Ring', () => {
  it('renders children inside the ring', () => {
    render(<Ring value={1000} max={2000}><span>1000</span></Ring>)
    expect(screen.getByText('1000')).toBeInTheDocument()
  })

  it('renders two SVG circles', () => {
    const { container } = render(<Ring value={500} max={2000} />)
    const circles = container.querySelectorAll('circle')
    expect(circles).toHaveLength(2)
  })

  it('uses accent color when under 90%', () => {
    const { container } = render(<Ring value={1000} max={2000} />)
    const filled = container.querySelectorAll('circle')[1]
    expect(filled.getAttribute('stroke')).toBe('var(--accent)')
  })

  it('uses orange color when between 90% and 105%', () => {
    const { container } = render(<Ring value={1900} max={2000} />)
    const filled = container.querySelectorAll('circle')[1]
    expect(filled.getAttribute('stroke')).toBe('var(--orange)')
  })

  it('uses orange color at 100% (pct clamped to 1, never exceeds 1.05)', () => {
    // pct = Math.min(value / max, 1) — so overflow shows orange, not red
    const { container } = render(<Ring value={2200} max={2000} />)
    const filled = container.querySelectorAll('circle')[1]
    expect(filled.getAttribute('stroke')).toBe('var(--orange)')
  })

  it('clamps value to 100% max fill', () => {
    const { container } = render(<Ring value={9999} max={2000} size={140} stroke={12} />)
    const filled = container.querySelectorAll('circle')[1]
    const dasharray = filled.getAttribute('stroke-dasharray')
    // pct clamped to 1 — both numbers in dasharray should be equal (full circle)
    const [a, b] = dasharray.split(' ').map(Number)
    expect(a).toBeCloseTo(b, 1)
  })

  it('handles zero max without dividing by zero', () => {
    expect(() => render(<Ring value={100} max={0} />)).not.toThrow()
  })

  it('respects custom size prop', () => {
    const { container } = render(<Ring value={0} max={2000} size={200} />)
    const svg = container.querySelector('svg')
    expect(svg).toHaveAttribute('width', '200')
    expect(svg).toHaveAttribute('height', '200')
  })
})
