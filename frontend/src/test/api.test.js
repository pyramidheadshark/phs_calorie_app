import { fmt, today, haptic } from '../api.js'

describe('fmt helpers', () => {
  describe('fmt.kcal', () => {
    it('rounds and appends unit', () => {
      expect(fmt.kcal(1500)).toBe('1500 ккал')
      expect(fmt.kcal(1500.7)).toBe('1501 ккал')
    })
  })

  describe('fmt.g', () => {
    it('rounds and appends г', () => {
      expect(fmt.g(25.4)).toBe('25 г')
      expect(fmt.g(25.6)).toBe('26 г')
    })
  })

  describe('fmt.date', () => {
    it('returns non-empty string for valid ISO date', () => {
      const result = fmt.date('2026-03-05T10:00:00Z')
      expect(typeof result).toBe('string')
      expect(result.length).toBeGreaterThan(0)
    })
  })

  describe('fmt.time', () => {
    it('returns HH:MM formatted string', () => {
      const result = fmt.time('2026-03-05T09:30:00Z')
      expect(typeof result).toBe('string')
      // e.g. "09:30" or "12:30" depending on timezone
      expect(result).toMatch(/\d{1,2}:\d{2}/)
    })
  })
})

describe('today', () => {
  it('returns YYYY-MM-DD format', () => {
    const result = today()
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })

  it('matches current date', () => {
    const expected = new Date().toISOString().slice(0, 10)
    expect(today()).toBe(expected)
  })
})

describe('haptic', () => {
  it('calls HapticFeedback when Telegram is available', () => {
    haptic('light')
    expect(window.Telegram.WebApp.HapticFeedback.impactOccurred).toHaveBeenCalledWith('light')
  })

  it('does not throw when Telegram is undefined', () => {
    const original = window.Telegram
    window.Telegram = undefined
    expect(() => haptic()).not.toThrow()
    window.Telegram = original
  })
})

describe('req error handling', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('throws error when response is not ok', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      text: async () => '{"detail":"Invalid input"}',
    })

    // Import inline to use real req function
    const { analyzeText } = await import('../api.js')
    await expect(analyzeText('test')).rejects.toThrow()
  })

  it('returns null on 204 response', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      status: 204,
      statusText: 'No Content',
    })

    const { deleteMeal } = await import('../api.js')
    const result = await deleteMeal('some-id')
    expect(result).toBeNull()
  })
})
