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
        data_to_rebuild_tb: 1,
        rebuild_throughput_mb_s: 200,
        hot_spare_active: false,
        data_accessible: true,
        remaining_fault_tolerance: '0 disks',
        write_penalty: 4,
        comparison: [
          { RAID: 'RAID 0', 'Capacity (TB)': 4, 'Efficiency (%)': 100, 'Fault Tolerance': '0', Characteristic: 'Performance', 'Write penalty': 1 },
          { RAID: 'RAID 5', 'Capacity (TB)': 3, 'Efficiency (%)': 75, 'Fault Tolerance': '1', Characteristic: 'Balanced', 'Write penalty': 4 },
        ],
        layout: [{ Stripe: 1, 'Disk 1': 'FAILED', 'Disk 2': 'D1.1' }],
        assumptions: ['Logical RAID simulation'],
      }
    }
    if (path === '/api/raid/xor') {
      return {
        blocks: { A: '1010', B: '1100', C: '0110' },
        parity: '0000',
        missing: 'C',
        recovered: '0110',
        verified: true,
        survivors: ['A', 'B'],
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
      expect(screen.getAllByText('3.00 TB').length).toBeGreaterThan(0)
      expect(screen.getByText('Degraded')).toBeInTheDocument()
    })
  })

  it('shows the comparison table and recovers a missing XOR block', async () => {
    render(<RaidPage />)
    fireEvent.click(screen.getByRole('button', { name: /Calculate and simulate/i }))
    await waitFor(() => expect(screen.getByText('RAID level comparison')).toBeInTheDocument())
    expect(screen.getByText('4 I/Os per write', { selector: 'td' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Calculate and recover/i }))
    await waitFor(() => expect(screen.getByText('Matches the original')).toBeInTheDocument())
  })

  it('allows failed disks to be toggled', () => {
    render(<RaidPage />)
    const disk = screen.getByRole('button', { name: 'Toggle Disk 1' })
    fireEvent.click(disk)
    expect(disk).toHaveClass('failed')
  })
})
