import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import App from './App'

describe('StorageLab shell', () => {
  it('renders the dashboard and primary navigation', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: 'StorageLab' })).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: 'Primary navigation' })).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: /RAID Simulator/i }).length).toBeGreaterThan(0)
  })

  it('renders a module route shell', () => {
    render(
      <MemoryRouter initialEntries={['/raid']}>
        <App />
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: 'RAID Simulator' })).toBeInTheDocument()
  })
})
