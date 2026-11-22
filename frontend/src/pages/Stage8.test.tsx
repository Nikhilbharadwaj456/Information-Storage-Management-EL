import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { ReplicationPage } from './ReplicationPage'
import { RiskPage } from './RiskPage'
import { ScenariosPage } from './ScenariosPage'

vi.mock('../services/api', () => ({
  apiRequest: vi.fn(async (path: string) => {
    if (path === '/api/replication/compare') {
      return {
        selected: { mode: 'Synchronous', response_ms: 22, lag_ms: 0, data_loss: 'Near zero' },
        comparison: [
          { mode: 'Synchronous', response_ms: 22, lag_ms: 0, data_loss: 'Near zero' },
          { mode: 'Asynchronous', response_ms: 2, lag_ms: 20.5, data_loss: 'Lag window' },
        ],
        assumptions: ['Simplified acknowledgement model'],
      }
    }
    if (path === '/api/risk/calculate') {
      return {
        asset: 'Stored data',
        threat: 'Ransomware',
        vulnerability: 'Unencrypted backups',
        likelihood: 3,
        impact: 3,
        risk_score: 9,
        risk_category: 'Medium',
        suggested_mitigation: 'Isolate backups',
      }
    }
    if (path === '/api/scenarios') return []
    return {}
  }),
}))

describe('Replication, risk, and scenario pages', () => {
  it('renders replication comparison', async () => {
    render(<ReplicationPage />)
    fireEvent.click(screen.getByRole('button', { name: /Compare replication/i }))
    await waitFor(() => expect(screen.getAllByText('22.00 ms').length).toBeGreaterThan(0))
  })

  it('renders risk assessment', async () => {
    render(<RiskPage />)
    fireEvent.click(screen.getByRole('button', { name: /Calculate risk/i }))
    await waitFor(() => {
      expect(screen.getByText('9 / 25')).toBeInTheDocument()
      expect(screen.getByText('Medium')).toBeInTheDocument()
    })
  })

  it('renders empty scenario state', async () => {
    render(<ScenariosPage />)
    await waitFor(() => expect(screen.getByText('No saved experiments')).toBeInTheDocument())
  })
})
