import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getHistory, getDaily, fmt, haptic } from '../api.js'
import MealCard from '../components/MealCard.jsx'

export default function History() {
  const nav = useNavigate()
  const [days, setDays] = useState(null)
  const [selected, setSelected] = useState(null)  // { date, meals, total_nutrition }
  const [loading, setLoading] = useState(true)
  const [loadingDay, setLoadingDay] = useState(false)

  useEffect(() => {
    getHistory()
      .then(d => setDays(d.days))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const openDay = async (date) => {
    haptic()
    setLoadingDay(true)
    try {
      const d = await getDaily(date)
      setSelected(d)
    } catch { }
    finally { setLoadingDay(false) }
  }

  const updateMeal = (updated) => {
    setSelected(prev => {
      const meals = prev.meals.map(m => m.id === updated.id ? updated : m)
      return { ...prev, meals, total_nutrition: recalc(meals) }
    })
    // Refresh summary in list
    setDays(prev => prev.map(d => d.date === selected.date
      ? { ...d, calories: recalc(selected.meals.map(m => m.id === updated.id ? updated : m)).calories }
      : d
    ))
  }

  const deleteMealCb = (id) => {
    setSelected(prev => {
      const meals = prev.meals.filter(m => m.id !== id)
      return { ...prev, meals, total_nutrition: recalc(meals) }
    })
  }

  if (selected) return (
    <div className="page">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <button className="btn btn-ghost btn-sm" onClick={() => setSelected(null)}>← Назад</button>
        <div style={{ flex: 1 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700 }}>{fmt.date(selected.date)}</h2>
          <span style={{ fontSize: 13, color: 'var(--muted)' }}>
            🔥 {selected.total_nutrition?.calories} ккал
            · 💪 {Math.round(selected.total_nutrition?.protein_g)}г
            · 🥑 {Math.round(selected.total_nutrition?.fat_g)}г
          </span>
        </div>
        <button className="btn btn-primary btn-sm"
          onClick={() => { haptic(); nav(`/add?date=${selected.date}`) }}>
          + Добавить
        </button>
      </div>
      {selected.meals.length === 0
        ? <div className="empty"><div className="empty-icon">📋</div><p>Нет записей</p></div>
        : selected.meals.map(m => (
          <MealCard key={m.id} meal={m} onUpdated={updateMeal} onDeleted={deleteMealCb} />
        ))
      }
    </div>
  )

  return (
    <div className="page">
      <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>История</h2>

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
          <div className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
        </div>
      ) : days?.length === 0 ? (
        <div className="empty"><div className="empty-icon">📋</div><p>История пока пуста</p></div>
      ) : (
        days?.map(day => (
          <button key={day.date}
            onClick={() => openDay(day.date)}
            style={{ width: '100%', background: 'none', border: 'none', textAlign: 'left', cursor: 'pointer', marginBottom: 8 }}>
            <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <p style={{ fontWeight: 600 }}>{fmt.date(day.date)}</p>
                <p style={{ fontSize: 13, color: 'var(--muted)', marginTop: 2 }}>{day.meal_count} приёма</p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <p style={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{day.calories}</p>
                <p style={{ fontSize: 12, color: 'var(--muted)' }}>ккал</p>
              </div>
            </div>
          </button>
        ))
      )}
      {loadingDay && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200 }}>
          <div className="spinner" style={{ width: 40, height: 40, borderWidth: 4 }} />
        </div>
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
