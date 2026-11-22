import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { DiskPage } from './DiskPage'
import { BackupPage } from './BackupPage'

vi.mock('../services/api', () => ({
  apiRequest: vi.fn(async (path: string) => {
    if (path === '/api/disk/analyze') {
      return {
        rotational_latency_ms: 4.167,
        transfer_time_ms: 0.026,
        service_time_ms: 8.193,
        estimated_iops: 122.1,
        utilization: 0.819,
        utilization_percent: 81.9,
        response_time_ms: 45.3,
        requests_in_system: 4.53,
        queue_length: 3.7,
        response_curve: [{ 'Utilization (%)': 5, 'Average response time (ms)': 8.6 }],
        assumptions: ['M/M/1 model'],
      }
    }
    if (path === '/api/backup/compare') {
      return {
        strategies: [{
          Strategy: 'Full',
          'Storage (GB)': 7000,
          'Backup duration (hours)': 2.84,
          'Restore duration (hours)': 2.84,
          'Recovery steps': 1,
          'Restore data (GB)': 1000,
          'RPO compliant': 'Yes',
          'RTO compliant': 'Yes',
        }],
        recommendation: 'Full backup meets the objectives.',
        backup_interval_hours: 24,
        rpo_hours: 24,
        rto_hours: 4,
        assumptions: ['Fixed change data'],
      }
    }
    return {}
  }),
}))

describe('Disk and backup pages', () => {
  it('renders disk analysis results', async () => {
    render(<DiskPage />)
    fireEvent.click(screen.getByRole('button', { name: /Analyze disk/i }))
    await waitFor(() => expect(screen.getByText('81.9%')).toBeInTheDocument())
  })

  it('renders backup comparison results', async () => {
    render(<BackupPage />)
    fireEvent.click(screen.getByRole('button', { name: /Compare strategies/i }))
    await waitFor(() => expect(screen.getByText('7000.0 GB')).toBeInTheDocument())
  })
})
