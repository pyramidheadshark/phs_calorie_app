import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import MealCard from '../components/MealCard.jsx'

// Mock api module
vi.mock('../api.js', () => ({
  updateMeal: vi.fn(),
  deleteMeal: vi.fn(),
  haptic: vi.fn(),
  fmt: {
    time: (s) => '12:30',
    kcal: (n) => `${Math.round(n)} ккал`,
    g: (n) => `${Math.round(n)} г`,
  },
}))

import { updateMeal, deleteMeal } from '../api.js'

const fakeMeal = {
  id: 'meal-123',
  description: 'Овсянка с бананом',
  confidence: 'high',
  logged_at: '2026-03-05T09:00:00Z',
  nutrition: { calories: 350, protein_g: 12.5, fat_g: 8.0, carbs_g: 55.0, portion_g: 300 },
}

describe('MealCard — view mode', () => {
  it('renders description', () => {
    render(<MealCard meal={fakeMeal} />)
    expect(screen.getByText('Овсянка с бананом')).toBeInTheDocument()
  })

  it('renders calories chip', () => {
    render(<MealCard meal={fakeMeal} />)
    expect(screen.getByText(/350/)).toBeInTheDocument()
  })

  it('renders edit and delete buttons', () => {
    render(<MealCard meal={fakeMeal} />)
    expect(screen.getByText('✏️')).toBeInTheDocument()
    expect(screen.getByText('🗑')).toBeInTheDocument()
  })

  it('renders confidence dot (high = green)', () => {
    const { container } = render(<MealCard meal={fakeMeal} />)
    const dot = container.querySelector('[style*="var(--green)"]')
    expect(dot).toBeInTheDocument()
  })
})

describe('MealCard — edit mode', () => {
  it('switches to edit form on pencil click', async () => {
    const user = userEvent.setup()
    render(<MealCard meal={fakeMeal} />)
    await user.click(screen.getByText('✏️'))
    expect(screen.getByText('Сохранить')).toBeInTheDocument()
    expect(screen.getByText('Отмена')).toBeInTheDocument()
  })

  it('cancel returns to view mode', async () => {
    const user = userEvent.setup()
    render(<MealCard meal={fakeMeal} />)
    await user.click(screen.getByText('✏️'))
    await user.click(screen.getByText('Отмена'))
    expect(screen.getByText('Овсянка с бананом')).toBeInTheDocument()
    expect(screen.queryByText('Сохранить')).not.toBeInTheDocument()
  })

  it('calls updateMeal and onUpdated on save', async () => {
    const user = userEvent.setup()
    const updated = { ...fakeMeal, description: 'Изменено' }
    updateMeal.mockResolvedValueOnce(updated)
    const onUpdated = vi.fn()

    render(<MealCard meal={fakeMeal} onUpdated={onUpdated} />)
    await user.click(screen.getByText('✏️'))
    await user.click(screen.getByText('Сохранить'))

    await waitFor(() => {
      expect(updateMeal).toHaveBeenCalledWith('meal-123', expect.objectContaining({
        description: 'Овсянка с бананом',
      }))
      expect(onUpdated).toHaveBeenCalledWith(updated)
    })
  })

  it('calls deleteMeal and onDeleted after confirmation', async () => {
    const user = userEvent.setup()
    deleteMeal.mockResolvedValueOnce(null)
    const onDeleted = vi.fn()
    vi.spyOn(window, 'confirm').mockReturnValueOnce(true)

    render(<MealCard meal={fakeMeal} onDeleted={onDeleted} />)
    await user.click(screen.getByText('🗑'))

    await waitFor(() => {
      expect(deleteMeal).toHaveBeenCalledWith('meal-123')
      expect(onDeleted).toHaveBeenCalledWith('meal-123')
    })
  })

  it('does not delete if confirm returns false', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValueOnce(false)

    render(<MealCard meal={fakeMeal} />)
    await user.click(screen.getByText('🗑'))

    expect(deleteMeal).not.toHaveBeenCalled()
  })
})
