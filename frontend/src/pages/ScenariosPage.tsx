import { useEffect, useState } from 'react'
import { Copy, Download, RefreshCw, Trash2 } from 'lucide-react'

import { API_BASE_URL, apiRequest } from '../services/api'
import { QuickStartGuide } from '../components/QuickStartGuide'

type Scenario = {
  id: number
  name: string
  module_type: string
  inputs: Record<string, unknown>
  results: Record<string, unknown>
  assumptions: string[]
  tags: string[]
  created_at: string
}

export function ScenariosPage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [selected, setSelected] = useState<number[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [comparison, setComparison] = useState<Scenario[]>([])

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      setScenarios(await apiRequest<Scenario[]>('/api/scenarios'))
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to load scenarios.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void load() }, [])

  const remove = async (id: number) => {
    try {
      await apiRequest(`/api/scenarios/${id}`, { method: 'DELETE' })
      await load()
      setSelected((items) => items.filter((item) => item !== id))
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to delete scenario.')
    }
  }

  const clone = async (id: number) => {
    try {
      await apiRequest(`/api/scenarios/${id}/clone`, { method: 'POST' })
      await load()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to clone scenario.')
    }
  }

  const toggle = (id: number) => {
    setSelected((items) => items.includes(id)
      ? items.filter((item) => item !== id)
      : items.length < 3 ? [...items, id] : items)
  }

  const downloadCsv = () => {
    window.open(`${API_BASE_URL}/api/scenarios/export/csv`, '_blank', 'noopener,noreferrer')
  }

  const compare = async () => {
    if (selected.length < 2) {
      setError('Select at least two scenarios to compare.')
      return
    }
    setError('')
    try {
      const data = await apiRequest<Scenario[]>('/api/scenarios/compare', {
        method: 'POST',
        body: JSON.stringify({ scenario_ids: selected }),
      })
      setComparison(data)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to compare scenarios.')
    }
  }

  return (
    <section className="page module-page">
      <div className="page-heading">
        <div><p className="eyebrow">Experiment history</p><h1>Saved Experiments</h1></div>
        <div className="heading-actions">
          <button type="button" className="secondary-button" onClick={load}><RefreshCw size={16} /> Refresh</button>
          <button type="button" className="secondary-button" onClick={compare} disabled={selected.length < 2}>Compare</button>
          <button type="button" className="primary-button" onClick={downloadCsv}><Download size={16} /> Export CSV</button>
        </div>
      </div>
      <QuickStartGuide title="How to manage saved experiments" steps={[
        { title: 'Save from a module', description: 'Complete a calculation, then select Save scenario.' },
        { title: 'Review and reuse', description: 'Clone a scenario to repeat it or delete it when no longer needed.' },
        { title: 'Compare and export', description: 'Select two or three entries, compare them, or export all entries as CSV.' },
      ]} />
      {error && <div className="notice error-notice" role="alert">{error}</div>}
      {loading ? (
        <div className="module-empty"><p>Loading scenarios...</p></div>
      ) : scenarios.length === 0 ? (
        <div className="module-empty"><h2>No saved experiments</h2><p>Save a RAID, disk, backup, replication, or risk scenario to see it here.</p></div>
      ) : (
        <article className="panel data-panel">
          <div className="layout-table-wrap">
            <table className="layout-table backup-table">
              <thead><tr><th>Select</th><th>Name</th><th>Module</th><th>Tags</th><th>Created</th><th>Actions</th></tr></thead>
              <tbody>
                {scenarios.map((scenario) => (
                  <tr key={scenario.id}>
                    <td><input type="checkbox" checked={selected.includes(scenario.id)} onChange={() => toggle(scenario.id)} aria-label={`Select ${scenario.name}`} /></td>
                    <td><strong>{scenario.name}</strong></td>
                    <td>{scenario.module_type}</td>
                    <td>{scenario.tags.join(', ') || '-'}</td>
                    <td>{new Date(scenario.created_at).toLocaleString()}</td>
                    <td>
                      <span className="table-actions">
                        <button type="button" className="icon-button small" onClick={() => clone(scenario.id)} aria-label={`Clone ${scenario.name}`}><Copy size={14} /></button>
                        <button type="button" className="icon-button small danger" onClick={() => remove(scenario.id)} aria-label={`Delete ${scenario.name}`}><Trash2 size={14} /></button>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
      )}
      {selected.length > 0 && <div className="selection-bar">{selected.length} scenario(s) selected for comparison</div>}
      {comparison.length > 0 && (
        <article className="panel data-panel comparison-panel">
          <div className="panel-heading"><div><p className="eyebrow">Side-by-side</p><h2>Scenario comparison</h2></div></div>
          <div className="layout-table-wrap">
            <table className="layout-table backup-table">
              <thead><tr><th>Name</th><th>Module</th><th>Key inputs</th><th>Key results</th></tr></thead>
              <tbody>
                {comparison.map((scenario) => (
                  <tr key={scenario.id}>
                    <td><strong>{scenario.name}</strong></td>
                    <td>{scenario.module_type}</td>
                    <td>{Object.entries(scenario.inputs).slice(0, 4).map(([key, value]) => `${key}: ${String(value)}`).join('; ')}</td>
                    <td>{Object.entries(scenario.results).slice(0, 4).map(([key, value]) => `${key}: ${typeof value === 'number' ? value : JSON.stringify(value).slice(0, 35)}`).join('; ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
      )}
    </section>
  )
}
