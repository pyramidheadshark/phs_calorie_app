import { render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import App from '../App.jsx'

vi.mock('../api.js', () => ({
  getSettings: vi.fn().mockResolvedValue({
    calorie_target: 2000,
    macro_targets: { protein_g: 120, fat_g: 70, carbs_g: 250 },
    goal_description: '',
    food_preferences: '',
    kitchen_equipment: [],
  }),
  getDaily: vi.fn().mockResolvedValue({ meals: [], total: { calories: 0, protein_g: 0, fat_g: 0, carbs_g: 0 } }),
  getStreak: vi.fn().mockResolvedValue({ streak: 0, logged_dates: [] }),
  today: () => '2026-03-05',
  fmt: {
    kcal: (n) => `${Math.round(n)} ккал`,
    g: (n) => `${Math.round(n)} г`,
    date: (s) => s,
    time: (s) => '12:00',
  },
  haptic: vi.fn(),
}))

describe('App', () => {
  it('renders without crashing', async () => {
    render(<App />)
    // App renders — at minimum the nav should appear
    await waitFor(() => {
      expect(document.body).toBeInTheDocument()
    })
  })

  it('calls Telegram.WebApp.ready on mount', async () => {
    render(<App />)
    await waitFor(() => {
      expect(window.Telegram.WebApp.ready).toHaveBeenCalled()
    })
  })

  it('calls Telegram.WebApp.expand on mount', async () => {
    render(<App />)
    await waitFor(() => {
      expect(window.Telegram.WebApp.expand).toHaveBeenCalled()
    })
  })

  it('renders navigation', async () => {
    render(<App />)
    // Nav renders links — at least 4 nav items
    await waitFor(() => {
      const links = document.querySelectorAll('a[href]')
      expect(links.length).toBeGreaterThanOrEqual(4)
    })
  })
})
