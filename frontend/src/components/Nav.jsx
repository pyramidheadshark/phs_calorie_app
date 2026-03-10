import { NavLink } from 'react-router-dom'

const items = [
  { to: '/',          emoji: '🏠', label: 'Сегодня'  },
  { to: '/history',   emoji: '📋', label: 'История'  },
  { to: '/add',       emoji: '➕', label: 'Добавить', fab: true },
  { to: '/chat',      emoji: '💬', label: 'Ассистент' },
  { to: '/analytics', emoji: '📊', label: 'Аналитика' },
  { to: '/profile',   emoji: '👤', label: 'Профиль'  },
]

export default function Nav() {
  return (
    <nav style={{
      position: 'fixed', bottom: 0, left: 0, right: 0,
      height: 'var(--nav-h)',
      background: 'var(--bg2)',
      borderTop: '1px solid var(--border)',
      display: 'flex',
      alignItems: 'center',
      backdropFilter: 'blur(12px)',
      WebkitBackdropFilter: 'blur(12px)',
      paddingBottom: 'env(safe-area-inset-bottom)',
      zIndex: 100,
    }}>
      {items.map(({ to, emoji, label, fab }) => (
        <NavLink key={to} to={to} style={{ flex: 1, textDecoration: 'none' }}>
          {({ isActive }) => (
            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              gap: 2, padding: '4px 0',
            }}>
              {fab ? (
                <div style={{
                  width: 40, height: 40,
                  borderRadius: '50%',
                  background: 'var(--accent)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 18, marginTop: -8,
                  boxShadow: '0 4px 12px rgba(0,122,255,.35)',
                }}>
                  {emoji}
                </div>
              ) : (
                <span style={{ fontSize: 20 }}>{emoji}</span>
              )}
              <span style={{
                fontSize: 9, fontWeight: 600,
                color: isActive ? 'var(--accent)' : 'var(--muted)',
              }}>
                {label}
              </span>
            </div>
          )}
        </NavLink>
      ))}
    </nav>
  )
}
