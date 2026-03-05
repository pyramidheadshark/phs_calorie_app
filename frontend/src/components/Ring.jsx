export default function Ring({ value = 0, max = 2000, size = 140, stroke = 12, children }) {
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const pct = Math.min(Math.max(value / (max || 1), 0), 1)
  const color = pct > 1.05 ? 'var(--red)' : pct > 0.9 ? 'var(--orange)' : 'var(--accent)'

  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke="var(--border)" strokeWidth={stroke} />
        <circle cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke={color} strokeWidth={stroke}
          strokeDasharray={`${pct * c} ${c}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray .5s ease' }} />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        gap: 2,
      }}>
        {children}
      </div>
    </div>
  )
}
