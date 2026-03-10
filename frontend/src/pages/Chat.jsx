import { useState, useRef, useEffect } from 'react'
import { sendChat, getDaily, today } from '../api.js'
import { useSettings } from '../App.jsx'

export default function Chat() {
  const { settings } = useSettings()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    getDaily(today()).then(data => {
      const cal = data.total_nutrition.calories
      const target = settings?.calorie_target ?? 2000
      const remaining = Math.max(0, target - cal)
      const greeting = remaining > 0
        ? `Привет! Сегодня съедено ${cal} из ${target} ккал — осталось ${remaining} ккал до нормы.`
        : `Привет! Норма на сегодня выполнена: ${cal} ккал. Отличная работа!`
      setMessages([{ role: 'assistant', text: greeting + ' Спроси меня о питании или попроси совет.' }])
    }).catch(() => {
      setMessages([{ role: 'assistant', text: 'Привет! Спроси меня что-нибудь о своём питании.' }])
    })
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setMessages(m => [...m, { role: 'user', text }])
    setLoading(true)
    try {
      const res = await sendChat(text)
      setMessages(m => [...m, { role: 'assistant', text: res.reply }])
    } catch (e) {
      setMessages(m => [...m, { role: 'assistant', text: `⚠️ ${e.message}` }])
    } finally {
      setLoading(false)
    }
  }

  const safeTop = 'calc(var(--tg-content-safe-area-inset-top, 0px) + 16px)'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100dvh - var(--nav-h))' }}>
      <div style={{ padding: `${safeTop} 16px 12px`, borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700 }}>Нутри-ассистент</h2>
        <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>Спроси о питании, рекомендации, анализ тенденций</p>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {messages.map((m, i) => (
          <div key={i} style={{
            alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '82%',
            background: m.role === 'user' ? 'var(--accent)' : 'var(--bg2)',
            color: m.role === 'user' ? 'var(--accent-t)' : 'var(--text)',
            borderRadius: m.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
            padding: '10px 14px',
            fontSize: 14,
            lineHeight: 1.55,
            boxShadow: '0 1px 3px rgba(0,0,0,.06)',
          }}>
            {m.text}
          </div>
        ))}
        {loading && (
          <div style={{
            alignSelf: 'flex-start',
            background: 'var(--bg2)',
            borderRadius: '18px 18px 18px 4px',
            padding: '14px 18px',
            boxShadow: '0 1px 3px rgba(0,0,0,.06)',
          }}>
            <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
              {[0, 1, 2].map(i => (
                <div key={i} style={{
                  width: 7, height: 7, borderRadius: '50%',
                  background: 'var(--muted)',
                  animation: 'pulse 1.2s ease-in-out infinite',
                  animationDelay: `${i * 0.2}s`,
                }} />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div style={{
        padding: '8px 16px',
        paddingBottom: 'calc(8px + env(safe-area-inset-bottom))',
        borderTop: '1px solid var(--border)',
        display: 'flex',
        gap: 8,
        flexShrink: 0,
      }}>
        <input
          className="input"
          placeholder="Написать сообщение..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          style={{ flex: 1 }}
        />
        <button
          className="btn btn-primary"
          onClick={send}
          disabled={loading || !input.trim()}
          style={{ width: 'auto', padding: '12px 18px', flexShrink: 0 }}
        >
          ➤
        </button>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 60%, 100% { opacity: 0.3; transform: scale(0.85); }
          30% { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </div>
  )
}
