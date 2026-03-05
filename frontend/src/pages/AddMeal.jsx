import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyzeText, analyzePhoto, analyzeVoice, analyzeCombo, confirmMeal, haptic, fmt } from '../api.js'

const TABS = ['📷 Фото', '✏️ Текст', '🎤 Голос', '🔀 Комбо']

export default function AddMeal() {
  const nav = useNavigate()
  const [tab, setTab] = useState(0)
  const [pending, setPending] = useState([])   // confirmed items waiting to be saved
  const [result, setResult] = useState(null)   // current analysis result
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  // Photo
  const [photoFile, setPhotoFile] = useState(null)
  const [photoContext, setPhotoContext] = useState('')

  // Text
  const [textDesc, setTextDesc] = useState('')

  // Voice
  const [recording, setRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState(null)
  const recorderRef = useRef(null)
  const streamRef = useRef(null)

  // Combo (photo + voice)
  const [comboPhoto, setComboPhoto] = useState(null)
  const [comboAudio, setComboAudio] = useState(null)
  const [comboRecording, setComboRecording] = useState(false)
  const comboRecorderRef = useRef(null)
  const comboStreamRef = useRef(null)

  const analyze = async () => {
    setError(null)
    setLoading(true)
    haptic()
    try {
      let r
      if (tab === 0) {
        if (!photoFile) throw new Error('Выберите фото')
        r = await analyzePhoto(photoFile, photoContext)
      } else if (tab === 1) {
        if (!textDesc.trim()) throw new Error('Введите описание')
        r = await analyzeText(textDesc)
      } else if (tab === 2) {
        if (!audioBlob) throw new Error('Запишите голосовое сообщение')
        r = await analyzeVoice(audioBlob)
      } else {
        if (!comboPhoto || !comboAudio) throw new Error('Нужно фото и голосовое')
        r = await analyzeCombo(comboPhoto, comboAudio)
      }
      setResult({ ...r, photo_path: r.photo_path ?? null, gemini_raw: r.gemini_raw ?? {} })
    } catch (e) { setError(e.message); haptic('medium') }
    finally { setLoading(false) }
  }

  const addToPending = () => {
    haptic()
    setPending(p => [...p, result])
    setResult(null)
    setPhotoFile(null); setPhotoContext(''); setTextDesc(''); setAudioBlob(null)
    setComboPhoto(null); setComboAudio(null)
  }

  const confirmAll = async () => {
    const items = result ? [...pending, result] : pending
    if (!items.length) return
    setSaving(true); haptic('medium')
    try {
      for (const item of items) {
        await confirmMeal({
          description: item.description,
          nutrition: item.nutrition,
          confidence: item.confidence,
          photo_path: item.photo_path,
          gemini_raw: item.gemini_raw,
        })
      }
      haptic('light')
      nav('/')
    } catch (e) { setError(e.message) }
    finally { setSaving(false) }
  }

  const startRecording = async (isCombo = false) => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? 'audio/webm;codecs=opus' : 'audio/webm'
    const recorder = new MediaRecorder(stream, { mimeType: mime })
    const chunks = []
    recorder.ondataavailable = e => chunks.push(e.data)
    recorder.onstop = () => {
      const blob = new Blob(chunks, { type: mime })
      if (isCombo) setComboAudio(blob); else setAudioBlob(blob)
      stream.getTracks().forEach(t => t.stop())
    }
    recorder.start()
    if (isCombo) { comboRecorderRef.current = recorder; comboStreamRef.current = stream; setComboRecording(true) }
    else { recorderRef.current = recorder; streamRef.current = stream; setRecording(true) }
    haptic()
  }

  const stopRecording = (isCombo = false) => {
    if (isCombo) { comboRecorderRef.current?.stop(); setComboRecording(false) }
    else { recorderRef.current?.stop(); setRecording(false) }
    haptic()
  }

  return (
    <div className="page">
      <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>Добавить блюдо</h2>

      {/* Pending items */}
      {pending.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <p className="label">В очереди ({pending.length})</p>
          {pending.map((item, i) => (
            <div key={i} className="card" style={{ marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <p style={{ fontWeight: 500, fontSize: 14 }}>{item.description}</p>
                <span style={{ fontSize: 12, color: 'var(--muted)' }}>{item.nutrition?.calories} ккал</span>
              </div>
              <button className="btn btn-ghost btn-sm" style={{ color: 'var(--red)' }}
                onClick={() => setPending(p => p.filter((_, j) => j !== i))}>✕</button>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      {!result && (
        <>
          <div className="tabs" style={{ marginBottom: 16 }}>
            {TABS.map((t, i) => (
              <button key={i} className={`tab${tab === i ? ' active' : ''}`}
                onClick={() => { setTab(i); setError(null) }}>{t}</button>
            ))}
          </div>

          {/* Photo */}
          {tab === 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <label style={{ cursor: 'pointer' }}>
                <input type="file" accept="image/*" capture="environment" style={{ display: 'none' }}
                  onChange={e => setPhotoFile(e.target.files[0])} />
                <div className="card" style={{ textAlign: 'center', border: `2px dashed ${photoFile ? 'var(--accent)' : 'var(--border)'}`, background: 'transparent' }}>
                  {photoFile ? (
                    <img src={URL.createObjectURL(photoFile)} style={{ maxHeight: 200, borderRadius: 8, maxWidth: '100%' }} />
                  ) : (
                    <div style={{ padding: '32px 0', color: 'var(--muted)' }}>
                      <div style={{ fontSize: 36 }}>📷</div>
                      <p style={{ marginTop: 8 }}>Нажмите чтобы выбрать</p>
                    </div>
                  )}
                </div>
              </label>
              <textarea className="input" rows={2} placeholder="Дополнительный контекст (необязательно)"
                value={photoContext} onChange={e => setPhotoContext(e.target.value)} />
            </div>
          )}

          {/* Text */}
          {tab === 1 && (
            <textarea className="input" rows={4}
              placeholder="Например: 200г варёной гречки с куриной грудкой"
              value={textDesc} onChange={e => setTextDesc(e.target.value)} />
          )}

          {/* Voice */}
          {tab === 2 && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, padding: '20px 0' }}>
              <button
                onClick={() => recording ? stopRecording() : startRecording()}
                style={{
                  width: 80, height: 80, borderRadius: '50%', border: 'none', cursor: 'pointer',
                  background: recording ? 'var(--red)' : 'var(--accent)',
                  fontSize: 32, transition: 'all .2s',
                  boxShadow: recording ? '0 0 0 12px rgba(255,59,48,.2)' : '0 4px 12px rgba(0,122,255,.3)',
                }}>
                {recording ? '⏹' : '🎤'}
              </button>
              <p style={{ color: 'var(--muted)', fontSize: 14 }}>
                {recording ? 'Запись...' : audioBlob ? '✅ Записано. Нажмите ещё раз чтобы перезаписать' : 'Нажмите чтобы начать запись'}
              </p>
            </div>
          )}

          {/* Combo */}
          {tab === 3 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <label style={{ cursor: 'pointer' }}>
                <input type="file" accept="image/*" capture="environment" style={{ display: 'none' }}
                  onChange={e => setComboPhoto(e.target.files[0])} />
                <div className="card" style={{ textAlign: 'center', border: `2px dashed ${comboPhoto ? 'var(--accent)' : 'var(--border)'}`, background: 'transparent' }}>
                  {comboPhoto
                    ? <img src={URL.createObjectURL(comboPhoto)} style={{ maxHeight: 160, borderRadius: 8, maxWidth: '100%' }} />
                    : <div style={{ padding: '24px 0', color: 'var(--muted)' }}><div style={{ fontSize: 32 }}>📷</div><p style={{ marginTop: 6 }}>Фото блюда</p></div>}
                </div>
              </label>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                <button
                  onClick={() => comboRecording ? stopRecording(true) : startRecording(true)}
                  style={{
                    width: 64, height: 64, borderRadius: '50%', border: 'none', cursor: 'pointer',
                    background: comboRecording ? 'var(--red)' : comboAudio ? 'var(--green)' : 'var(--accent)',
                    fontSize: 26,
                  }}>
                  {comboRecording ? '⏹' : comboAudio ? '✅' : '🎤'}
                </button>
                <p style={{ fontSize: 13, color: 'var(--muted)' }}>
                  {comboRecording ? 'Запись...' : comboAudio ? 'Голосовое записано' : 'Записать описание'}
                </p>
              </div>
            </div>
          )}
        </>
      )}

      {/* Analysis result */}
      {result && (
        <div className="card" style={{ marginBottom: 16, borderTop: '3px solid var(--accent)' }}>
          <p style={{ fontWeight: 600, marginBottom: 8 }}>{result.description}</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
            <span className="chip chip-blue">🔥 {result.nutrition?.calories} ккал</span>
            <span className="chip chip-green">💪 {Math.round(result.nutrition?.protein_g)}г</span>
            <span className="chip chip-orange">🥑 {Math.round(result.nutrition?.fat_g)}г</span>
            <span className="chip chip-muted">🌾 {Math.round(result.nutrition?.carbs_g)}г</span>
            <span className={`chip chip-${result.confidence === 'high' ? 'green' : result.confidence === 'medium' ? 'orange' : 'red'}`}>
              {result.confidence === 'high' ? '✓ Уверен' : result.confidence === 'medium' ? '~ Примерно' : '? Не уверен'}
            </span>
          </div>
          {result.notes && <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12 }}>{result.notes}</p>}
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-secondary btn-sm" onClick={addToPending}>+ Добавить ещё</button>
            <button className="btn btn-ghost btn-sm" onClick={() => setResult(null)}>Переанализировать</button>
          </div>
        </div>
      )}

      {error && <p style={{ color: 'var(--red)', fontSize: 14, marginBottom: 12 }}>⚠️ {error}</p>}

      {/* Actions */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 16 }}>
        {!result && (
          <button className="btn btn-primary" onClick={analyze} disabled={loading}>
            {loading ? <><span className="spinner" /> Анализирую...</> : '🔍 Анализировать'}
          </button>
        )}
        {(pending.length > 0 || result) && (
          <button className="btn btn-primary" onClick={confirmAll} disabled={saving}
            style={{ background: 'var(--green)' }}>
            {saving ? <><span className="spinner" /> Сохраняю...</> : `✅ Сохранить${pending.length + (result ? 1 : 0) > 1 ? ` все (${pending.length + (result ? 1 : 0)})` : ''}`}
          </button>
        )}
        <button className="btn btn-ghost" onClick={() => nav('/')}>Отмена</button>
      </div>
    </div>
  )
}
