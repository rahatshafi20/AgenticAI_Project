export default function PromptForm({ prompt, setPrompt, onRunAll, running }) {
  return (
    <div style={styles.card}>
      <h2 style={styles.title}>✨ Story Prompt</h2>
      <p style={styles.hint}>
        Describe your short film idea. The AI will generate the full story,
        voices, visuals, and video automatically.
      </p>

      <textarea
        style={styles.textarea}
        value={prompt}
        onChange={e => setPrompt(e.target.value)}
        placeholder="e.g. A young astronaut discovers a hidden ocean on Mars and must decide whether to tell the world..."
        rows={5}
        disabled={running}
      />

      <div style={styles.actions}>
        <button
          style={{ ...styles.btn, ...(running ? styles.btnDisabled : styles.btnPrimary) }}
          onClick={onRunAll}
          disabled={running || !prompt.trim()}
        >
          {running ? '⏳ Pipeline Running...' : '🚀 Generate Full Video'}
        </button>
        <span style={styles.charCount}>{prompt.length} chars</span>
      </div>

      {running && (
        <div style={styles.progressBar}>
          <div style={styles.progressFill} />
        </div>
      )}
    </div>
  )
}

const styles = {
  card: {
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 14, padding: 20,
  },
  title:    { fontSize: 18, fontWeight: 700, marginBottom: 8 },
  hint:     { fontSize: 13, color: '#999', marginBottom: 14, lineHeight: 1.5 },
  textarea: {
    width: '100%', background: 'rgba(0,0,0,0.3)',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: 8, padding: 12, color: '#e0e0f0',
    fontSize: 14, resize: 'vertical', fontFamily: 'inherit',
    outline: 'none',
  },
  actions:      { display: 'flex', alignItems: 'center', gap: 12, marginTop: 12 },
  btn:          { padding: '10px 20px', borderRadius: 8, border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: 14, transition: 'all 0.2s' },
  btnPrimary:   { background: 'linear-gradient(135deg, #6c63ff, #4facfe)', color: '#fff' },
  btnDisabled:  { background: '#333', color: '#666', cursor: 'not-allowed' },
  charCount:    { fontSize: 12, color: '#555' },
  progressBar:  { marginTop: 14, height: 3, background: '#222', borderRadius: 3, overflow: 'hidden' },
  progressFill: {
    height: '100%', width: '60%',
    background: 'linear-gradient(90deg, #6c63ff, #4facfe)',
    animation: 'slide 1.5s infinite',
    borderRadius: 3,
  },
}
