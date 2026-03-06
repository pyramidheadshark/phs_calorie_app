import { render, screen } from '@testing-library/react'
import MacroBar from '../components/MacroBar.jsx'

describe('MacroBar', () => {
  it('renders label', () => {
    render(<MacroBar label="Белки" value={50} max={120} color="green" />)
    expect(screen.getByText('Белки')).toBeInTheDocument()
  })

  it('displays rounded value and max', () => {
    render(<MacroBar label="Жиры" value={25.7} max={70} color="orange" />)
    expect(screen.getByText('26')).toBeInTheDocument()
    expect(screen.getByText('/70г')).toBeInTheDocument()
  })

  it('uses custom unit', () => {
    render(<MacroBar label="Калории" value={1500} max={2000} unit=" ккал" color="blue" />)
    expect(screen.getByText('/2000 ккал')).toBeInTheDocument()
  })

  it('bar width does not exceed 100%', () => {
    const { container } = render(<MacroBar label="X" value={500} max={100} color="red" />)
    const bar = container.querySelector('[style*="width"]')
    expect(bar.style.width).toBe('100%')
  })

  it('bar width is 0% when value is 0', () => {
    const { container } = render(<MacroBar label="X" value={0} max={100} color="red" />)
    const bar = container.querySelector('[style*="width: 0%"]')
    expect(bar).toBeInTheDocument()
  })

  it('handles zero max without crash', () => {
    expect(() => render(<MacroBar label="X" value={10} max={0} color="red" />)).not.toThrow()
  })
})
