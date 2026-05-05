export default function VideoPlayer({ ready, apiBase }) {
  if (!ready) {
    return (
      <div style={styles.placeholder}>
        <div style={styles.placeholderIcon}>🎬</div>
        <p style={styles.placeholderText}>
          Your generated video will appear here once Phase 3 completes.
        </p>
        <p style={styles.placeholderHint}>
          Run the pipeline using the prompt form on the left.
        </p>
      </div>
    )
  }

  return (
    <div style={styles.playerCard}>
      <div style={styles.playerHeader}>
        <h3 style={styles.playerTitle}>🎥 Final Output</h3>
        <a
          href={`${apiBase}/api/video`}
          download="final_output.mp4"
          style={styles.downloadBtn}
        >
          ⬇ Download MP4
        </a>
      </div>

      <video
        key={Date.now()}   // force reload when video updates
        controls
        style={styles.video}
        src={`${apiBase}/api/video/stream`}
      >
        Your browser does not support the video tag.
      </video>

      <p style={styles.hint}>
        ✓ Video ready — click play or download the MP4 file.
      </p>
    </div>
  )
}

const styles = {
  placeholder: {
    background: 'rgba(255,255,255,0.02)',
    border: '2px dashed rgba(255,255,255,0.1)',
    borderRadius: 14, padding: 60,
    display: 'flex', flexDirection: 'column',
    alignItems: 'center', textAlign: 'center', gap: 12,
  },
  placeholderIcon: { fontSize: 64 },
  placeholderText: { fontSize: 16, color: '#aaa', maxWidth: 300 },
  placeholderHint: { fontSize: 13, color: '#555' },

  playerCard: {
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: 14, padding: 20,
  },
  playerHeader: {
    display: 'flex', justifyContent: 'space-between',
    alignItems: 'center', marginBottom: 16,
  },
  playerTitle: { fontSize: 18, fontWeight: 700 },
  downloadBtn: {
    padding: '8px 18px', borderRadius: 8,
    background: 'linear-gradient(135deg, #6c63ff, #4facfe)',
    color: '#fff', textDecoration: 'none',
    fontSize: 14, fontWeight: 600,
  },
  video: {
    width: '100%', borderRadius: 10,
    background: '#000', maxHeight: 450,
  },
  hint: { fontSize: 12, color: '#4cff88', marginTop: 10 },
}
