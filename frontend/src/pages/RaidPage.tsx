import { useMemo, useState } from 'react'
import { RotateCcw, Save, ShieldAlert, Wrench } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { apiRequest } from '../services/api'
import { ExplanationPanel, type Explanation } from '../components/ExplanationPanel'
import { QuickStartGuide } from '../components/QuickStartGuide'

type RaidResult = {
  level: string
  disk_count: number
  disk_size_tb: number
  raw_capacity_tb: number
  usable_capacity_tb: number
  efficiency_percent: number
  fault_tolerance: number | string
  read_performance: string
  write_performance: string
  array_state: string
  failed_disks: number[]
  rebuild_time_hours: number
  hot_spare_active: boolean
  layout: Array<Record<string, string | number>>
  xor_example: {
    a: string
    b: string
    c: string
    parity: string
    recovered_c: string
  }
  assumptions: string[]
  explanation: Explanation
}

const parityClass = (value: string | number) => {
  const text = String(value)
  if (text === 'FAILED') return 'disk-cell failed'
  if (text.startsWith('P') || text.startsWith('Q')) return 'disk-cell parity'
  return 'disk-cell data'
}

export function RaidPage() {
  const [raidLevel, setRaidLevel] = useState('RAID 5')
  const [diskCount, setDiskCount] = useState(4)
  const [diskSize, setDiskSize] = useState(1)
  const [rebuildThroughput, setRebuildThroughput] = useState(200)
  const [hotSpare, setHotSpare] = useState(false)
  const [failedDisks, setFailedDisks] = useState<number[]>([])
  const [result, setResult] = useState<RaidResult | null>(null)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState('')

  const raidCompare = useMemo(() => (
    ['RAID 0', 'RAID 1', 'RAID 5', 'RAID 6', 'RAID 10'].map((level) => {
      let usable = 0
      if (level === 'RAID 0') usable = diskCount * diskSize
      if (level === 'RAID 1' || level === 'RAID 10') usable = diskCount / 2 * diskSize
      if (level === 'RAID 5') usable = (diskCount - 1) * diskSize
      if (level === 'RAID 6') usable = (diskCount - 2) * diskSize
      return {
        raid: level,
        efficiency: diskCount ? usable / (diskCount * diskSize) * 100 : 0,
      }
    })
  ), [diskCount, diskSize])

  const calculate = async () => {
    setError('')
    setSaved('')
    try {
      const data = await apiRequest<RaidResult>('/api/raid/simulate-failure', {
        method: 'POST',
        body: JSON.stringify({
          raid_level: raidLevel,
          disk_count: diskCount,
          disk_size_tb: diskSize,
          failed_disks: failedDisks,
          hot_spare: hotSpare,
          rebuild_throughput_mb_s: rebuildThroughput,
        }),
      })
      setResult(data)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to calculate RAID configuration.')
    }
  }

  const toggleDisk = (diskIndex: number) => {
    setFailedDisks((current) =>
      current.includes(diskIndex)
        ? current.filter((item) => item !== diskIndex)
        : [...current, diskIndex].sort((a, b) => a - b),
    )
  }

  const reset = () => {
    setFailedDisks([])
    setResult(null)
    setError('')
    setSaved('')
  }

  const saveScenario = async () => {
    if (!result) {
      setError('Calculate the configuration before saving it.')
      return
    }
    setSaving(true)
    setError('')
    try {
      await apiRequest('/api/scenarios', {
        method: 'POST',
        body: JSON.stringify({
          name: `${raidLevel} - ${diskCount} disks`,
          module_type: 'raid',
          inputs: {
            raid_level: raidLevel,
            disk_count: diskCount,
            disk_size_tb: diskSize,
            failed_disks: failedDisks,
            hot_spare: hotSpare,
            rebuild_throughput_mb_s: rebuildThroughput,
          },
          results: result,
          assumptions: result.assumptions,
          tags: ['raid'],
        }),
      })
      setSaved('Scenario saved')
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to save scenario.')
    } finally {
      setSaving(false)
    }
  }

  const layoutColumns = result?.layout?.[0]
    ? Object.keys(result.layout[0]).filter((key) => key !== 'Stripe')
    : Array.from({ length: diskCount }, (_, index) => `Disk ${index + 1}`)

  return (
    <section className="page module-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Reliability and fault tolerance</p>
          <h1>RAID Simulator</h1>
        </div>
        <div className="heading-actions">
          <button type="button" className="secondary-button" onClick={reset}>
            <RotateCcw size={16} /> Reset
          </button>
          <button type="button" className="primary-button" onClick={saveScenario} disabled={saving}>
            <Save size={16} /> {saving ? 'Saving...' : 'Save scenario'}
          </button>
        </div>
      </div>

      <div className="workspace-grid">
        <aside className="control-panel">
          <QuickStartGuide steps={[
            { title: 'Choose a layout', description: 'Select RAID 0, 1, 5, 6, or 10.' },
            { title: 'Set array details', description: 'Enter disk count and capacity per disk.' },
            { title: 'Simulate failures', description: 'Select failed disks and optionally enable a hot spare.' },
            { title: 'Calculate', description: 'Review capacity, state, rebuild time, and the plain-language explanation.' },
          ]} />
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Configuration</p>
              <h2>Array parameters</h2>
            </div>
          </div>

          <label className="field">
            <span>RAID level</span>
            <select value={raidLevel} onChange={(event) => setRaidLevel(event.target.value)}>
              {['RAID 0', 'RAID 1', 'RAID 5', 'RAID 6', 'RAID 10'].map((level) => (
                <option key={level}>{level}</option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Number of disks</span>
            <input type="number" min="2" max="32" value={diskCount}
              onChange={(event) => setDiskCount(Number(event.target.value))} />
          </label>

          <label className="field">
            <span>Disk capacity (TB)</span>
            <input type="number" min="0.1" step="0.1" value={diskSize}
              onChange={(event) => setDiskSize(Number(event.target.value))} />
          </label>

          <label className="field">
            <span>Rebuild throughput (MB/s)</span>
            <input type="number" min="1" value={rebuildThroughput}
              onChange={(event) => setRebuildThroughput(Number(event.target.value))} />
          </label>

          <label className="toggle-row">
            <span>
              <strong>Hot spare</strong>
              <small>Activate an eligible spare on failure</small>
            </span>
            <input type="checkbox" checked={hotSpare}
              onChange={(event) => setHotSpare(event.target.checked)} />
          </label>

          <div className="field">
            <span>Failed disks</span>
            <div className="disk-buttons">
              {Array.from({ length: diskCount }, (_, index) => (
                <button
                  type="button"
                  key={index}
                  className={failedDisks.includes(index) ? 'disk-button failed' : 'disk-button'}
                  onClick={() => toggleDisk(index)}
                  aria-label={`Toggle Disk ${index + 1}`}
                >
                  {index + 1}
                </button>
              ))}
            </div>
          </div>

          <button type="button" className="calculate-button" onClick={calculate}>
            <Wrench size={17} /> Calculate and simulate
          </button>

          {error && <div className="notice error-notice" role="alert">{error}</div>}
          {saved && <div className="notice success-notice" role="status">{saved}</div>}
        </aside>

        <div className="results-column">
          {result ? (
            <>
              <div className="metric-grid">
                <article className="metric-card">
                  <p>Usable capacity</p>
                  <strong>{result.usable_capacity_tb.toFixed(2)} TB</strong>
                  <small>Raw: {result.raw_capacity_tb.toFixed(2)} TB</small>
                </article>
                <article className="metric-card">
                  <p>Storage efficiency</p>
                  <strong>{result.efficiency_percent.toFixed(1)}%</strong>
                  <small>{raidLevel}</small>
                </article>
                <article className="metric-card">
                  <p>Array state</p>
                  <strong className={`state-${result.array_state.toLowerCase()}`}>
                    {result.array_state}
                  </strong>
                  <small>{result.failed_disks.length} failed disk(s)</small>
                </article>
                <article className="metric-card">
                  <p>Rebuild estimate</p>
                  <strong>{result.rebuild_time_hours.toFixed(2)} h</strong>
                  <small>{result.hot_spare_active ? 'Hot spare active' : 'No active spare'}</small>
                </article>
              </div>

              <div className="analysis-grid">
                <article className="panel data-panel">
                  <div className="panel-heading">
                    <div>
                      <p className="eyebrow">Physical mapping</p>
                      <h2>Disk layout</h2>
                    </div>
                    <ShieldAlert size={18} />
                  </div>
                  <div className="layout-table-wrap">
                    <table className="layout-table">
                      <thead>
                        <tr>
                          <th>Stripe</th>
                          {layoutColumns.map((column) => <th key={column}>{column}</th>)}
                        </tr>
                      </thead>
                      <tbody>
                        {result.layout.map((row) => (
                          <tr key={String(row.Stripe)}>
                            <td>{row.Stripe}</td>
                            {layoutColumns.map((column) => (
                              <td key={column}>
                                <span className={parityClass(row[column] ?? '-')}>
                                  {row[column] ?? '-'}
                                </span>
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </article>

                <article className="panel chart-panel">
                  <div className="panel-heading">
                    <div>
                      <p className="eyebrow">Configuration comparison</p>
                      <h2>Usable efficiency</h2>
                    </div>
                  </div>
                  <div className="chart-wrap">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={raidCompare}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="raid" />
                        <YAxis domain={[0, 100]} tickFormatter={(value) => `${value}%`} />
                        <Tooltip formatter={(value) => [`${Number(value).toFixed(1)}%`, 'Efficiency']} />
                        <Bar dataKey="efficiency" radius={[6, 6, 0, 0]} fill="#5b72ee" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </article>
              </div>

              {raidLevel === 'RAID 5' && (
                <article className="panel xor-panel">
                  <div className="panel-heading">
                    <div>
                      <p className="eyebrow">Parity recovery</p>
                      <h2>RAID 5 XOR demonstration</h2>
                    </div>
                  </div>
                  <div className="xor-flow">
                    <div><span>A</span><strong>{result.xor_example.a}</strong></div>
                    <b>⊕</b>
                    <div><span>B</span><strong>{result.xor_example.b}</strong></div>
                    <b>⊕</b>
                    <div><span>C</span><strong>{result.xor_example.c}</strong></div>
                    <b>=</b>
                    <div className="xor-result"><span>P</span><strong>{result.xor_example.parity}</strong></div>
                  </div>
                  <p className="xor-recovery">
                    Reconstruct C: P ⊕ A ⊕ B = <strong>{result.xor_example.recovered_c}</strong>
                  </p>
                </article>
              )}

              <article className="interpretation-panel">
                <div>
                  <p className="eyebrow">Interpretation</p>
                  <h2>{result.array_state === 'Healthy' ? 'Array remains available' : `Array is ${result.array_state.toLowerCase()}`}</h2>
                  <p>Read: {result.read_performance}. Write: {result.write_performance}.</p>
                </div>
                <span className="fault-badge">Fault tolerance: {result.fault_tolerance}</span>
              </article>
              <ExplanationPanel explanation={result.explanation} />
            </>
          ) : (
            <div className="module-empty">
              <ShieldAlert size={30} />
              <h2>Configure an array</h2>
              <p>Select a RAID level and calculate its capacity, layout, fault behavior, and rebuild estimate.</p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
