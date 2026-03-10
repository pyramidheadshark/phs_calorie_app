import { useState, useEffect, createContext, useContext } from 'react'
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import Nav from './components/Nav.jsx'
import Home from './pages/Home.jsx'
import AddMeal from './pages/AddMeal.jsx'
import History from './pages/History.jsx'
import Analytics from './pages/Analytics.jsx'
import Chat from './pages/Chat.jsx'
import Profile from './pages/Profile.jsx'
import { getSettings } from './api.js'

const SettingsCtx = createContext({ settings: null, reload: () => {} })
export const useSettings = () => useContext(SettingsCtx)

export default function App() {
  const [settings, setSettings] = useState(null)

  const load = async () => {
    try { setSettings(await getSettings()) } catch { /* not authenticated in browser */ }
  }

  useEffect(() => {
    const tg = window.Telegram?.WebApp
    tg?.ready()
    tg?.expand()
    // Apply dark/light class so CSS vars work correctly outside Telegram
    document.documentElement.dataset.theme = tg?.colorScheme ?? 'light'
    load()
  }, [])

  return (
    <SettingsCtx.Provider value={{ settings, reload: load }}>
      <HashRouter>
        <Routes>
          <Route path="/"          element={<Home />} />
          <Route path="/add"       element={<AddMeal />} />
          <Route path="/history"   element={<History />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/chat"      element={<Chat />} />
          <Route path="/profile"   element={<Profile />} />
          <Route path="*"          element={<Navigate to="/" replace />} />
        </Routes>
        <Nav />
      </HashRouter>
    </SettingsCtx.Provider>
  )
}
