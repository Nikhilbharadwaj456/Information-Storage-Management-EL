import { useState } from 'react'
import { Save, SlidersHorizontal } from 'lucide-react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { apiRequest } from '../services/api'
import { ExplanationPanel, type Explanation } from '../components/ExplanationPanel'
import { QuickStartGuide } from '../components/QuickStartGuide'

type DiskResult = {
  rotational_latency_ms: number
  transfer_time_ms: number
  service_time_ms: number
  estimated_iops: number
  utilization: number
  utilization_percent: number
  response_time_ms: number
  requests_in_system: number
  response_curve: Array<{ 'Utilization (%)': number; 'Average response time (ms)': number }>
  assumptions: string[]
  explanation: Explanation
}

export function DiskPage() {
  const [rpm, setRpm] = useState(7200)
  const [seek, setSeek] = useState(4)
  const [transfer, setTransfer] = useState(150)
  const [block, setBlock] = useState(4)
  const [arrival, setArrival] = useState(100)
  const [result, setResult] = useState<DiskResult | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')

  const calculate = async () => {
    setError('')
    setSaved('')
    try {
      const data = await apiRequest<DiskResult>('/api/disk/analyze', {
        method: 'POST',
        body: JSON.stringify({
          rpm,
          seek_ms: seek,
          transfer_rate_mb_s: transfer,
          block_kb: block,
          arrival_iops: arrival,
        }),
      })
      setResult(data)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to analyze disk performance.')
    }
  }

  const save = async () => {
    if (!result) return setError('Calculate disk performance before saving.')
    try {
      await apiRequest('/api/scenarios', {
        method: 'POST',
        body: JSON.stringify({
          name: `${rpm} RPM Disk - ${arrival} IOPS`,
          module_type: 'disk',
          inputs: { rpm, seek_ms: seek, transfer_rate_mb_s: transfer, block_kb: block, arrival_iops: arrival },
          results: result,
          assumptions: result.assumptions,
          tags: ['disk'],
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
        <div><p className="eyebrow">Latency and queueing</p><h1>Disk Performance Analyzer</h1></div>
        <button type="button" className="primary-button" onClick={save}><Save size={16} /> Save scenario</button>
      </div>
      <div className="workspace-grid">
        <aside className="control-panel">
          <QuickStartGuide steps={[
            { title: 'Enter disk specifications', description: 'Set RPM, seek time, transfer rate, and block size.' },
            { title: 'Set workload', description: 'Enter the expected arrival rate in IOPS.' },
            { title: 'Analyze', description: 'Check utilization before using the response-time results.' },
          ]} />
          <div className="panel-heading"><div><p className="eyebrow">Parameters</p><h2>Disk configuration</h2></div></div>
          <label className="field"><span>Disk RPM</span><input type="number" min="1" value={rpm} onChange={(e) => setRpm(Number(e.target.value))} /></label>
          <label className="field"><span>Seek time (ms)</span><input type="number" min="0" step="0.1" value={seek} onChange={(e) => setSeek(Number(e.target.value))} /></label>
          <label className="field"><span>Transfer rate (MB/s)</span><input type="number" min="0.1" value={transfer} onChange={(e) => setTransfer(Number(e.target.value))} /></label>
          <label className="field"><span>Block size (KB)</span><input type="number" min="0.1" value={block} onChange={(e) => setBlock(Number(e.target.value))} /></label>
          <label className="field"><span>Arrival rate (IOPS)</span><input type="number" min="0" value={arrival} onChange={(e) => setArrival(Number(e.target.value))} /></label>
          <button type="button" className="calculate-button" onClick={calculate}><SlidersHorizontal size={17} /> Analyze disk</button>
          {error && <div className="notice error-notice" role="alert">{error}</div>}
          {saved && <div className="notice success-notice" role="status">{saved}</div>}
        </aside>
        <div className="results-column">
          {result ? (
            <>
              <div className="metric-grid five-metrics">
                <article className="metric-card"><p>Rotational latency</p><strong>{result.rotational_latency_ms.toFixed(3)} ms</strong></article>
                <article className="metric-card"><p>Transfer time</p><strong>{result.transfer_time_ms.toFixed(3)} ms</strong></article>
                <article className="metric-card"><p>Service time</p><strong>{result.service_time_ms.toFixed(3)} ms</strong></article>
                <article className="metric-card"><p>Estimated IOPS</p><strong>{result.estimated_iops.toFixed(1)}</strong></article>
                <article className="metric-card"><p>Utilization</p><strong>{result.utilization_percent.toFixed(1)}%</strong></article>
              </div>
              <article className="panel">
                <div className="panel-heading"><div><p className="eyebrow">M/M/1 queue model</p><h2>Average response time</h2></div></div>
                <div className="chart-wrap">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={result.response_curve}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="Utilization (%)" type="number" domain={[5, 95]} tickFormatter={(v) => `${v}%`} />
                      <YAxis tickFormatter={(v) => `${v} ms`} />
                      <Tooltip formatter={(v) => [`${Number(v).toFixed(3)} ms`, 'Response']} />
                      <Line type="monotone" dataKey="Average response time (ms)" stroke="#5b72ee" strokeWidth={3} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </article>
              <div className="metric-grid">
                <article className="metric-card"><p>Average response</p><strong>{result.response_time_ms.toFixed(3)} ms</strong></article>
                <article className="metric-card"><p>Requests in system</p><strong>{result.requests_in_system.toFixed(3)}</strong></article>
                <article className="metric-card"><p>Little's Law</p><strong>L = λW</strong><small>{arrival} IOPS × {result.response_time_ms.toFixed(3)} ms</small></article>
                <article className="metric-card"><p>System state</p><strong>{result.utilization_percent >= 80 ? 'High utilization' : 'Stable'}</strong></article>
              </div>
              <ExplanationPanel explanation={result.explanation} />
            </>
          ) : (
            <div className="module-empty"><SlidersHorizontal size={30} /><h2>Analyze a disk workload</h2><p>Enter RPM, seek, transfer, block, and arrival parameters.</p></div>
          )}
        </div>
      </div>
    </section>
  )
}
