import { useState } from 'react'
import { updateMeal, deleteMeal, haptic, fmt } from '../api.js'

export default function MealCard({ meal, onUpdated, onDeleted }) {
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    description: meal.description,
    calories: meal.nutrition.calories,
    protein_g: meal.nutrition.protein_g,
    fat_g: meal.nutrition.fat_g,
    carbs_g: meal.nutrition.carbs_g,
  })
  const [saving, setSaving] = useState(false)

  const confidenceColor = { high: 'var(--green)', medium: 'var(--orange)', low: 'var(--red)' }

  const save = async () => {
    setSaving(true)
    haptic()
    try {
      const updated = await updateMeal(meal.id, {
        description: form.description,
        nutrition: {
          calories: +form.calories,
          protein_g: +form.protein_g,
          fat_g: +form.fat_g,
          carbs_g: +form.carbs_g,
          portion_g: meal.nutrition.portion_g,
        },
      })
      onUpdated?.(updated)
      setEditing(false)
    } catch (e) { alert(e.message) }
    finally { setSaving(false) }
  }

  const remove = async () => {
    if (!confirm('Удалить запись?')) return
    haptic('medium')
    await deleteMeal(meal.id)
    onDeleted?.(meal.id)
  }

  return (
    <div className="card" style={{ marginBottom: 10 }}>
      {!editing ? (
        <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>{fmt.time(meal.logged_at)}</span>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: confidenceColor[meal.confidence], flexShrink: 0 }} />
            </div>
            <p style={{ fontWeight: 500, marginBottom: 6, lineHeight: 1.3 }}>{meal.description}</p>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <span className="chip chip-blue">🔥 {meal.nutrition.calories} ккал</span>
              <span className="chip chip-green">💪 {Math.round(meal.nutrition.protein_g)}г</span>
              <span className="chip chip-orange">🥑 {Math.round(meal.nutrition.fat_g)}г</span>
              <span className="chip chip-muted">🌾 {Math.round(meal.nutrition.carbs_g)}г</span>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <button className="btn btn-ghost btn-sm" onClick={() => setEditing(true)}>✏️</button>
            <button className="btn btn-ghost btn-sm" onClick={remove} style={{ color: 'var(--red)' }}>🗑</button>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <textarea className="input" rows={2} value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {[['calories','🔥 Ккал'],['protein_g','💪 Белки'],['fat_g','🥑 Жиры'],['carbs_g','🌾 Углеводы']].map(([k, label]) => (
              <label key={k} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <span style={{ fontSize: 11, color: 'var(--muted)' }}>{label}</span>
                <input className="input" type="number" value={form[k]}
                  onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))} />
              </label>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary" onClick={save} disabled={saving}>
              {saving ? <span className="spinner" /> : 'Сохранить'}
            </button>
            <button className="btn btn-secondary" onClick={() => setEditing(false)}>Отмена</button>
          </div>
        </div>
      )}
    </div>
  )
}
