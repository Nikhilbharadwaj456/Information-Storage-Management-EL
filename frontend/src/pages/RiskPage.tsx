import { useState } from 'react'
import { Save, ShieldCheck } from 'lucide-react'

import { apiRequest } from '../services/api'
import { ExplanationPanel, type Explanation } from '../components/ExplanationPanel'
import { QuickStartGuide } from '../components/QuickStartGuide'

type RiskResult = {
  asset: string
  threat: string
  vulnerability: string
  likelihood: number
  impact: number
  risk_score: number
  risk_category: string
  suggested_mitigation: string
  explanation: Explanation
}

export function RiskPage() {
  const [asset, setAsset] = useState('Stored data')
  const [threat, setThreat] = useState('Ransomware')
  const [vulnerability, setVulnerability] = useState('Unencrypted backups')
  const [likelihood, setLikelihood] = useState(3)
  const [impact, setImpact] = useState(3)
  const [result, setResult] = useState<RiskResult | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')

  const calculate = async () => {
    setError('')
    setSaved('')
    try {
      const data = await apiRequest<RiskResult>('/api/risk/calculate', {
        method: 'POST',
        body: JSON.stringify({ asset, threat, vulnerability, likelihood, impact }),
      })
      setResult(data)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to calculate risk.')
    }
  }

  const save = async () => {
    if (!result) return setError('Calculate risk before saving.')
    try {
      await apiRequest('/api/scenarios', {
        method: 'POST',
        body: JSON.stringify({
          name: `${threat} Risk Assessment`,
          module_type: 'risk',
          inputs: { asset, threat, vulnerability, likelihood, impact },
          results: result,
          assumptions: ['Likelihood-impact scale uses integers from 1 to 5'],
          tags: ['risk'],
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
        <div><p className="eyebrow">Storage security</p><h1>Storage Risk Assessment</h1></div>
        <button type="button" className="primary-button" onClick={save}><Save size={16} /> Save scenario</button>
      </div>
      <div className="workspace-grid">
        <aside className="control-panel">
          <QuickStartGuide steps={[
            { title: 'Identify the situation', description: 'Select the asset, threat, and vulnerability.' },
            { title: 'Score likelihood and impact', description: 'Use 1 for very low and 5 for very high.' },
            { title: 'Review mitigation', description: 'The score and matrix show the urgency and suggested control.' },
          ]} />
          <label className="field"><span>Asset</span><select value={asset} onChange={(e) => setAsset(e.target.value)}><option>Stored data</option><option>Storage devices</option><option>Backup servers</option></select></label>
          <label className="field"><span>Threat</span><select value={threat} onChange={(e) => setThreat(e.target.value)}><option>Hardware failure</option><option>Ransomware</option><option>Unauthorized access</option></select></label>
          <label className="field"><span>Vulnerability</span><select value={vulnerability} onChange={(e) => setVulnerability(e.target.value)}><option>Weak authentication</option><option>Unencrypted backups</option><option>Lack of redundancy</option></select></label>
          <label className="field"><span>Likelihood: {likelihood}</span><input type="range" min="1" max="5" value={likelihood} onChange={(e) => setLikelihood(Number(e.target.value))} /></label>
          <label className="field"><span>Impact: {impact}</span><input type="range" min="1" max="5" value={impact} onChange={(e) => setImpact(Number(e.target.value))} /></label>
          <button type="button" className="calculate-button" onClick={calculate}><ShieldCheck size={17} /> Calculate risk</button>
          {error && <div className="notice error-notice" role="alert">{error}</div>}
          {saved && <div className="notice success-notice" role="status">{saved}</div>}
        </aside>
        <div className="results-column">
          {result ? (
            <>
              <div className="metric-grid">
                <article className="metric-card"><p>Risk score</p><strong>{result.risk_score} / 25</strong></article>
                <article className="metric-card"><p>Category</p><strong className={`risk-${result.risk_category.toLowerCase()}`}>{result.risk_category}</strong></article>
                <article className="metric-card"><p>Likelihood</p><strong>{result.likelihood}</strong></article>
                <article className="metric-card"><p>Impact</p><strong>{result.impact}</strong></article>
              </div>
              <article className="interpretation-panel"><div><p className="eyebrow">Suggested mitigation</p><h2>{result.suggested_mitigation}</h2><p>{result.asset} · {result.threat} · {result.vulnerability}</p></div></article>
              <article className="panel">
                <div className="panel-heading"><div><p className="eyebrow">1-5 risk matrix</p><h2>Likelihood × impact</h2></div></div>
                <p className="layout-note">Columns: likelihood 1 → 5. Rows: impact 5 (top) → 1 (bottom). The highlighted cell is your selection.</p>
                <div className="risk-grid" aria-label="Risk matrix">
                  {[5, 4, 3, 2, 1].map((row) => [1, 2, 3, 4, 5].map((column) => {
                    const score = row * column
                    const active = likelihood === column && impact === row
                    const category = score <= 5 ? 'low' : score <= 10 ? 'medium' : score <= 15 ? 'high' : 'critical'
                    return <span key={`${row}-${column}`} className={`risk-cell ${category}${active ? ' active' : ''}`} title={`${column} × ${row} = ${score}`}>{score}</span>
                  }))}
                </div>
              </article>
              <ExplanationPanel explanation={result.explanation} />
            </>
          ) : (
            <div className="module-empty"><ShieldCheck size={30} /><h2>Assess a storage risk</h2><p>Select asset, threat, vulnerability, likelihood, and impact.</p></div>
          )}
        </div>
      </div>
    </section>
  )
}
