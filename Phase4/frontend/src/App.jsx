import { useState, useEffect, useRef, useCallback } from 'react'
import axios from 'axios'
import PromptForm   from './components/PromptForm'
import PhaseCard    from './components/PhaseCard'
import VideoPlayer  from './components/VideoPlayer'

const API = 'http://localhost:8000'
const WS  = 'ws://localhost:8000/ws'

const PHASE_INFO = {
  1: { label: 'Phase 1',  name: 'Story & Script',    icon: '📝' },
  2: { label: 'Phase 2',  name: 'Audio Generation',  icon: '🎙️' },
  3: { label: 'Phase 3',  name: 'Video Composition', icon: '🎬' },
  4: { label: 'Phase 4',  name: 'Web Interface',     icon: '🌐' },
  5: { label: 'Phase 5',  name: 'Edit & Undo Agent', icon: '✂️' },
}

const defaultPhases = Object.fromEntries(
  Object.keys(PHASE_INFO).map(k => [k, {
    status: 'pending', percent: 0, message: '',
    name: PHASE_INFO[k].name,
  }])
)

export default function App() {
  const [prompt,       setPrompt]       = useState('')
  const [phases,       setPhases]       = useState(defaultPhases)
  const [runningPhase, setRunningPhase] = useState(null)
  const [videoReady,   setVideoReady]   = useState(false)
  const [wsStatus,     setWsStatus]     = useState('connecting')
  const [logs,         setLogs]         = useState([])
  const wsRef = useRef(null)

  // ── WebSocket connection ──────────────────────────────────────
  const connectWS = useCallback(() => {
    const ws = new WebSocket(WS)
    wsRef.current = ws

    ws.onopen  = () => setWsStatus('connected')
    ws.onclose = () => {
      setWsStatus('disconnected')
      setTimeout(connectWS, 3000)   // auto-reconnect
    }
    ws.onerror = () => setWsStatus('error')

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)

      if (data.type === 'init') {
        // Full state sync on connect
        const state = data.state
        setPrompt(state.prompt || '')
        setRunningPhase(state.running_phase)
        if (state.phases) {
          setPhases(prev => {
            const next = { ...prev }
            Object.entries(state.phases).forEach(([k, v]) => {
              next[k] = { ...next[k], ...v }
            })
            return next
          })
        }
        if (state.final_video) setVideoReady(true)
        return
      }

      // Phase progress event
      const { phase, status, message, percent } = data
      setPhases(prev => ({
        ...prev,
        [phase]: { ...prev[phase], status, message, percent },
      }))
      setRunningPhase(status === 'running' ? phase : null)
      if (phase === 3 && status === 'done') setVideoReady(true)

      // Add to log
      setLogs(prev => [
        { time: new Date().toLocaleTimeString(), phase, status, message },
        ...prev.slice(0, 49),   // keep last 50
      ])
    }
  }, [])

  useEffect(() => {
    connectWS()
    return () => wsRef.current?.close()
  }, [connectWS])

  // ── Actions ───────────────────────────────────────────────────
  const handleRunAll = async () => {
    if (!prompt.trim()) return alert('Enter a story prompt first.')
    await axios.post(`${API}/api/prompt`, { prompt })
    await axios.post(`${API}/api/run/all`)
  }

  const handleRunPhase = async (phase) => {
    if (runningPhase) return alert(`Phase ${runningPhase} is still running.`)
    await axios.post(`${API}/api/prompt`, { prompt })
    await axios.post(`${API}/api/run/${phase}`)
  }

  // ── Render ────────────────────────────────────────────────────
  return (
    <div style={styles.app}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerInner}>
          <span style={styles.logo}>🎬</span>
          <div>
            <h1 style={styles.title}>Project Montage</h1>
            <p style={styles.subtitle}>AI-Powered Animated Video Generation</p>
          </div>
          <div style={{
            ...styles.wsBadge,
            background: wsStatus === 'connected' ? '#1a4a1a' : '#4a1a1a',
            color:      wsStatus === 'connected' ? '#4cff88' : '#ff6666',
          }}>
            {wsStatus === 'connected' ? '● Live' : '● Disconnected'}
          </div>
        </div>
      </header>

      <main style={styles.main}>
        {/* Left column: prompt + phases */}
        <div style={styles.leftCol}>
          <PromptForm
            prompt={prompt}
            setPrompt={setPrompt}
            onRunAll={handleRunAll}
            running={runningPhase !== null}
          />

          <div style={styles.phasesGrid}>
            {Object.entries(PHASE_INFO).map(([num, info]) => (
              <PhaseCard
                key={num}
                phaseNum={parseInt(num)}
                info={info}
                state={phases[num]}
                running={runningPhase === parseInt(num)}
                disabled={runningPhase !== null && runningPhase !== parseInt(num)}
                onRerun={() => handleRunPhase(parseInt(num))}
              />
            ))}
          </div>
        </div>

        {/* Right column: video + logs */}
        <div style={styles.rightCol}>
          <VideoPlayer
            ready={videoReady}
            apiBase={API}
          />

          <div style={styles.logBox}>
            <h3 style={styles.logTitle}>📋 Live Log</h3>
            <div style={styles.logScroll}>
              {logs.length === 0 && (
                <p style={{ color: '#666', fontSize: 13 }}>
                  Waiting for pipeline events...
                </p>
              )}
              {logs.map((log, i) => (
                <div key={i} style={styles.logEntry}>
                  <span style={{ color: '#888', fontSize: 11 }}>{log.time}</span>
                  <span style={{
                    color: log.status === 'error' ? '#ff6666'
                         : log.status === 'done'  ? '#4cff88'
                         : '#88aaff',
                    fontSize: 12, marginLeft: 8,
                  }}>
                    [Phase {log.phase}] {log.message}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

// ── Styles ────────────────────────────────────────────────────────────────
const styles = {
  app: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%)',
    color: '#e0e0f0',
  },
  header: {
    background: 'rgba(255,255,255,0.04)',
    borderBottom: '1px solid rgba(255,255,255,0.08)',
    padding: '16px 32px',
  },
  headerInner: {
    display: 'flex', alignItems: 'center', gap: 16, maxWidth: 1400, margin: '0 auto',
  },
  logo:     { fontSize: 36 },
  title:    { fontSize: 24, fontWeight: 700, color: '#fff' },
  subtitle: { fontSize: 13, color: '#888', marginTop: 2 },
  wsBadge:  {
    marginLeft: 'auto', padding: '6px 14px',
    borderRadius: 20, fontSize: 13, fontWeight: 600,
  },
  main: {
    display: 'flex', gap: 24, padding: '24px 32px',
    maxWidth: 1400, margin: '0 auto',
  },
  leftCol:    { flex: '0 0 480px', display: 'flex', flexDirection: 'column', gap: 20 },
  rightCol:   { flex: 1, display: 'flex', flexDirection: 'column', gap: 20 },
  phasesGrid: { display: 'flex', flexDirection: 'column', gap: 10 },
  logBox: {
    background: 'rgba(0,0,0,0.4)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: 12, padding: 16,
  },
  logTitle:  { fontSize: 14, fontWeight: 600, marginBottom: 10, color: '#aaa' },
  logScroll: { height: 200, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 4 },
  logEntry:  { display: 'flex', alignItems: 'flex-start' },
}
