export function MethodologyPage() {
  return (
    <section className="page module-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Models and limitations</p>
          <h1>Methodology</h1>
        </div>
      </div>

      <div className="methodology-grid">
        <article className="panel methodology-card">
          <p className="eyebrow">RAID</p>
          <h2>Capacity and fault tolerance</h2>
          <p>Usable capacity is calculated for RAID 0, 1, 5, 6, and 10. Mirror-pair and distributed-parity failures determine degraded or failed states.</p>
        </article>
        <article className="panel methodology-card">
          <p className="eyebrow">Disk performance</p>
          <h2>Latency and queueing</h2>
          <p>The model combines seek, rotational latency, and transfer time, then applies a simplified M/M/1 response-time equation and Little's Law.</p>
        </article>
        <article className="panel methodology-card">
          <p className="eyebrow">Backup</p>
          <h2>Storage and recovery objectives</h2>
          <p>Full, incremental, and differential strategies use fixed change assumptions and are compared against backup interval, RPO, and estimated RTO.</p>
        </article>
        <article className="panel methodology-card">
          <p className="eyebrow">Replication</p>
          <h2>Acknowledgement assumptions</h2>
          <p>Synchronous writes include network round-trip time. Asynchronous writes are acknowledged locally, with replication lag estimated separately.</p>
        </article>
        <article className="panel methodology-card">
          <p className="eyebrow">Risk</p>
          <h2>Likelihood-impact scoring</h2>
          <p>A 1-5 likelihood and impact scale produces a score from 1-25 and a Low, Medium, High, or Critical category.</p>
        </article>
        <article className="panel methodology-card warning-card">
          <p className="eyebrow">Important limitation</p>
          <h2>Educational estimates only</h2>
          <p>Results are reproducible software simulations and must not be interpreted as physical hardware benchmarks or production compliance guarantees.</p>
        </article>
      </div>
    </section>
  )
}
