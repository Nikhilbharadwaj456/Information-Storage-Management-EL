import { useState } from 'react'
import { BarChart3, Save } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { apiRequest } from '../services/api'
import { ExplanationPanel, type Explanation } from '../components/ExplanationPanel'
import { QuickStartGuide } from '../components/QuickStartGuide'

type Strategy = {
  Strategy: string
  'Storage (GB)': number
  'Backup duration (hours)': number
  'Restore duration (hours)': number
  'Recovery steps': number
  'Restore data (GB)': number
  'RPO compliant': string
  'RTO compliant': string
}

type BackupResult = {
  strategies: Strategy[]
  recommendation: string
  backup_interval_hours: number
  rpo_hours: number
  rto_hours: number
  assumptions: string[]
  explanation: Explanation
}

export function BackupPage() {
  const [dataSize, setDataSize] = useState(1000)
  const [change, setChange] = useState(5)
  const [retention, setRetention] = useState(7)
  const [throughput, setThroughput] = useState(100)
  const [frequency, setFrequency] = useState('Daily')
  const [rpo, setRpo] = useState(24)
  const [rto, setRto] = useState(4)
  const [result, setResult] = useState<BackupResult | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')

  const interval = { Hourly: 1, Daily: 24, Weekly: 168 }[frequency]

  const calculate = async () => {
    setError('')
    setSaved('')
    try {
      const data = await apiRequest<BackupResult>('/api/backup/compare', {
        method: 'POST',
        body: JSON.stringify({
          data_size_gb: dataSize,
          change_percent: change,
          retention_days: retention,
          throughput_mb_s: throughput,
          rpo_hours: rpo,
          rto_hours: rto,
          backup_interval_hours: interval,
        }),
      })
      setResult(data)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to compare backup strategies.')
    }
  }

  const save = async () => {
    if (!result) return setError('Calculate backup strategies before saving.')
    try {
      await apiRequest('/api/scenarios', {
        method: 'POST',
        body: JSON.stringify({
          name: `${frequency} Backup - ${dataSize} GB`,
          module_type: 'backup',
          inputs: { data_size_gb: dataSize, change_percent: change, retention_days: retention, throughput_mb_s: throughput, backup_frequency: frequency, rpo_hours: rpo, rto_hours: rto },
          results: result,
          assumptions: result.assumptions,
          tags: ['backup'],
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
        <div><p className="eyebrow">Protection and recovery</p><h1>Backup Strategy Planner</h1></div>
        <button type="button" className="primary-button" onClick={save}><Save size={16} /> Save scenario</button>
      </div>
      <div className="workspace-grid">
        <aside className="control-panel">
          <QuickStartGuide steps={[
            { title: 'Describe the data', description: 'Enter dataset size, daily change, and retention.' },
            { title: 'Set recovery targets', description: 'Enter backup throughput, frequency, RPO, and RTO.' },
            { title: 'Compare', description: 'Choose the strategy that meets both objectives and capacity needs.' },
          ]} />
          <label className="field"><span>Original data (GB)</span><input type="number" min="1" value={dataSize} onChange={(e) => setDataSize(Number(e.target.value))} /></label>
          <label className="field"><span>Daily change (%)</span><input type="number" min="0" max="100" value={change} onChange={(e) => setChange(Number(e.target.value))} /></label>
          <label className="field"><span>Retention (days)</span><input type="number" min="1" max="365" value={retention} onChange={(e) => setRetention(Number(e.target.value))} /></label>
          <label className="field"><span>Throughput (MB/s)</span><input type="number" min="0.1" value={throughput} onChange={(e) => setThroughput(Number(e.target.value))} /></label>
          <label className="field"><span>Backup frequency</span><select value={frequency} onChange={(e) => setFrequency(e.target.value)}><option>Hourly</option><option>Daily</option><option>Weekly</option></select></label>
          <label className="field"><span>Required RPO (hours)</span><input type="number" min="0.1" value={rpo} onChange={(e) => setRpo(Number(e.target.value))} /></label>
          <label className="field"><span>Required RTO (hours)</span><input type="number" min="0.1" value={rto} onChange={(e) => setRto(Number(e.target.value))} /></label>
          <button type="button" className="calculate-button" onClick={calculate}><BarChart3 size={17} /> Compare strategies</button>
          {error && <div className="notice error-notice" role="alert">{error}</div>}
          {saved && <div className="notice success-notice" role="status">{saved}</div>}
        </aside>
        <div className="results-column">
          {result ? (
            <>
              <div className="analysis-grid">
                <article className="panel">
                  <div className="panel-heading"><div><p className="eyebrow">Retained storage</p><h2>Storage comparison</h2></div></div>
                  <div className="chart-wrap">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={result.strategies} margin={{ top: 10, right: 8 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="Strategy" /><YAxis width={72} tickFormatter={(v) => `${v} GB`} />
                        <Tooltip formatter={(v) => [`${Number(v).toFixed(1)} GB`, 'Storage']} />
                        <Bar dataKey="Storage (GB)" fill="#6366f1" radius={[6, 6, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </article>
                <article className="panel">
                  <div className="panel-heading"><div><p className="eyebrow">Recovery objectives</p><h2>RPO / RTO</h2></div></div>
                  <div className="objective-stack">
                    <div><span>Backup interval</span><strong>{interval} h</strong><small>RPO {rpo} h</small></div>
                    <div><span>Fastest restore</span><strong>{Math.min(...result.strategies.map((item) => item['Restore duration (hours)'])).toFixed(2)} h</strong><small>RTO {rto} h</small></div>
                  </div>
                </article>
              </div>
              <article className="panel data-panel">
                <div className="panel-heading"><div><p className="eyebrow">Strategy details</p><h2>Backup and restore comparison</h2></div></div>
                <div className="layout-table-wrap">
                  <table className="layout-table backup-table">
                    <thead><tr><th>Strategy</th><th>Storage retained</th><th>Backup window</th><th>Restore time</th><th>Data restored</th><th>Restore steps</th><th>RPO</th><th>RTO</th></tr></thead>
                    <tbody>
                      {result.strategies.map((item) => (
                        <tr key={item.Strategy}>
                          <td><strong>{item.Strategy}</strong></td>
                          <td>{item['Storage (GB)'].toFixed(1)} GB</td>
                          <td>{item['Backup duration (hours)'].toFixed(2)} h</td>
                          <td>{item['Restore duration (hours)'].toFixed(2)} h</td>
                          <td>{item['Restore data (GB)'].toFixed(1)} GB</td>
                          <td>{item['Recovery steps']}</td>
                          <td><span className={`compliance ${item['RPO compliant'] === 'Yes' ? 'pass' : 'fail'}`}>{item['RPO compliant']}</span></td>
                          <td><span className={`compliance ${item['RTO compliant'] === 'Yes' ? 'pass' : 'fail'}`}>{item['RTO compliant']}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="layout-note">
                  Restore steps: Full restores 1 backup. Incremental restores the full backup, then every incremental in order.
                  Differential restores the full backup plus only the latest differential.
                  Backup window is the largest single backup in the retention period.
                </p>
              </article>
              <article className="interpretation-panel"><div><p className="eyebrow">Recommendation</p><h2>{result.recommendation}</h2></div></article>
              <ExplanationPanel explanation={result.explanation} />
            </>
          ) : (
            <div className="module-empty"><BarChart3 size={30} /><h2>Compare backup strategies</h2><p>Enter data size, change rate, retention, throughput, RPO, and RTO.</p></div>
          )}
        </div>
      </div>
    </section>
  )
}
