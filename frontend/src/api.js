const tg = () => window.Telegram?.WebApp

function headers(isJson = true) {
  const h = { 'x-telegram-init-data': tg()?.initData || '' }
  if (isJson) h['Content-Type'] = 'application/json'
  return h
}

function humanError(status, body) {
  if (status === 429) return 'Превышен лимит запросов. Подождите минуту и попробуйте снова'
  if (status === 413) return 'Файл слишком большой. Максимум 10 МБ'
  if (status === 415) return 'Неподдерживаемый формат файла'
  if (status === 401) return 'Ошибка авторизации. Перезапустите приложение'
  if (status >= 500) return 'Сервер временно недоступен. Попробуйте снова'
  try {
    const parsed = JSON.parse(body)
    return parsed.detail || body || `Ошибка ${status}`
  } catch {
    return body || `Ошибка ${status}`
  }
}

async function req(path, opts = {}) {
  let r
  try {
    r = await fetch(path, opts)
  } catch {
    throw new Error('Нет соединения. Проверьте интернет')
  }
  if (!r.ok) {
    const text = await r.text().catch(() => '')
    throw new Error(humanError(r.status, text))
  }
  if (r.status === 204) return null
  return r.json()
}

const MAX_FILE_MB = 10
const MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024

function checkFileSize(file) {
  if (file && file.size > MAX_FILE_BYTES)
    throw new Error(`Файл слишком большой. Максимум ${MAX_FILE_MB} МБ`)
}

export const haptic = (type = 'light') => tg()?.HapticFeedback?.impactOccurred(type)

// ── Meals ──────────────────────────────────────────────────────────────────
export const analyzeText = (description) =>
  req('/api/meal/text', { method: 'POST', headers: headers(), body: JSON.stringify({ description }) })

export const analyzePhoto = (file, context = '') => {
  checkFileSize(file)
  const fd = new FormData()
  fd.append('file', file)
  fd.append('context', context)
  return req('/api/meal/photo-path', { method: 'POST', headers: headers(false), body: fd })
}

export const analyzeVoice = (blob) => {
  checkFileSize(blob)
  const fd = new FormData()
  fd.append('file', blob, 'voice.webm')
  return req('/api/meal/voice', { method: 'POST', headers: headers(false), body: fd })
}

export const analyzeCombo = (imageFile, audioBlob) => {
  checkFileSize(imageFile)
  checkFileSize(audioBlob)
  const fd = new FormData()
  fd.append('image', imageFile)
  fd.append('audio', audioBlob, 'voice.webm')
  return req('/api/meal/combo', { method: 'POST', headers: headers(false), body: fd })
}

export const confirmMeal = (data) =>
  req('/api/meal/confirm', { method: 'POST', headers: headers(), body: JSON.stringify(data) })

export const updateMeal = (id, data) =>
  req(`/api/meal/${id}`, { method: 'PATCH', headers: headers(), body: JSON.stringify(data) })

export const deleteMeal = (id) =>
  req(`/api/meal/${id}`, { method: 'DELETE', headers: headers() })

// ── Logs ──────────────────────────────────────────────────────────────────
export const getDaily = (date) =>
  req(`/api/daily/${date}`, { headers: headers() })

export const getHistory = () =>
  req('/api/history', { headers: headers() })

// ── Stats ─────────────────────────────────────────────────────────────────
export const getWeekly = () =>
  req('/api/stats/weekly', { headers: headers() })

export const getStreak = () =>
  req('/api/stats/streak', { headers: headers() })

export const getAnalytics = () =>
  req('/api/stats/analytics', { headers: headers() })

// ── Settings ──────────────────────────────────────────────────────────────
export const getSettings = () =>
  req('/api/user/settings', { headers: headers() })

export const updateSettings = (data) =>
  req('/api/user/settings', { method: 'POST', headers: headers(), body: JSON.stringify(data) })

export const parseProfile = (profile_text) =>
  req('/api/user/profile/parse', { method: 'POST', headers: headers(), body: JSON.stringify({ profile_text }) })

// ── Recipes ───────────────────────────────────────────────────────────────
export const generateRecipe = () =>
  req('/api/recipes/generate', { method: 'POST', headers: headers() })

export const getRecipes = () =>
  req('/api/recipes', { headers: headers() })

export const recipeFeedback = (id, liked) =>
  req(`/api/recipes/${id}/feedback`, { method: 'PATCH', headers: headers(), body: JSON.stringify({ liked }) })

// ── Helpers ───────────────────────────────────────────────────────────────
export const today = () => new Date().toISOString().slice(0, 10)

export const fmt = {
  kcal: (n) => `${Math.round(n)} ккал`,
  g: (n) => `${Math.round(n)} г`,
  date: (s) => new Date(s).toLocaleDateString('ru', { day: 'numeric', month: 'long' }),
  time: (s) => new Date(s).toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' }),
}
