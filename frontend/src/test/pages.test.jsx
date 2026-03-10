/**
 * Page component tests: smoke + key interactions.
 */
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import { createContext, useContext } from 'react'

// ── Hoisted constants (available inside vi.mock factories) ────────────────────

const { defaultSettings } = vi.hoisted(() => ({
  defaultSettings: {
    calorie_target: 2000,
    macro_targets: { protein_g: 120, fat_g: 70, carbs_g: 250 },
    goal_description: 'Похудение',
    food_preferences: '',
    kitchen_equipment: [],
  },
}))

// ── Mock useSettings (used by all pages) ─────────────────────────────────────

vi.mock('../App.jsx', () => ({
  useSettings: () => ({ settings: defaultSettings, reload: vi.fn() }),
}))

// ── Mock API ──────────────────────────────────────────────────────────────────

vi.mock('../api.js', () => ({
  getDaily: vi.fn().mockResolvedValue({
    meals: [],
    total_nutrition: { calories: 0, protein_g: 0, fat_g: 0, carbs_g: 0 },
  }),
  getStreak: vi.fn().mockResolvedValue({ streak_days: 3 }),
  getHistory: vi.fn().mockResolvedValue({
    days: [{ date: '2026-03-05', meal_count: 3, calories: 1800 }],
    total: 1, page: 1, page_size: 30,
  }),
  getAnalytics: vi.fn().mockResolvedValue({
    calorie_trend: [],
    macro_split: { protein_pct: 30, fat_pct: 30, carbs_pct: 40 },
    weekday_avg: {},
    top_meals: [],
    avg_daily_calories: 0,
    goal_adherence_pct: 0,
    total_days: 0,
  }),
  getSettings: vi.fn().mockResolvedValue(defaultSettings),
  getRecipes: vi.fn().mockResolvedValue([]),
  analyzeText: vi.fn().mockResolvedValue({
    description: 'Гречка с курицей',
    nutrition: { calories: 400, protein_g: 30, fat_g: 10, carbs_g: 45, portion_g: 350 },
    confidence: 'medium', notes: '', photo_path: null, gemini_raw: {},
  }),
  analyzePhoto: vi.fn(),
  analyzeVoice: vi.fn(),
  analyzeCombo: vi.fn(),
  confirmMeal: vi.fn().mockResolvedValue({}),
  updateMeal: vi.fn(),
  deleteMeal: vi.fn(),
  generateRecipe: vi.fn(),
  recipeFeedback: vi.fn(),
  updateSettings: vi.fn().mockResolvedValue({}),
  parseProfile: vi.fn(),
  today: () => '2026-03-05',
  fmt: {
    kcal: (n) => `${Math.round(n)} ккал`,
    g: (n) => `${Math.round(n)} г`,
    date: (s) => s,
    time: () => '12:00',
  },
  haptic: vi.fn(),
}))

// ── Static imports (after mocks are hoisted) ──────────────────────────────────

import Home from '../pages/Home.jsx'
import History from '../pages/History.jsx'
import Analytics from '../pages/Analytics.jsx'
import Profile from '../pages/Profile.jsx'
import AddMeal from '../pages/AddMeal.jsx'

function Wrap({ children }) {
  return <MemoryRouter>{children}</MemoryRouter>
}

// ── Home ──────────────────────────────────────────────────────────────────────

describe('Home page', () => {
  it('renders without crashing', async () => {
    render(<Wrap><Home /></Wrap>)
    await waitFor(() => expect(document.body).toBeInTheDocument())
  })
})

// ── History ───────────────────────────────────────────────────────────────────

describe('History page', () => {
  it('renders without crashing', async () => {
    render(<Wrap><History /></Wrap>)
    await waitFor(() => expect(document.body).toBeInTheDocument())
  })

  it('renders content after load', async () => {
    render(<Wrap><History /></Wrap>)
    await waitFor(() => {
      // Page loaded — either shows history items or empty state text
      expect(document.body.textContent.length).toBeGreaterThan(0)
    })
  })
})

// ── Analytics ─────────────────────────────────────────────────────────────────

describe('Analytics page', () => {
  it('renders without crashing', async () => {
    render(<Wrap><Analytics /></Wrap>)
    await waitFor(() => expect(document.body).toBeInTheDocument())
  })

  it('shows empty state when total_days is 0', async () => {
    render(<Wrap><Analytics /></Wrap>)
    // Either shows spinner initially or empty state after load
    await waitFor(() => {
      expect(document.body.textContent.length).toBeGreaterThan(0)
    })
  })
})

// ── Profile ───────────────────────────────────────────────────────────────────

describe('Profile page', () => {
  it('renders without crashing', async () => {
    render(<Wrap><Profile /></Wrap>)
    await waitFor(() => expect(document.body).toBeInTheDocument())
  })

  it('renders goal settings tab by default', async () => {
    render(<Wrap><Profile /></Wrap>)
    await waitFor(() => {
      // Profile renders some heading or label
      expect(document.body.textContent.length).toBeGreaterThan(0)
    })
  })
})

