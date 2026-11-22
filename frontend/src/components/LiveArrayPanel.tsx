import { useState } from 'react'
import { CheckCircle2, HardDrive, Play, RotateCcw, ShieldCheck, Trash2, Upload, XCircle } from 'lucide-react'

import { API_BASE_URL, apiRequest } from '../services/api'
import { QuickStartGuide } from './QuickStartGuide'

type Cell = {
  disk: number
  role: 'data' | 'mirror' | 'parity' | 'q'
  label: string
  preview: string | null
}

export type LiveArray = {
  id: string
  filename: string
  level: string
  disks: number
  block_size: number
  rows: number
  size: number
  sha256: string
  state: 'Healthy' | 'Degraded' | 'Failed'
  missing_disks: number[]
  fault_tolerance: number
  usable_bytes: number
  raw_bytes: number
  spares_available: number
  spares_total: number
  events: string[]
  layout_rows: Array<{ row: number; cells: Cell[] }>
  rows_shown: number
}

export type VerifyResult = {
  state: string
  missing_disks: number[]
  original_sha256: string
  read_sha256: string | null
  match: boolean
  data_loss: boolean
  message: string
}

const LEVELS = ['RAID 0', 'RAID 1', 'RAID 5', 'RAID 6', 'RAID 10']
const BLOCK_SIZES = [512, 1024, 4096, 16384, 65536]

const formatBytes = (bytes: number) => {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(2)} MB`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${bytes} B`
}

const sampleFile = () => {
  const line = 'StorageLab sample file: RAID stripes these bytes across disks and rebuilds them from parity.\n'
  return new File([line.repeat(700)], 'storagelab-sample.txt', { type: 'text/plain' })
}

const toBase64 = (file: File) => new Promise<string>((resolve, reject) => {
  const reader = new FileReader()
  reader.onload = () => resolve(String(reader.result).split(',')[1] ?? '')
  reader.onerror = () => reject(new Error('Unable to read the selected file.'))
  reader.readAsDataURL(file)
})

