import { useState } from 'react'
import { RotateCcw, Save, ShieldAlert, Wrench } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { apiRequest } from '../services/api'
import { ExplanationPanel, type Explanation } from '../components/ExplanationPanel'
import { QuickStartGuide } from '../components/QuickStartGuide'
import { LiveArrayPanel } from '../components/LiveArrayPanel'

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
  data_to_rebuild_tb: number
  rebuild_throughput_mb_s: number
  hot_spare_active: boolean
  data_accessible: boolean
  remaining_fault_tolerance: string
  write_penalty: number
  comparison: Array<{
    RAID: string
    'Capacity (TB)': number
    'Efficiency (%)': number
    'Fault Tolerance': string
    Characteristic: string
    'Write penalty': number
  }>
  layout: Array<Record<string, string | number>>
  assumptions: string[]
  explanation: Explanation
}

type XorResult = {
  blocks: Record<'A' | 'B' | 'C', string>
  parity: string
  missing: 'A' | 'B' | 'C'
  recovered: string
  verified: boolean
  survivors: string[]
}

const parityClass = (value: string | number) => {
  const text = String(value)
  if (text === 'FAILED') return 'disk-cell failed'
  if (text.startsWith('P') || text.startsWith('Q')) return 'disk-cell parity'
  return 'disk-cell data'
}