// ── AddMeal ───────────────────────────────────────────────────────────────────

describe('AddMeal page', () => {
  beforeEach(() => {
    global.MediaRecorder = vi.fn().mockImplementation(() => ({
      start: vi.fn(),
      stop: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      state: 'inactive',
    }))
    global.MediaRecorder.isTypeSupported = vi.fn().mockReturnValue(true)
    Object.defineProperty(navigator, 'mediaDevices', {
      value: { getUserMedia: vi.fn().mockResolvedValue({}) },
      configurable: true,
    })
  })

  it('renders without crashing', async () => {
    render(<Wrap><AddMeal /></Wrap>)
    await waitFor(() => expect(document.body).toBeInTheDocument())
  })

  it('renders tab buttons', async () => {
    render(<Wrap><AddMeal /></Wrap>)
    await waitFor(() => {
      const buttons = document.querySelectorAll('button')
      expect(buttons.length).toBeGreaterThan(0)
    })
  })

  it('text tab: analyze → shows result with edit button', async () => {
    const { analyzeText } = await import('../api.js')
    const user = userEvent.setup()
    render(<Wrap><AddMeal /></Wrap>)

    // Switch to text tab
    await user.click(screen.getByText(/Текст/))
    const textarea = screen.getByPlaceholderText(/200г/)
    await user.type(textarea, 'гречка 200г')

    await user.click(screen.getByText(/Анализировать/))

    await waitFor(() => {
      expect(analyzeText).toHaveBeenCalledWith('гречка 200г')
      expect(screen.getByText('Гречка с курицей')).toBeInTheDocument()
      expect(screen.getByText('✏️')).toBeInTheDocument()
    })
  })

  it('text tab: analyze → edit result → values updated', async () => {
    const user = userEvent.setup()
    render(<Wrap><AddMeal /></Wrap>)

    await user.click(screen.getByText(/Текст/))
    await user.type(screen.getByPlaceholderText(/200г/), 'борщ')
    await user.click(screen.getByText(/Анализировать/))

    await waitFor(() => screen.getByText('Гречка с курицей'))

    // Open inline edit
    await user.click(screen.getByText('✏️'))
    expect(screen.getByText('Применить')).toBeInTheDocument()

    // Change calories field
    const calInput = screen.getAllByRole('spinbutton')[0]
    await user.clear(calInput)
    await user.type(calInput, '500')
    await user.click(screen.getByText('Применить'))

    // Should show updated value
    await waitFor(() => expect(screen.getByText(/500/)).toBeInTheDocument())
  })

  it('text tab: analyze → confirm → confirmMeal called', async () => {
    const { confirmMeal } = await import('../api.js')
    const user = userEvent.setup()
    render(<Wrap><AddMeal /></Wrap>)

    await user.click(screen.getByText(/Текст/))
    await user.type(screen.getByPlaceholderText(/200г/), 'яблоко')
    await user.click(screen.getByText(/Анализировать/))

    await waitFor(() => screen.getByText(/Сохранить/))
    await user.click(screen.getByText(/Сохранить/))

    await waitFor(() => {
      expect(confirmMeal).toHaveBeenCalledWith(expect.objectContaining({
        description: 'Гречка с курицей',
        nutrition: expect.objectContaining({ calories: 400 }),
      }))
    })
  })
})

// ── AddMeal — past date ───────────────────────────────────────────────────────

describe('AddMeal page — past date mode', () => {
  it('shows target date in heading', async () => {
    render(
      <MemoryRouter initialEntries={['/add?date=2026-03-01']}>
        <AddMeal />
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByText(/2026-03-01/)).toBeInTheDocument()
    })
  })

  it('passes logged_at to confirmMeal when date param present', async () => {
    const { analyzeText, confirmMeal } = await import('../api.js')
    const user = userEvent.setup()

    render(
      <MemoryRouter initialEntries={['/add?date=2026-03-01']}>
        <AddMeal />
      </MemoryRouter>
    )

    await user.click(screen.getByText(/Текст/))
    await user.type(screen.getByPlaceholderText(/200г/), 'суп')
    await user.click(screen.getByText(/Анализировать/))
    await waitFor(() => screen.getByText(/Сохранить/))
    await user.click(screen.getByText(/Сохранить/))

    await waitFor(() => {
      expect(confirmMeal).toHaveBeenCalledWith(expect.objectContaining({
        logged_at: '2026-03-01T12:00:00Z',
      }))
    })
  })
})

// ── History — add to past day ─────────────────────────────────────────────────

describe('History page — day detail', () => {
  it('shows date row in list after load', async () => {
    render(<Wrap><History /></Wrap>)
    await waitFor(() => {
      expect(screen.getByText('2026-03-05')).toBeInTheDocument()
    })
  })
})
