import { useState, useEffect } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

export default function VersionHistory() {
  const [history,   setHistory]   = useState([])
  const [loading,   setLoading]   = useState(false)
  const [reverting, setReverting] = useState(null)
  const [message,   setMessage]   = useState('')

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const res = await axios.get(`${API}/api/history`)
      setHistory(res.data.history || [])
    } catch (e) {
      setMessage('Failed to load history')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
    // Refresh every 10 seconds to catch new snapshots
    const interval = setInterval(fetchHistory, 10000)
    return () => clearInterval(interval)
  }, [])

  const handleRevert = async (version) => {
    if (!confirm(`Revert to version ${version}? Current state will be saved first.`))
      return

    setReverting(version)
    setMessage('')
    try {
      await axios.post(`${API}/api/revert/${version}`)
      setMessage(`✓ Reverted to version ${version}`)
      fetchHistory()
    } catch (e) {
      setMessage(`✗ Revert failed: ${e.response?.data?.detail || e.message}`)
    } finally {
      setReverting(null)
    }
  }

  const intentColor = (intent) => {
    if (!intent || intent === 'initial') return '#888'
    if (intent === 'revert')            return '#ff9944'
    if (intent.includes('audio'))       return '#4facfe'
    if (intent.includes('video'))       return '#a855f7'
    if (intent.includes('filter') || intent.includes('darker') || intent.includes('brighter'))
      return '#f59e0b'
    if (intent.includes('script'))      return '#4cff88'
    return '#6c63ff'
  }

  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <h3 style={styles.title}>🕒 Version History</h3>
        <button style={styles.refreshBtn} onClick={fetchHistory} disabled={loading}>
          {loading ? '...' : '↻ Refresh'}
        </button>
      </div>

      {message && (
        <div style={{
          ...styles.msgBox,
          background: message.startsWith('✓') ? '#0a2a0a' : '#2a0a0a',
          color:      message.startsWith('✓') ? '#4cff88' : '#ff8888',
        }}>
          {message}
        </div>
      )}

      {history.length === 0 && !loading && (
        <p style={styles.empty}>No versions saved yet. Run the pipeline to create snapshots.</p>
      )}

      <div style={styles.list}>
        {history.map((v) => (
          <div key={v.version} style={styles.versionRow}>
            {/* Version badge */}
            <div style={styles.vBadge}>v{v.version}</div>

            {/* Info */}
            <div style={styles.vInfo}>
              <div style={styles.vDesc}>{v.description}</div>
              <div style={styles.vMeta}>
                <span style={{ color: '#555', fontSize: 11 }}>
                  {v.timestamp.slice(0, 19).replace('T', ' ')}
                </span>
                <span style={{
                  ...styles.intentPill,
                  background: intentColor(v.edit_intent) + '22',
                  color:      intentColor(v.edit_intent),
                }}>
                  {v.edit_intent || 'initial'}
                </span>
                <span style={{ color: '#444', fontSize: 11 }}>
                  {v.asset_count} assets
                </span>
              </div>
            </div>

            {/* Undo button */}
            <button
              style={{
                ...styles.undoBtn,
                opacity: reverting === v.version ? 0.5 : 1,
              }}
              onClick={() => handleRevert(v.version)}
              disabled={reverting !== null}
              title={`Revert to v${v.version}`}
            >
              {reverting === v.version ? '⏳' : '↩ Undo'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

const styles = {
  card: {
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 12, padding: 20,
  },
  header:     { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 },
  title:      { fontSize: 16, fontWeight: 700 },
  refreshBtn: {
    padding: '5px 12px', borderRadius: 6, fontSize: 12,
    border: '1px solid rgba(255,255,255,0.12)',
    background: 'transparent', color: '#aaa', cursor: 'pointer',
  },
  msgBox:  { padding: '8px 12px', borderRadius: 8, fontSize: 13, marginBottom: 12 },
  empty:   { color: '#555', fontSize: 13, textAlign: 'center', padding: '20px 0' },
  list:    { display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 400, overflowY: 'auto' },
  versionRow: {
    display: 'flex', alignItems: 'center', gap: 12,
    padding: '10px 12px', borderRadius: 8,
    background: 'rgba(255,255,255,0.02)',
    border: '1px solid rgba(255,255,255,0.05)',
  },
  vBadge: {
    fontSize: 13, fontWeight: 700, color: '#6c63ff',
    background: '#6c63ff22', padding: '4px 10px',
    borderRadius: 8, whiteSpace: 'nowrap',
  },
  vInfo:  { flex: 1, minWidth: 0 },
  vDesc:  { fontSize: 13, color: '#ddd', marginBottom: 4, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
  vMeta:  { display: 'flex', gap: 10, alignItems: 'center' },
  intentPill: {
    fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 10,
  },
  undoBtn: {
    padding: '5px 12px', borderRadius: 6, fontSize: 12,
    border: '1px solid rgba(255,100,100,0.3)',
    background: 'rgba(255,100,100,0.08)',
    color: '#ff9999', cursor: 'pointer', whiteSpace: 'nowrap',
    transition: 'all 0.2s',
  },
}
