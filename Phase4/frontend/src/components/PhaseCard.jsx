export default function PhaseCard({ phaseNum, info, state, running, disabled, onRerun }) {
  const { status = 'pending', percent = 0, message = '' } = state || {}

  const statusColor = {
    pending:  '#555',
    running:  '#4facfe',
    done:     '#4cff88',
    error:    '#ff6666',
  }[status] || '#555'

  const statusLabel = {
    pending: 'Pending',
    running: 'Running',
    done:    'Complete',
    error:   'Error',
  }[status] || 'Pending'

  return (
    <div style={{
      ...styles.card,
      borderColor: running ? '#4facfe44' : 'rgba(255,255,255,0.07)',
      boxShadow:   running ? '0 0 12px #4facfe22' : 'none',
    }}>
      {/* Header row */}
      <div style={styles.header}>
        <span style={styles.icon}>{info.icon}</span>
        <div style={styles.meta}>
          <span style={styles.label}>{info.label}</span>
          <span style={styles.name}>{info.name}</span>
        </div>
        <div style={{ ...styles.badge, background: statusColor + '22', color: statusColor }}>
          {running ? '⏳' : status === 'done' ? '✓' : status === 'error' ? '✗' : '○'} {statusLabel}
        </div>
        <button
          style={{
            ...styles.rerunBtn,
            opacity: disabled || running ? 0.3 : 1,
            cursor:  disabled || running ? 'not-allowed' : 'pointer',
          }}
          onClick={onRerun}
          disabled={disabled || running}
          title={`Re-run ${info.name}`}
        >
          ↺ Re-run
        </button>
      </div>

      {/* Progress bar */}
      <div style={styles.barTrack}>
        <div style={{
          ...styles.barFill,
          width:      `${percent}%`,
          background: status === 'error' ? '#ff6666'
                    : status === 'done'  ? '#4cff88'
                    : 'linear-gradient(90deg, #6c63ff, #4facfe)',
          transition: 'width 0.4s ease',
        }} />
      </div>

      {/* Message */}
      {message && (
        <p style={{ ...styles.msg, color: status === 'error' ? '#ff8888' : '#aaa' }}>
          {message}
        </p>
      )}
    </div>
  )
}

const styles = {
  card: {
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid',
    borderRadius: 10, padding: '12px 16px',
    transition: 'box-shadow 0.3s, border-color 0.3s',
  },
  header:   { display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 },
  icon:     { fontSize: 22 },
  meta:     { display: 'flex', flexDirection: 'column' },
  label:    { fontSize: 11, color: '#666', fontWeight: 600, textTransform: 'uppercase' },
  name:     { fontSize: 14, fontWeight: 600, color: '#ddd' },
  badge:    { marginLeft: 'auto', fontSize: 12, fontWeight: 600, padding: '3px 10px', borderRadius: 12 },
  rerunBtn: {
    marginLeft: 8, padding: '4px 10px', borderRadius: 6,
    border: '1px solid rgba(255,255,255,0.15)',
    background: 'transparent', color: '#aaa',
    fontSize: 12, fontWeight: 600, transition: 'all 0.2s',
  },
  barTrack: { height: 4, background: '#1a1a2e', borderRadius: 2, overflow: 'hidden' },
  barFill:  { height: '100%', borderRadius: 2 },
  msg:      { fontSize: 12, marginTop: 6 },
}
