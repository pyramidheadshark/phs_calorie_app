export default function MacroBar({ label, value, max, unit = 'г', color }) {
  const pct = Math.min((value / (max || 1)) * 100, 100)
  return (
    <div style={{ flex: 1 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
        <span style={{ fontSize: 12, color: 'var(--muted)' }}>{label}</span>
        <span style={{ fontSize: 12, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
          {Math.round(value)}<span style={{ color: 'var(--muted)', fontWeight: 400 }}>/{max}{unit}</span>
        </span>
      </div>
      <div style={{ height: 6, borderRadius: 3, background: 'var(--border)', overflow: 'hidden' }}>
        <div style={{
          height: '100%', borderRadius: 3,
          width: `${pct}%`,
          background: color,
          transition: 'width .5s ease',
        }} />
      </div>
    </div>
  )
}
