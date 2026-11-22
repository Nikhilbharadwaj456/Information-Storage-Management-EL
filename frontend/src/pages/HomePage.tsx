import { Activity, ArrowRight, Database, HardDrive, Play, ShieldCheck, Waypoints } from 'lucide-react'
import { Link } from 'react-router-dom'

const modules = [
  {
    path: '/raid',
    title: 'RAID Simulator',
    description: 'Capacity and write penalty calculator, plus a live array that stripes a real file, fails disks, rebuilds onto a hot spare, and verifies SHA-256.',
    icon: HardDrive,
  },
  {
    path: '/disk',
    title: 'Disk Performance',
    description: "Latency, service time, IOPS, utilization, Little's Law, and queue response.",
    icon: Activity,
  },
  {
    path: '/backup',
    title: 'Backup Planner',
    description: 'Compare storage, restoration, RPO compliance, RTO compliance, and recommendations.',
    icon: Database,
  },
  {
    path: '/replication',
    title: 'Replication',
    description: 'Compare synchronous and asynchronous replication: write response, distance delay, lag, and RPO.',
    icon: Waypoints,
  },
  {
    path: '/risk',
    title: 'Risk Assessment',
    description: 'Calculate likelihood-impact scores and recommended mitigations.',
    icon: ShieldCheck,
  },
]

export function HomePage() {
  return (
    <section className="page">
      <div className="hero-panel">
        <div>
          <p className="eyebrow">Storage research workspace</p>
          <h1>StorageLab</h1>
          <p className="hero-copy">
            Explore reliability, performance, backup recovery, replication, and storage risk
            without physical infrastructure.
          </p>
        </div>
        <div className="hero-status">
          <span className="status-dot" />
          <div>
            <strong>Local models online</strong>
            <small>All estimates are simplified simulations</small>
          </div>
        </div>
      </div>

      <div className="module-grid">
        {modules.map((module) => {
          const Icon = module.icon
          return (
            <Link to={module.path} className="module-card" key={module.path}>
              <span className="module-icon"><Icon size={20} /></span>
              <div>
                <h2>{module.title}</h2>
                <p>{module.description}</p>
              </div>
              <span className="card-arrow" aria-hidden="true">→</span>
            </Link>
          )
        })}
      </div>

      <article className="panel quickstart-panel">
        <div className="quickstart-heading">
          <span className="module-icon"><Play size={18} /></span>
          <div>
            <p className="eyebrow">Quick start</p>
            <h2>Try your first storage simulation</h2>
          </div>
        </div>
        <ol className="quickstart-steps">
          <li><strong>1. Choose a module</strong><span>Start with RAID, Disk, Backup, Replication, or Risk.</span></li>
          <li><strong>2. Enter your parameters</strong><span>Use the defaults for a simple first run or change the values.</span></li>
          <li><strong>3. Calculate and review</strong><span>Read the result, explanation, assumptions, and recommended action.</span></li>
        </ol>
        <Link className="primary-button quickstart-action" to="/raid">
          Start with RAID <ArrowRight size={16} />
        </Link>
      </article>

      <div className="overview-grid">
        <article className="panel">
          <p className="eyebrow">Platform</p>
          <h2>One workspace for storage decisions</h2>
          <p>Preserve scenarios, compare outcomes, and export reproducible model results.</p>
        </article>
        <article className="panel accent-panel">
          <p className="eyebrow">Important distinction</p>
          <h2>Educational estimates</h2>
          <p>Results are model-based and must not be interpreted as hardware benchmarks.</p>
        </article>
      </div>
    </section>
  )
}