export function LiveArrayPanel() {
  const [file, setFile] = useState<File | null>(null)
  const [raidLevel, setRaidLevel] = useState('RAID 5')
  const [diskCount, setDiskCount] = useState(4)
  const [blockSize, setBlockSize] = useState(4096)
  const [hotSpares, setHotSpares] = useState(1)
  const [array, setArray] = useState<LiveArray | null>(null)
  const [verify, setVerify] = useState<VerifyResult | null>(null)
  const [progress, setProgress] = useState<{ disk: number; done: number; total: number } | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const run = async (action: () => Promise<void>) => {
    setError('')
    setBusy(true)
    try {
      await action()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Request failed.')
    } finally {
      setBusy(false)
    }
  }

  const refreshVerify = async (id: string) => {
    setVerify(await apiRequest<VerifyResult>(`/api/raid/array/${id}/verify`))
  }

  const createArray = (source: File) => run(async () => {
    const created = await apiRequest<LiveArray>('/api/raid/array', {
      method: 'POST',
      body: JSON.stringify({
        raid_level: raidLevel,
        disk_count: diskCount,
        block_size: blockSize,
        hot_spares: hotSpares,
        filename: source.name,
        content_base64: await toBase64(source),
      }),
    })
    setFile(source)
    setArray(created)
    await refreshVerify(created.id)
  })

  const failDisk = (disk: number) => run(async () => {
    if (!array) return
    const updated = await apiRequest<LiveArray>(`/api/raid/array/${array.id}/fail/${disk}`, { method: 'POST' })
    setArray(updated)
    await refreshVerify(updated.id)
  })

  const rebuildDisk = (disk: number) => run(async () => {
    if (!array) return
    setProgress({ disk, done: 0, total: array.rows })
    try {
      const response = await fetch(`${API_BASE_URL}/api/raid/array/${array.id}/rebuild/${disk}`, { method: 'POST' })
      if (!response.ok || !response.body) {
        const body = await response.json().catch(() => ({}))
        throw new Error(typeof body.detail === 'string' ? body.detail : `Rebuild failed (${response.status})`)
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      for (;;) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        for (const line of lines.filter(Boolean)) {
          const event = JSON.parse(line)
          if (event.complete) setArray(event.array)
          else setProgress({ disk, done: event.done, total: event.total })
        }
      }
      await refreshVerify(array.id)
    } finally {
      setProgress(null)
    }
  })

  const discard = () => run(async () => {
    if (array) await apiRequest(`/api/raid/array/${array.id}`, { method: 'DELETE' })
    setArray(null)
    setVerify(null)
  })

  const missing = new Set(array?.missing_disks ?? [])

  return (
    <div className="workspace-grid">
      <aside className="control-panel">
        <QuickStartGuide steps={[
          { title: 'Pick a file', description: 'Upload any file up to 5 MB, or use the sample file.' },
          { title: 'Create the array', description: 'The file is split into stripe units and written to one file per disk.' },
          { title: 'Fail disks', description: 'Failing a disk deletes its file. Reads are rebuilt from parity or mirrors.' },
          { title: 'Rebuild and verify', description: 'Rebuild onto a hot spare, then compare SHA-256 with the original.' },
        ]} />
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Block-level simulation</p>
            <h2>Live array</h2>
          </div>
        </div>

        <label className="field">
          <span>RAID level</span>
          <select value={raidLevel} disabled={!!array} onChange={(event) => setRaidLevel(event.target.value)}>
            {LEVELS.map((level) => <option key={level}>{level}</option>)}
          </select>
        </label>

        <label className="field">
          <span>Number of disks</span>
          <input type="number" min="2" max="8" value={diskCount} disabled={!!array}
            onChange={(event) => setDiskCount(Number(event.target.value))} />
        </label>

        <label className="field">
          <span>Stripe unit (block size)</span>
          <select value={blockSize} disabled={!!array} onChange={(event) => setBlockSize(Number(event.target.value))}>
            {BLOCK_SIZES.map((size) => <option key={size} value={size}>{formatBytes(size)}</option>)}
          </select>
        </label>

        <label className="field">
          <span>Hot spares</span>
          <input type="number" min="0" max="2" value={hotSpares} disabled={!!array}
            onChange={(event) => setHotSpares(Number(event.target.value))} />
        </label>

        {array ? (
          <button type="button" className="secondary-button wide-button" onClick={discard} disabled={busy}>
            <Trash2 size={16} /> Discard array and start over
          </button>
        ) : (
          <>
            <label className="field">
              <span>File to store</span>
              <input type="file" aria-label="File to store"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
            </label>
            <button type="button" className="calculate-button" disabled={busy || !file}
              onClick={() => file && createArray(file)}>
              <Upload size={17} /> Write file to array
            </button>
            <button type="button" className="secondary-button wide-button" disabled={busy}
              onClick={() => createArray(sampleFile())}>
              <Play size={16} /> Use sample file
            </button>
          </>
        )}

        {error && <div className="notice error-notice" role="alert">{error}</div>}
      </aside>

      <div className="results-column">
        {array ? (
          <>
            <div className="metric-grid">
              <article className="metric-card">
                <p>Array state</p>
                <strong className={`state-${array.state.toLowerCase()}`}>{array.state}</strong>
                <small>{array.missing_disks.length} failed disk(s)</small>
              </article>
              <article className="metric-card">
                <p>Fault tolerance</p>
                <strong>{array.fault_tolerance} disk{array.fault_tolerance === 1 ? '' : 's'}</strong>
                <small>{array.level}, {array.disks} disks</small>
              </article>
              <article className="metric-card">
                <p>Stored file</p>
                <strong>{formatBytes(array.size)}</strong>
                <small>{array.rows} stripe rows of {formatBytes(array.block_size)}</small>
              </article>
              <article className="metric-card">
                <p>Hot spares</p>
                <strong>{array.spares_available} / {array.spares_total}</strong>
                <small>available</small>
              </article>
            </div>

            {verify && (
              <article className={`verify-banner ${verify.data_loss ? 'loss' : verify.match ? 'match' : 'mismatch'}`}>
                {verify.match ? <CheckCircle2 size={26} /> : <XCircle size={26} />}
                <div>
                  <h2>{verify.data_loss ? 'DATA LOSS' : verify.match ? 'SHA-256 MATCH' : 'SHA-256 MISMATCH'}</h2>
                  <p>{verify.message}</p>
                  <code>original: {verify.original_sha256}</code>
                  <code>read back: {verify.read_sha256 ?? 'unreadable'}</code>
                </div>
              </article>
            )}

            <article className="panel data-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Actual bytes on each disk file</p>
                  <h2>Block and parity layout</h2>
                </div>
                <HardDrive size={18} />
              </div>
              <div className="layout-table-wrap">
                <table className="layout-table live-layout">
                  <thead>
                    <tr>
                      <th>Row</th>
                      {Array.from({ length: array.disks }, (_, disk) => (
                        <th key={disk}>
                          <div>Disk {disk + 1}</div>
                          {missing.has(disk) ? (
                            <button type="button" className="disk-action rebuild" disabled={busy || array.state === 'Failed'}
                              onClick={() => rebuildDisk(disk)}>
                              <RotateCcw size={12} /> Rebuild
                            </button>
                          ) : (
                            <button type="button" className="disk-action fail" disabled={busy}
                              onClick={() => failDisk(disk)}>
                              Fail
                            </button>
                          )}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {array.layout_rows.map((row) => (
                      <tr key={row.row}>
                        <td>{row.row}</td>
                        {row.cells.map((cell) => (
                          <td key={cell.disk}>
                            <span className={`disk-cell ${cell.preview === null ? 'failed' : cell.role}`}>
                              {cell.label}
                              <small>{cell.preview ?? 'missing'}</small>
                            </span>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {array.rows > array.rows_shown && (
                <p className="layout-note">Showing the first {array.rows_shown} of {array.rows} stripe rows.</p>
              )}
              <p className="layout-note">
                D = data block, D′ = mirror copy, P = XOR parity, Q = Reed–Solomon parity over GF(2⁸).
                The hex under each block is its first 4 bytes on disk.
              </p>
            </article>

            {progress && (
              <article className="panel rebuild-panel" role="status">
                <p className="eyebrow">Rebuilding Disk {progress.disk + 1} onto hot spare</p>
                <div className="progress-track">
                  <div className="progress-fill" style={{ width: `${(progress.done / progress.total) * 100}%` }} />
                </div>
                <small>{progress.done} / {progress.total} stripe rows reconstructed</small>
              </article>
            )}

            <article className="panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">Array history</p>
                  <h2>Event log</h2>
                </div>
                <ShieldCheck size={18} />
              </div>
              <ol className="event-log">
                {array.events.map((event, index) => <li key={index}>{event}</li>)}
              </ol>
            </article>
          </>
        ) : (
          <div className="module-empty">
            <HardDrive size={30} />
            <h2>Write a file to a RAID array</h2>
            <p>Your file is really split into blocks, striped with parity across disk files, and verified with SHA-256 after failures and rebuilds.</p>
          </div>
        )}
      </div>
    </div>
  )
}
