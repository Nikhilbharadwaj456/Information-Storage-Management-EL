import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { RaidPage } from './RaidPage'

vi.mock('../services/api', () => ({
  apiRequest: vi.fn(async (path: string) => {
    if (path === '/api/raid/simulate-failure') {
      return {
        level: 'RAID 5',
        disk_count: 4,
        disk_size_tb: 1,
        raw_capacity_tb: 4,
        usable_capacity_tb: 3,
        efficiency_percent: 75,
        fault_tolerance: 1,
        read_performance: 'High',
        write_performance: 'Moderate',
        array_state: 'Degraded',
        failed_disks: [0],
        rebuild_time_hours: 1,
        hot_spare_active: false,
        layout: [{ Stripe: 1, 'Disk 1': 'FAILED', 'Disk 2': 'D1.1' }],
        xor_example: { a: '1010', b: '1100', c: '0110', parity: '0000', recovered_c: '0110' },
        assumptions: ['Logical RAID simulation'],
      }
    }
    return {}
  }),
}))

describe('RAID simulator page', () => {
  it('renders RAID controls and calculates a result', async () => {
    render(<RaidPage />)

    expect(screen.getByRole('heading', { name: 'RAID Simulator' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Calculate and simulate/i }))

    await waitFor(() => {
      expect(screen.getByText('3.00 TB')).toBeInTheDocument()
      expect(screen.getByText('Degraded')).toBeInTheDocument()
    })
  })

  it('allows failed disks to be toggled', () => {
    render(<RaidPage />)
    const disk = screen.getByRole('button', { name: 'Toggle Disk 1' })
    fireEvent.click(disk)
    expect(disk).toHaveClass('failed')
  })
})
