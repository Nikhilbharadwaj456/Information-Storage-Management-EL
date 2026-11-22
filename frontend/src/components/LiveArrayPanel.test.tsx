import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { LiveArrayPanel } from './LiveArrayPanel'

const array = {
  id: 'abc123abc123',
  filename: 'storagelab-sample.txt',
  level: 'RAID 5',
  disks: 3,
  block_size: 4096,
  rows: 1,
  size: 100,
  sha256: 'f'.repeat(64),
  state: 'Degraded',
  missing_disks: [1],
  fault_tolerance: 1,
  usable_bytes: 8192,
  raw_bytes: 12288,
  spares_available: 1,
  spares_total: 1,
  events: ['Created RAID 5 with 3 disks and 1 hot spare(s).'],
  layout_rows: [{
    row: 1,
    cells: [
      { disk: 0, role: 'parity', label: 'P1', preview: '00ff00ff' },
      { disk: 1, role: 'data', label: 'D1', preview: null },
      { disk: 2, role: 'data', label: 'D2', preview: '41424344' },
    ],
  }],
  rows_shown: 1,
}

vi.mock('../services/api', () => ({
  API_BASE_URL: 'http://test',
  apiRequest: vi.fn(async (path: string) => {
    if (path.endsWith('/verify')) {
      return {
        state: 'Degraded',
        missing_disks: [1],
        original_sha256: 'f'.repeat(64),
        read_sha256: 'f'.repeat(64),
        match: true,
        data_loss: false,
        message: 'Read in degraded mode: Disk 2 reconstructed on the fly.',
      }
    }
    return array
  }),
}))

describe('Live RAID array panel', () => {
  it('writes the sample file and shows the layout and SHA-256 result', async () => {
    render(<LiveArrayPanel />)
    fireEvent.click(screen.getByRole('button', { name: /Use sample file/i }))

    await waitFor(() => {
      expect(screen.getByText('SHA-256 MATCH')).toBeInTheDocument()
    })
    expect(screen.getByText('P1')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Rebuild/i })).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Fail' })).toHaveLength(2)
  })
})
