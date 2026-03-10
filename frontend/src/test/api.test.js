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

  it('throws Russian message on network failure', async () => {
    fetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

    const { analyzeText } = await import('../api.js')
    await expect(analyzeText('test')).rejects.toThrow('Нет соединения')
  })

  it('throws rate limit message on 429', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 429,
      text: async () => 'Too Many Requests',
    })

    const { analyzeText } = await import('../api.js')
    await expect(analyzeText('test')).rejects.toThrow('Превышен лимит')
  })

  it('throws auth message on 401', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      text: async () => 'Unauthorized',
    })

    const { analyzeText } = await import('../api.js')
    await expect(analyzeText('test')).rejects.toThrow('авторизации')
  })

  it('throws server error message on 500', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: async () => 'Internal Server Error',
    })

    const { analyzeText } = await import('../api.js')
    await expect(analyzeText('test')).rejects.toThrow('временно недоступен')
  })
})

describe('sendChat', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('POSTs to /api/chat with message and returns reply', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ reply: 'Отличный вопрос!' }),
    })

    const { sendChat } = await import('../api.js')
    const result = await sendChat('Что поесть?')

    expect(result.reply).toBe('Отличный вопрос!')
    expect(fetch).toHaveBeenCalledWith(
      '/api/chat',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ message: 'Что поесть?' }),
      })
    )
  })

  it('throws on non-ok response', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: async () => 'Server error',
    })

    const { sendChat } = await import('../api.js')
    await expect(sendChat('тест')).rejects.toThrow()
  })
})

describe('checkFileSize', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('throws immediately for files over 10MB without fetching', async () => {
    const bigFile = { size: 11 * 1024 * 1024, name: 'big.jpg' }
    const { analyzePhoto } = await import('../api.js')
    let threw = false
    try {
      await analyzePhoto(bigFile)
    } catch (e) {
      threw = true
      expect(e.message).toMatch('слишком большой')
    }
    expect(threw).toBe(true)
    expect(fetch).not.toHaveBeenCalled()
  })

  it('does not throw for files under 10MB', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ description: 'test', nutrition: {}, confidence: 'high' }),
    })
    const smallFile = { size: 1 * 1024 * 1024, name: 'small.jpg' }
    const { analyzePhoto } = await import('../api.js')
    // Should not throw from size check (may fail for other reasons)
    await analyzePhoto(smallFile).catch(() => {})
    expect(fetch).toHaveBeenCalled()
  })
})
