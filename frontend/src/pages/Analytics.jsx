import { useState, useEffect } from 'react'
import { getAnalytics } from '../api.js'
import { useSettings } from '../App.jsx'

export default function Analytics() {
  const { settings } = useSettings()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAnalytics().then(setData).catch(() => {}).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="page" style={{ display: 'flex', justifyContent: 'center', paddingTop: 60 }}>
      <div className="spinner" style={{ width: 36, height: 36, borderWidth: 3 }} />
    </div>
  )

  if (!data || data.total_days === 0) return (
    <div className="page">
      <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>Аналитика</h2>
      <div className="empty"><div className="empty-icon">📊</div><p>Недостаточно данных. Добавьте несколько записей!</p></div>
    </div>
  )

  const target = settings?.calorie_target ?? 2000

  return (
    <div className="page">
      <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>Аналитика</h2>

      {/* Summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
        <div className="card" style={{ textAlign: 'center' }}>
          <p style={{ fontSize: 28, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{data.avg_daily_calories}</p>
          <p style={{ fontSize: 12, color: 'var(--muted)' }}>ср. ккал/день</p>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <p style={{ fontSize: 28, fontWeight: 700 }}>{data.goal_adherence_pct}%</p>
          <p style={{ fontSize: 12, color: 'var(--muted)' }}>цель достигнута</p>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <p style={{ fontSize: 28, fontWeight: 700 }}>{data.total_days}</p>
          <p style={{ fontSize: 12, color: 'var(--muted)' }}>дней в статистике</p>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <p style={{ fontSize: 28, fontWeight: 700, color: data.avg_daily_calories > target ? 'var(--red)' : 'var(--green)' }}>
            {data.avg_daily_calories > target ? '+' : ''}{data.avg_daily_calories - target}
          </p>
          <p style={{ fontSize: 12, color: 'var(--muted)' }}>δ от цели</p>
        </div>
      </div>

      {/* Calorie trend */}
      {data.calorie_trend?.length > 0 && (
        <>
          <p className="label">Тренд калорий (14 дней)</p>
          <div className="card" style={{ marginBottom: 16 }}>
            <CalorieTrend data={data.calorie_trend} target={target} />
          </div>
        </>
      )}

      {/* Macro split */}
      {data.macro_split && (
        <>
          <p className="label">Распределение макросов</p>
          <div className="card" style={{ marginBottom: 16 }}>
            <MacroDonut split={data.macro_split} />
          </div>
        </>
      )}

      {/* Weekday pattern */}
      {data.weekday_avg && Object.keys(data.weekday_avg).length > 0 && (
        <>
          <p className="label">Паттерн по дням недели</p>
          <div className="card" style={{ marginBottom: 16 }}>
            <WeekdayChart data={data.weekday_avg} target={target} />
          </div>
        </>
      )}

      {/* Top meals */}
      {data.top_meals?.length > 0 && (
        <>
          <p className="label">Топ блюд</p>
          {data.top_meals.map((m, i) => (
            <div key={i} className="card" style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ flex: 1, marginRight: 12 }}>
                <p style={{ fontWeight: 500, fontSize: 14 }}>{m.description}</p>
                <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>~{m.avg_calories} ккал · {m.count}×</p>
              </div>
              <span style={{ fontSize: 20 }}>{'🥇🥈🥉🏅🏅'[i]}</span>
            </div>
          ))}
        </>
      )}
    </div>
  )
}

function CalorieTrend({ data, target }) {
  const W = 300, H = 100, pad = 8
  const vals = data.map(d => d.calories)
  const min = Math.min(...vals, 0)
  const max = Math.max(...vals, target * 1.2)
  const xStep = (W - pad * 2) / Math.max(data.length - 1, 1)
  const y = v => pad + (H - pad * 2) * (1 - (v - min) / (max - min))
  const pts = data.map((d, i) => `${pad + i * xStep},${y(d.calories)}`).join(' ')
  const targetY = y(target)

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%' }}>
      <line x1={pad} y1={targetY} x2={W - pad} y2={targetY}
        stroke="var(--border)" strokeWidth={1.5} strokeDasharray="4 3" />
      <polyline points={pts} fill="none" stroke="var(--accent)" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" />
      {data.map((d, i) => (
        <circle key={i} cx={pad + i * xStep} cy={y(d.calories)} r={3} fill="var(--accent)" />
      ))}
      <text x={W - pad} y={targetY - 4} textAnchor="end" fontSize={9} fill="var(--muted)">{target} ккал</text>
    </svg>
  )
}

function MacroDonut({ split }) {
  const { protein_pct, fat_pct, carbs_pct } = split
  const size = 100, stroke = 18, r = (size - stroke) / 2
  const c = 2 * Math.PI * r

  const slices = [
    { pct: protein_pct / 100, color: 'var(--green)',  label: '💪 Белки',    val: protein_pct },
    { pct: fat_pct / 100,     color: 'var(--orange)', label: '🥑 Жиры',     val: fat_pct },
    { pct: carbs_pct / 100,   color: 'var(--blue)',   label: '🌾 Углеводы', val: carbs_pct },
  ]
  let offset = 0
  const arcs = slices.map(s => {
    const dash = s.pct * c
    const gap = c - dash
    const rot = offset * 360 - 90
    offset += s.pct
    return { ...s, dash, gap, rot }
  })

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
      <svg width={size} height={size} style={{ flexShrink: 0 }}>
        {arcs.map((arc, i) => (
          <circle key={i} cx={size / 2} cy={size / 2} r={r}
            fill="none" stroke={arc.color} strokeWidth={stroke}
            strokeDasharray={`${arc.dash} ${arc.gap}`}
            style={{ transform: `rotate(${arc.rot}deg)`, transformOrigin: '50% 50%' }} />
        ))}
      </svg>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {slices.map((s, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 10, height: 10, borderRadius: 3, background: s.color, flexShrink: 0 }} />
            <span style={{ fontSize: 13 }}>{s.label}</span>
            <span style={{ fontSize: 13, fontWeight: 700, marginLeft: 'auto' }}>{s.val}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function WeekdayChart({ data, target }) {
  const entries = Object.entries(data)
  const maxVal = Math.max(...entries.map(([, v]) => v), target)
  const W = 300, H = 80, pad = 4
  const barW = (W - pad * 2) / entries.length - 4

  return (
    <svg viewBox={`0 0 ${W} ${H + 20}`} style={{ width: '100%' }}>
      {entries.map(([day, val], i) => {
        const bH = val / maxVal * H
        const x = pad + i * ((W - pad * 2) / entries.length)
        const color = val > target * 1.1 ? 'var(--red)' : val > target * 0.85 ? 'var(--accent)' : 'var(--green)'
        return (
          <g key={day}>
            <rect x={x} y={H - bH} width={barW} height={bH} rx={4} fill={color} opacity={0.85} />
            <text x={x + barW / 2} y={H + 14} textAnchor="middle" fontSize={10} fill="var(--muted)">{day}</text>
          </g>
        )
      })}
      <line x1={pad} y1={target / maxVal * H} x2={W - pad} y2={target / maxVal * H}
        stroke="var(--border)" strokeWidth={1.5} strokeDasharray="4 3"
        transform={`translate(0, ${H - target / maxVal * H}) scale(1, ${target / maxVal})`} />
    </svg>
  )
}
