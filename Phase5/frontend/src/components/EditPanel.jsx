import { useState } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

const EXAMPLE_QUERIES = [
  "Change voice tone to whispered for scene 1",
  "Apply sepia filter to scene 2",
  "Make scene 3 darker",
  "Add background music to all scenes",
  "Speed up scene 1 by 1.5x",
  "Remove the subtitle",
  "Apply grayscale filter to all scenes",
]

export default function EditPanel({ onEditDone }) {
  const [query,   setQuery]   = useState('')
  const [loading, setLoading] = useState(false)
  const [result,  setResult]  = useState(null)
  const [error,   setError]   = useState('')

  const handleEdit = async () => {
    if (!query.trim()) return
    setLoading(true)
    setResult(null)
    setError('')

    try {
      const res = await axios.post(`${API}/api/edit`, { query })
      setResult(res.data)
      if (onEditDone) onEditDone()
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.card}>
      <h3 style={styles.title}>✂️ Edit Agent</h3>
      <p style={styles.hint}>
        Describe an edit in plain English. The AI will classify your intent
        and apply the change automatically.
      </p>

      {/* Example queries */}
      <div style={styles.examples}>
        {EXAMPLE_QUERIES.map((q, i) => (
          <button
            key={i}
            style={styles.exampleBtn}
            onClick={() => setQuery(q)}
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input */}
      <div style={styles.inputRow}>
        <input
          style={styles.input}
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleEdit()}
          placeholder="e.g. Make scene 2 darker..."
          disabled={loading}
        />
        <button
          style={{
            ...styles.btn,
            opacity: loading || !query.trim() ? 0.5 : 1,
            cursor:  loading || !query.trim() ? 'not-allowed' : 'pointer',
          }}
          onClick={handleEdit}
          disabled={loading || !query.trim()}
        >
          {loading ? '⏳' : '▶ Apply'}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div style={{
          ...styles.resultBox,
          borderColor: result.ok ? '#4cff8844' : '#ff666644',
          background:  result.ok ? '#0a2a0a' : '#2a0a0a',
        }}>
          <div style={styles.resultHeader}>
            <span>{result.ok ? '✓' : '✗'} {result.ok ? 'Edit applied' : 'Edit failed'}</span>
            {result.version > 0 && (
              <span style={styles.versionBadge}>v{result.version}</span>
            )}
          </div>

          {result.intent?.intent && (
            <div style={styles.intentRow}>
              <span style={styles.intentTag}>intent</span>
              <code>{result.intent.intent}</code>
              <span style={styles.intentTag}>target</span>
              <code>{result.intent.target}</code>
              <span style={styles.intentTag}>scope</span>
              <code>{result.intent.scope}</code>
            </div>
          )}

          {result.result && (
            <p style={{ fontSize: 13, color: '#aaa', marginTop: 6 }}>
              {result.result}
            </p>
          )}
          {result.error && (
            <p style={{ fontSize: 13, color: '#ff8888', marginTop: 6 }}>
              {result.error}
            </p>
          )}
        </div>
      )}

      {error && (
        <div style={{ ...styles.resultBox, borderColor: '#ff666644', background: '#2a0a0a' }}>
          <p style={{ color: '#ff8888', fontSize: 13 }}>✗ {error}</p>
        </div>
      )}
    </div>
  )
}

const styles = {
  card: {
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 12, padding: 20,
  },
  title:   { fontSize: 16, fontWeight: 700, marginBottom: 6 },
  hint:    { fontSize: 13, color: '#888', marginBottom: 14, lineHeight: 1.5 },
  examples: { display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 },
  exampleBtn: {
    padding: '4px 10px', borderRadius: 6, fontSize: 11,
    border: '1px solid rgba(255,255,255,0.12)',
    background: 'transparent', color: '#aaa',
    cursor: 'pointer', transition: 'all 0.2s',
  },
  inputRow:  { display: 'flex', gap: 8 },
  input: {
    flex: 1, padding: '10px 14px', borderRadius: 8,
    background: 'rgba(0,0,0,0.3)',
    border: '1px solid rgba(255,255,255,0.12)',
    color: '#e0e0f0', fontSize: 14, fontFamily: 'inherit', outline: 'none',
  },
  btn: {
    padding: '10px 18px', borderRadius: 8, border: 'none',
    background: 'linear-gradient(135deg, #6c63ff, #4facfe)',
    color: '#fff', fontWeight: 700, fontSize: 14, transition: 'all 0.2s',
  },
  resultBox: {
    marginTop: 14, padding: 14, borderRadius: 8,
    border: '1px solid', fontSize: 13,
  },
  resultHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontWeight: 600 },
  versionBadge: {
    background: '#6c63ff33', color: '#6c63ff',
    padding: '2px 8px', borderRadius: 10, fontSize: 12, fontWeight: 700,
  },
  intentRow: { display: 'flex', gap: 8, alignItems: 'center', marginTop: 8, flexWrap: 'wrap' },
  intentTag: {
    fontSize: 10, fontWeight: 700, textTransform: 'uppercase',
    color: '#666', letterSpacing: 1,
  },
}
