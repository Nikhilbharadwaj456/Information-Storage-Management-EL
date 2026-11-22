export type GuideStep = {
  title: string
  description: string
}

export function QuickStartGuide({ title = 'How to use this module', steps }: {
  title?: string
  steps: GuideStep[]
}) {
  return (
    <details className="quick-start">
      <summary>{title}</summary>
      <ol>
        {steps.map((step) => (
          <li key={step.title}>
            <strong>{step.title}</strong>
            <span>{step.description}</span>
          </li>
        ))}
      </ol>
    </details>
  )
}
