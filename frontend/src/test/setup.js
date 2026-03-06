import '@testing-library/jest-dom'

// Mock Telegram Web App SDK
const mockWebApp = {
  ready: vi.fn(),
  expand: vi.fn(),
  close: vi.fn(),
  initData: 'test-init-data',
  initDataUnsafe: { user: { id: 123456, first_name: 'Test' } },
  colorScheme: 'light',
  themeParams: {},
  HapticFeedback: {
    impactOccurred: vi.fn(),
    notificationOccurred: vi.fn(),
    selectionChanged: vi.fn(),
  },
  MainButton: {
    show: vi.fn(),
    hide: vi.fn(),
    setText: vi.fn(),
    onClick: vi.fn(),
    offClick: vi.fn(),
  },
}

Object.defineProperty(window, 'Telegram', {
  value: { WebApp: mockWebApp },
  writable: true,
})

// Reset mocks between tests
beforeEach(() => {
  vi.clearAllMocks()
})
