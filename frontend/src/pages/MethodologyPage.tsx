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
          <p>Usable capacity, efficiency, and write penalty (1, 2, 4, 6, 2 back-end I/Os per write) are calculated for RAID 0, 1, 5, 6, and 10. Mirror-pair and distributed-parity failures determine degraded or failed states. Rebuild time = data to rebuild / rebuild throughput.</p>
        </article>
        <article className="panel methodology-card">
          <p className="eyebrow">RAID live array</p>
          <h2>Block-level striping and parity</h2>
          <p>An uploaded file is split into stripe units and written to one file per disk. RAID 5 stores rotating XOR parity. RAID 6 adds a Reed–Solomon Q parity over GF(2⁸), so any two lost blocks in a stripe can be solved. Failing a disk deletes its file; reads and hot-spare rebuilds reconstruct the data, and SHA-256 proves the result matches the original.</p>
        </article>
        <article className="panel methodology-card">
          <p className="eyebrow">Disk performance</p>
          <h2>Latency and queueing</h2>
          <p>Service time = seek + rotational latency (30000 / RPM ms) + transfer time. Utilization U = arrival rate × service time. The M/M/1 model gives response time Ts / (1 − U), queue length U² / (1 − U), and Little's Law N = λ × R. Response time rises sharply past about 70% utilization.</p>
        </article>
        <article className="panel methodology-card">
          <p className="eyebrow">Backup</p>
          <h2>Storage and recovery objectives</h2>
          <p>Full, incremental, and differential strategies use fixed change assumptions and are compared against backup interval, RPO, and estimated RTO.</p>
        </article>
        <article className="panel methodology-card">
          <p className="eyebrow">Replication</p>
          <h2>Acknowledgement assumptions</h2>
          <p>Round trip = network latency + 2 × distance × 5 µs/km. Synchronous writes wait for that round trip (RPO = 0). Asynchronous writes are acknowledged locally; their lag (and RPO) is the one-way delay plus queued transmission time on the replication link.</p>
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
