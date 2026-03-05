import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import Ring from '../components/Ring.jsx'
import MacroBar from '../components/MacroBar.jsx'
import MealCard from '../components/MealCard.jsx'
import { getDaily, getStreak, today, fmt, haptic } from '../api.js'
import { useSettings } from '../App.jsx'

export default function Home() {
  const nav = useNavigate()
  const { settings } = useSettings()
  const [log, setLog] = useState(null)
  const [streak, setStreak] = useState(0)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [d, s] = await Promise.all([getDaily(today()), getStreak()])
      setLog(d)
      setStreak(s.streak_days)
    } catch { /* not authed in browser */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const cal   = log?.total_nutrition?.calories ?? 0
  const prot  = log?.total_nutrition?.protein_g ?? 0
  const fat   = log?.total_nutrition?.fat_g ?? 0
  const carbs = log?.total_nutrition?.carbs_g ?? 0

  const targets = {
    cal:   settings?.calorie_target      ?? 2000,
    prot:  settings?.macro_targets?.protein_g ?? 120,
    fat:   settings?.macro_targets?.fat_g     ?? 70,
    carbs: settings?.macro_targets?.carbs_g   ?? 250,
  }

  const dateLabel = new Date().toLocaleDateString('ru', { weekday: 'long', day: 'numeric', month: 'long' })

  const updateMeal = (updated) => {
    setLog(prev => ({
      ...prev,
      meals: prev.meals.map(m => m.id === updated.id ? updated : m),
      total_nutrition: recalc([...prev.meals.map(m => m.id === updated.id ? updated : m)]),
    }))
  }
  const deleteMealCb = (id) => {
    setLog(prev => {
      const meals = prev.meals.filter(m => m.id !== id)
      return { ...prev, meals, total_nutrition: recalc(meals) }
    })
  }

  return (
    <div className="page">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 700, textTransform: 'capitalize' }}>
            {dateLabel}
          </h2>
          {streak > 0 && (
            <span style={{ fontSize: 13, color: 'var(--muted)' }}>🔥 {streak} дней подряд</span>
          )}
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
          <div className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
        </div>
      ) : (
        <>
          {/* Calorie ring */}
          <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: 16 }}>
            <Ring value={cal} max={targets.cal} size={140} stroke={12}>
              <span style={{ fontSize: 28, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{cal}</span>
              <span style={{ fontSize: 12, color: 'var(--muted)' }}>из {targets.cal} ккал</span>
              <span style={{ fontSize: 12, color: cal < targets.cal ? 'var(--green)' : 'var(--red)' }}>
                {cal < targets.cal ? `–${targets.cal - cal}` : `+${cal - targets.cal}`}
              </span>
            </Ring>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 10 }}>
              <MacroBar label="💪 Белки"   value={prot}  max={targets.prot}  color="var(--green)"  />
              <MacroBar label="🥑 Жиры"    value={fat}   max={targets.fat}   color="var(--orange)" />
              <MacroBar label="🌾 Углеводы" value={carbs} max={targets.carbs} color="var(--blue)"   />
            </div>
          </div>

          {/* Meals */}
          <p className="label">Приёмы пищи</p>
          {log?.meals?.length > 0 ? (
            log.meals.map(m => (
              <MealCard key={m.id} meal={m} onUpdated={updateMeal} onDeleted={deleteMealCb} />
            ))
          ) : (
            <div className="empty">
              <div className="empty-icon">🍽️</div>
              <p>Ещё ничего не добавлено</p>
              <button className="btn btn-primary" style={{ marginTop: 16, width: 'auto' }}
                onClick={() => { haptic(); nav('/add') }}>
                Добавить блюдо
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function recalc(meals) {
  return {
    calories: meals.reduce((s, m) => s + (m.nutrition?.calories ?? 0), 0),
    protein_g: meals.reduce((s, m) => s + (m.nutrition?.protein_g ?? 0), 0),
    fat_g: meals.reduce((s, m) => s + (m.nutrition?.fat_g ?? 0), 0),
    carbs_g: meals.reduce((s, m) => s + (m.nutrition?.carbs_g ?? 0), 0),
  }
}
