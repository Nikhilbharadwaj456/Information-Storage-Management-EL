import { useState } from 'react'
import { Save, Waypoints } from 'lucide-react'

import { apiRequest } from '../services/api'
import { ExplanationPanel, type Explanation } from '../components/ExplanationPanel'
import { QuickStartGuide } from '../components/QuickStartGuide'

type ReplicationMode = {
  mode: string
  response_ms: number
  lag_ms: number
  data_loss: string
}

type ReplicationResult = {
  selected: ReplicationMode
  comparison: ReplicationMode[]
  assumptions: string[]
  explanation: Explanation
}

export function ReplicationPage() {
  const [mode, setMode] = useState('Synchronous')
  const [latency, setLatency] = useState(20)
  const [localWrite, setLocalWrite] = useState(2)
  const [bandwidth, setBandwidth] = useState(1000)
  const [frequency, setFrequency] = useState(500)
  const [result, setResult] = useState<ReplicationResult | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')

  const calculate = async () => {
    setError('')
    setSaved('')
    try {
      const data = await apiRequest<ReplicationResult>('/api/replication/compare', {
        method: 'POST',
        body: JSON.stringify({
          mode,
          local_write_ms: localWrite,
          network_round_trip_ms: latency,
          bandwidth_mbps: bandwidth,
          write_frequency_iops: frequency,
        }),
      })
      setResult(data)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to compare replication modes.')
    }
  }

  const save = async () => {
    if (!result) return setError('Calculate replication before saving.')
    try {
      await apiRequest('/api/scenarios', {
        method: 'POST',
        body: JSON.stringify({
          name: `${mode} Replication - ${latency} ms RTT`,
          module_type: 'replication',
          inputs: { mode, local_write_ms: localWrite, network_round_trip_ms: latency, bandwidth_mbps: bandwidth, write_frequency_iops: frequency },
          results: result,
          assumptions: result.assumptions,
          tags: ['replication'],
        }),
      })
      setSaved('Scenario saved')
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to save scenario.')
    }
  }

  return (
    <section className="page module-page">
      <div className="page-heading">
        <div><p className="eyebrow">Remote copy behavior</p><h1>Replication Simulator</h1></div>
        <button type="button" className="primary-button" onClick={save}><Save size={16} /> Save scenario</button>
      </div>
      <div className="workspace-grid">
        <aside className="control-panel">
          <QuickStartGuide steps={[
            { title: 'Choose a mode', description: 'Compare local acknowledgement with remote acknowledgement.' },
            { title: 'Enter network details', description: 'Set RTT, bandwidth, local write time, and write frequency.' },
            { title: 'Compare', description: 'Balance response time against replication lag and data-loss risk.' },
          ]} />
          <label className="field"><span>Replication mode</span><select value={mode} onChange={(e) => setMode(e.target.value)}><option>Synchronous</option><option>Asynchronous</option></select></label>
          <label className="field"><span>Network RTT (ms)</span><input type="number" min="0" value={latency} onChange={(e) => setLatency(Number(e.target.value))} /></label>
          <label className="field"><span>Local write (ms)</span><input type="number" min="0" value={localWrite} onChange={(e) => setLocalWrite(Number(e.target.value))} /></label>
          <label className="field"><span>Bandwidth (Mbps)</span><input type="number" min="0.1" value={bandwidth} onChange={(e) => setBandwidth(Number(e.target.value))} /></label>
          <label className="field"><span>Write frequency (IOPS)</span><input type="number" min="0" value={frequency} onChange={(e) => setFrequency(Number(e.target.value))} /></label>
          <button type="button" className="calculate-button" onClick={calculate}><Waypoints size={17} /> Compare replication</button>
          {error && <div className="notice error-notice" role="alert">{error}</div>}
          {saved && <div className="notice success-notice" role="status">{saved}</div>}
        </aside>
        <div className="results-column">
          {result ? (
            <>
              <div className="metric-grid">
                {result.comparison.map((item) => (
                  <article className="metric-card" key={item.mode}>
                    <p>{item.mode}</p>
                    <strong>{item.response_ms.toFixed(2)} ms</strong>
                    <small>{item.lag_ms.toFixed(2)} ms replication lag</small>
                  </article>
                ))}
              </div>
              <article className="panel data-panel">
                <div className="panel-heading"><div><p className="eyebrow">Replication comparison</p><h2>Response and lag</h2></div></div>
                <div className="layout-table-wrap">
                  <table className="layout-table backup-table">
                    <thead><tr><th>Mode</th><th>Write response</th><th>Replication lag</th><th>Data-loss window</th></tr></thead>
                    <tbody>{result.comparison.map((item) => <tr key={item.mode}><td><strong>{item.mode}</strong></td><td>{item.response_ms.toFixed(2)} ms</td><td>{item.lag_ms.toFixed(2)} ms</td><td>{item.data_loss}</td></tr>)}</tbody>
                  </table>
                </div>
              </article>
              <article className="interpretation-panel"><div><p className="eyebrow">Selected model</p><h2>{mode}</h2><p>{result.selected.data_loss}</p></div></article>
              <ExplanationPanel explanation={result.explanation} />
            </>
          ) : (
            <div className="module-empty"><Waypoints size={30} /><h2>Compare replication modes</h2><p>Configure network, write, and acknowledgement assumptions.</p></div>
          )}
        </div>
      </div>
    </section>
  )
}
