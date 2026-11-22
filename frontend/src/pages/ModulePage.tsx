import { Construction } from 'lucide-react'

type ModulePageProps = {
  moduleName: string
}

export function ModulePage({ moduleName }: ModulePageProps) {
  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">StorageLab module</p>
          <h1>{moduleName}</h1>
        </div>
        <span className="stage-badge">Implementation stage</span>
      </div>

      <div className="empty-state">
        <Construction size={28} />
        <h2>{moduleName} interface ready for integration</h2>
        <p>
          This route is prepared for API-connected controls, metrics, tables, charts,
          and scenario actions in the next stage.
        </p>
      </div>
    </section>
  )
}
