export type Explanation = {
  summary: string
  formula: string
  contributing_factors: string[]
  assumptions: string[]
}

export function ExplanationPanel({ explanation }: { explanation?: Explanation }) {
  if (!explanation) return null
  return (
    <article className="panel explanation-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Explainable AI</p>
          <h2>Why this result?</h2>
        </div>
      </div>
      <p className="explanation-summary">{explanation.summary}</p>
      <div className="explanation-grid">
        <div>
          <h3>Main factors</h3>
          <ul>{explanation.contributing_factors.map((factor) => <li key={factor}>{factor}</li>)}</ul>
        </div>
        <div>
          <h3>Calculation</h3>
          <p>{explanation.formula}</p>
          <h3>Limitations</h3>
          <ul>{explanation.assumptions.map((assumption) => <li key={assumption}>{assumption}</li>)}</ul>
        </div>
      </div>
    </article>
  )
}