export function RaidPage() {
  const [mode, setMode] = useState<'calculator' | 'live'>('calculator')
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

  const [xorBlocks, setXorBlocks] = useState({ A: '1010', B: '1100', C: '0110' })
  const [xorMissing, setXorMissing] = useState<'A' | 'B' | 'C'>('C')
  const [xorResult, setXorResult] = useState<XorResult | null>(null)
  const [xorError, setXorError] = useState('')

  const runXor = async () => {
    setXorError('')
    try {
      setXorResult(await apiRequest<XorResult>('/api/raid/xor', {
        method: 'POST',
        body: JSON.stringify({ a: xorBlocks.A, b: xorBlocks.B, c: xorBlocks.C, missing: xorMissing }),
      }))
    } catch (caught) {
      setXorResult(null)
      setXorError(caught instanceof Error ? caught.message : 'Unable to run the XOR demonstration.')
    }
  }

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
          failed_disks: failedDisks.filter((disk) => disk < diskCount),
          hot_spare: hotSpare,
          rebuild_throughput_mb_s: rebuildThroughput,
        }),
      })
      setResult(data)
    } catch (caught) {
      setResult(null)
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
        {mode === 'calculator' && (
        <div className="heading-actions">
          <button type="button" className="secondary-button" onClick={reset}>
            <RotateCcw size={16} /> Reset
          </button>
          <button type="button" className="primary-button" onClick={saveScenario} disabled={saving}>
            <Save size={16} /> {saving ? 'Saving...' : 'Save scenario'}
          </button>
        </div>
        )}
      </div>

      <div className="mode-tabs" role="tablist" aria-label="RAID simulator mode">
        <button type="button" role="tab" aria-selected={mode === 'calculator'}
          className={mode === 'calculator' ? 'mode-tab active' : 'mode-tab'}
          onClick={() => setMode('calculator')}>
          Capacity calculator
        </button>
        <button type="button" role="tab" aria-selected={mode === 'live'}
          className={mode === 'live' ? 'mode-tab active' : 'mode-tab'}
          onClick={() => setMode('live')}>
          Live array (real data)
        </button>
      </div>

      {mode === 'live' && <LiveArrayPanel />}

      {mode === 'calculator' && (
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
                  <small>
                    {result.data_to_rebuild_tb > 0
                      ? `${result.data_to_rebuild_tb.toFixed(2)} TB at ${result.rebuild_throughput_mb_s} MB/s${result.hot_spare_active ? ', hot spare active' : ', no spare'}`
                      : result.data_accessible ? 'Nothing to rebuild' : 'Data lost, rebuild impossible'}
                  </small>
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
                      <BarChart data={result.comparison}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="RAID" interval={0} />
                        <YAxis domain={[0, 100]} tickFormatter={(value) => `${value}%`} />
                        <Tooltip formatter={(value) => [`${Number(value).toFixed(1)}%`, 'Efficiency']} />
                        <Bar dataKey="Efficiency (%)" radius={[6, 6, 0, 0]} fill="#6366f1" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </article>
              </div>

              <article className="panel data-panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">{diskCount} disks × {diskSize} TB</p>
                    <h2>RAID level comparison</h2>
                  </div>
                </div>
                <div className="layout-table-wrap">
                  <table className="layout-table backup-table">
                    <thead>
                      <tr><th>RAID</th><th>Usable capacity</th><th>Efficiency</th><th>Fault tolerance</th><th>Write penalty</th><th>Main characteristic</th></tr>
                    </thead>
                    <tbody>
                      {result.comparison.map((row) => (
                        <tr key={row.RAID} className={row.RAID === result.level ? 'selected-row' : undefined}>
                          <td><strong>{row.RAID}</strong></td>
                          <td>{row['Capacity (TB)'].toFixed(2)} TB</td>
                          <td>{row['Efficiency (%)'].toFixed(1)}%</td>
                          <td>{/^\d+$/.test(row['Fault Tolerance']) ? `${row['Fault Tolerance']} disk(s)` : row['Fault Tolerance']}</td>
                          <td>{row['Write penalty']} I/Os per write</td>
                          <td>{row.Characteristic}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {result.comparison.length < 5 && (
                  <p className="layout-note">Levels that need an even number of disks are hidden for {diskCount} disks.</p>
                )}
              </article>

              {raidLevel === 'RAID 5' && (
                <article className="panel xor-panel">
                  <div className="panel-heading">
                    <div>
                      <p className="eyebrow">Parity recovery</p>
                      <h2>RAID 5 XOR demonstration</h2>
                    </div>
                  </div>
                  <div className="xor-inputs">
                    {(['A', 'B', 'C'] as const).map((name) => (
                      <label className="field" key={name}>
                        <span>Block {name} (binary)</span>
                        <input value={xorBlocks[name]} maxLength={16} inputMode="numeric"
                          onChange={(event) => setXorBlocks({ ...xorBlocks, [name]: event.target.value })} />
                      </label>
                    ))}
                    <label className="field">
                      <span>Mark as missing</span>
                      <select value={xorMissing} onChange={(event) => setXorMissing(event.target.value as 'A' | 'B' | 'C')}>
                        <option value="A">Block A</option><option value="B">Block B</option><option value="C">Block C</option>
                      </select>
                    </label>
                    <button type="button" className="secondary-button xor-run" onClick={runXor}>Calculate and recover</button>
                  </div>
                  {xorError && <div className="notice error-notice" role="alert">{xorError}</div>}
                  {xorResult && (
                    <>
                      <div className="xor-flow">
                        {(['A', 'B', 'C'] as const).map((name, index) => (
                          <span className="xor-term" key={name}>
                            {index > 0 && <b>⊕</b>}
                            <div className={name === xorResult.missing ? 'xor-missing' : undefined}>
                              <span>{name}</span><strong>{xorResult.blocks[name]}</strong>
                            </div>
                          </span>
                        ))}
                        <b>=</b>
                        <div className="xor-result"><span>P</span><strong>{xorResult.parity}</strong></div>
                      </div>
                      <p className="xor-recovery">
                        {xorResult.missing} is lost. Rebuild it: P ⊕ {xorResult.survivors.join(' ⊕ ')} = <strong>{xorResult.recovered}</strong>
                        {' '}<span className={`compliance ${xorResult.verified ? 'pass' : 'fail'}`}>
                          {xorResult.verified ? 'Matches the original' : 'Does not match'}
                        </span>
                      </p>
                    </>
                  )}
                </article>
              )}

              <article className="interpretation-panel">
                <div>
                  <p className="eyebrow">Interpretation</p>
                  <h2>{result.array_state === 'Healthy' ? 'Array remains available' : `Array is ${result.array_state.toLowerCase()}`}</h2>
                  <p>
                    Data accessible: <strong>{result.data_accessible ? 'Yes' : 'No, data is lost'}</strong>.
                    Further failures it can survive: <strong>{result.remaining_fault_tolerance}</strong>.
                  </p>
                  <p>Read: {result.read_performance}. Write: {result.write_performance} (write penalty {result.write_penalty}).</p>
                </div>
                <span className="fault-badge">Fault tolerance: {typeof result.fault_tolerance === 'number' ? `${result.fault_tolerance} disk(s)` : result.fault_tolerance}</span>
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
      )}
    </section>
  )
}
