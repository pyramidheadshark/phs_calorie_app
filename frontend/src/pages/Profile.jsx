import { useState, useEffect } from 'react'
import { getSettings, updateSettings, parseProfile, generateRecipe, getRecipes, recipeFeedback, haptic } from '../api.js'
import { useSettings } from '../App.jsx'

export default function Profile() {
  const { reload } = useSettings()
  const [tab, setTab] = useState(0)
  const [form, setForm] = useState(null)
  const [profileText, setProfileText] = useState('')
  const [parsing, setParsing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [recipes, setRecipes] = useState([])
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    getSettings().then(s => {
      setForm({
        calorie_target: s.calorie_target,
        protein_target_g: s.protein_target_g,
        fat_target_g: s.fat_target_g,
        carbs_target_g: s.carbs_target_g,
        food_preferences: s.food_preferences ?? '',
        kitchen_equipment: (s.kitchen_equipment ?? []).join(', '),
        goal_description: s.goal_description ?? '',
        timezone: s.timezone ?? 'Europe/Moscow',
      })
      setProfileText(s.profile_text ?? '')
    }).catch(() => {})
    getRecipes().then(setRecipes).catch(() => {})
  }, [])

  const save = async () => {
    setSaving(true); haptic()
    try {
      await updateSettings({
        ...form,
        kitchen_equipment: form.kitchen_equipment.split(',').map(s => s.trim()).filter(Boolean),
      })
      await reload()
    } catch (e) { alert(e.message) }
    finally { setSaving(false) }
  }

  const parseAI = async () => {
    if (!profileText.trim()) return
    setParsing(true); haptic()
    try {
      const parsed = await parseProfile(profileText)
      setForm(f => ({
        ...f,
        calorie_target: parsed.calorie_target ?? f.calorie_target,
        protein_target_g: parsed.protein_target_g ?? f.protein_target_g,
        fat_target_g: parsed.fat_target_g ?? f.fat_target_g,
        carbs_target_g: parsed.carbs_target_g ?? f.carbs_target_g,
        goal_description: parsed.goal_description ?? f.goal_description,
        kitchen_equipment: (parsed.kitchen_equipment ?? []).join(', '),
        food_preferences: parsed.food_preferences ?? f.food_preferences,
      }))
    } catch (e) { alert(e.message) }
    finally { setParsing(false) }
  }

  const generate = async () => {
    setGenerating(true); haptic('medium')
    try {
      const r = await generateRecipe()
      setRecipes(prev => [r, ...prev])
    } catch (e) { alert(e.message) }
    finally { setGenerating(false) }
  }

  const feedback = async (id, liked) => {
    haptic()
    await recipeFeedback(id, liked).catch(() => {})
    setRecipes(prev => prev.map(r => r.id === id ? { ...r, liked } : r))
  }

  if (!form) return (
    <div className="page" style={{ display: 'flex', justifyContent: 'center', paddingTop: 60 }}>
      <div className="spinner" style={{ width: 36, height: 36, borderWidth: 3 }} />
    </div>
  )

  return (
    <div className="page">
      <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>Профиль</h2>

      <div className="tabs" style={{ marginBottom: 20 }}>
        {['🎯 Цели', '🤖 AI-профиль', '🍳 Рецепты'].map((t, i) => (
          <button key={i} className={`tab${tab === i ? ' active' : ''}`} onClick={() => setTab(i)}>{t}</button>
        ))}
      </div>

      {/* Goals tab */}
      {tab === 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {[
            ['calorie_target', '🔥 Калории (ккал)', 'number'],
            ['protein_target_g', '💪 Белки (г)', 'number'],
            ['fat_target_g', '🥑 Жиры (г)', 'number'],
            ['carbs_target_g', '🌾 Углеводы (г)', 'number'],
            ['goal_description', '🎯 Цель (текст)', 'text'],
            ['food_preferences', '🥗 Предпочтения в еде', 'text'],
            ['kitchen_equipment', '🍳 Оборудование (через запятую)', 'text'],
            ['timezone', '🌍 Часовой пояс', 'text'],
          ].map(([key, label, type]) => (
            <label key={key} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <span style={{ fontSize: 13, color: 'var(--muted)', fontWeight: 600 }}>{label}</span>
              <input className="input" type={type} value={form[key] ?? ''}
                onChange={e => setForm(f => ({ ...f, [key]: type === 'number' ? +e.target.value : e.target.value }))} />
            </label>
          ))}
          <button className="btn btn-primary" onClick={save} disabled={saving}>
            {saving ? <span className="spinner" /> : '💾 Сохранить'}
          </button>
        </div>
      )}

      {/* AI profile tab */}
      {tab === 1 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <p style={{ fontSize: 14, color: 'var(--muted)' }}>
            Опишите себя свободным текстом — рост, вес, цель, активность. AI сам поставит оптимальные цели.
          </p>
          <textarea className="input" rows={6}
            placeholder="Мне 28 лет, вешу 80кг, рост 180см, хочу похудеть до 72кг. Тренируюсь 3 раза в неделю. Не ем свинину."
            value={profileText}
            onChange={e => setProfileText(e.target.value)} />
          <button className="btn btn-primary" onClick={parseAI} disabled={parsing}>
            {parsing ? <><span className="spinner" /> Анализирую...</> : '✨ Рассчитать цели через AI'}
          </button>
          {form.calorie_target > 0 && (
            <>
              <div className="divider" />
              <p style={{ fontSize: 13, color: 'var(--muted)' }}>Текущие цели:</p>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <span className="chip chip-blue">🔥 {form.calorie_target} ккал</span>
                <span className="chip chip-green">💪 {form.protein_target_g}г</span>
                <span className="chip chip-orange">🥑 {form.fat_target_g}г</span>
                <span className="chip chip-muted">🌾 {form.carbs_target_g}г</span>
              </div>
              <button className="btn btn-primary" onClick={save} disabled={saving}>
                {saving ? <span className="spinner" /> : '💾 Сохранить цели'}
              </button>
            </>
          )}
        </div>
      )}

      {/* Recipes tab */}
      {tab === 2 && (
        <div>
          <button className="btn btn-primary" onClick={generate} disabled={generating} style={{ marginBottom: 20 }}>
            {generating ? <><span className="spinner" /> Генерирую...</> : '✨ Новый рецепт'}
          </button>
          {recipes.length === 0
            ? <div className="empty"><div className="empty-icon">🍳</div><p>Пока нет рецептов</p></div>
            : recipes.map(r => (
              <div key={r.id} className="card" style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                  <div style={{ flex: 1 }}>
                    <p style={{ fontWeight: 700, fontSize: 16 }}>{r.title}</p>
                    <p style={{ fontSize: 13, color: 'var(--muted)', marginTop: 2 }}>{r.description}</p>
                  </div>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button onClick={() => feedback(r.id, true)}
                      style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', opacity: r.liked === true ? 1 : 0.4 }}>👍</button>
                    <button onClick={() => feedback(r.id, false)}
                      style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', opacity: r.liked === false ? 1 : 0.4 }}>👎</button>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
                  <span className="chip chip-blue">🔥 {r.nutrition_estimate?.calories} ккал</span>
                  <span className="chip chip-muted">⏱ {r.cooking_time_min} мин</span>
                </div>
                <details>
                  <summary style={{ fontSize: 13, color: 'var(--accent)', cursor: 'pointer', userSelect: 'none' }}>Ингредиенты и шаги</summary>
                  <div style={{ marginTop: 10 }}>
                    <p style={{ fontSize: 12, fontWeight: 600, color: 'var(--muted)', marginBottom: 6 }}>ИНГРЕДИЕНТЫ</p>
                    {r.ingredients?.map((ing, i) => (
                      <p key={i} style={{ fontSize: 13, marginBottom: 3 }}>• {ing.name} — {ing.amount}</p>
                    ))}
                    <p style={{ fontSize: 12, fontWeight: 600, color: 'var(--muted)', margin: '10px 0 6px' }}>ПРИГОТОВЛЕНИЕ</p>
                    {r.instructions?.map((step, i) => (
                      <p key={i} style={{ fontSize: 13, marginBottom: 5 }}>{i + 1}. {step}</p>
                    ))}
                  </div>
                </details>
              </div>
            ))
          }
        </div>
      )}
    </div>
  )
}
