import {
  Activity,
  BookOpen,
  CircleHelp,
  Database,
  FlaskConical,
  HardDrive,
  LayoutGrid,
  Moon,
  ShieldCheck,
  Sun,
  Waypoints,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'

import { HomePage } from './pages/HomePage'
import { RaidPage } from './pages/RaidPage'
import { DiskPage } from './pages/DiskPage'
import { BackupPage } from './pages/BackupPage'
import { ReplicationPage } from './pages/ReplicationPage'
import { RiskPage } from './pages/RiskPage'
import { ScenariosPage } from './pages/ScenariosPage'
import { MethodologyPage } from './pages/MethodologyPage'

const navigation = [
  { path: '/', label: 'Overview', icon: LayoutGrid },
  { path: '/raid', label: 'RAID Simulator', icon: HardDrive },
  { path: '/disk', label: 'Disk Performance', icon: Activity },
  { path: '/backup', label: 'Backup Planner', icon: Database },
  { path: '/replication', label: 'Replication', icon: Waypoints },
  { path: '/risk', label: 'Risk Assessment', icon: ShieldCheck },
  { path: '/scenarios', label: 'Saved Experiments', icon: FlaskConical },
  { path: '/methodology', label: 'Methodology', icon: BookOpen },
]

function App() {
  const [dark, setDark] = useState(() => localStorage.getItem('storagelab-theme') === 'dark')
  const navigate = useNavigate()
  const location = useLocation()
  const current = navigation.find((item) => item.path === location.pathname) ?? navigation[0]

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
    localStorage.setItem('storagelab-theme', dark ? 'dark' : 'light')
  }, [dark])

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <NavLink to="/" className="brand" aria-label="StorageLab home">
          <span className="brand-mark">SL</span>
          <span>
            <strong>StorageLab</strong>
            <small>Enterprise storage simulator</small>
          </span>
        </NavLink>

        <nav className="primary-nav" aria-label="Primary navigation">
          {navigation.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <span className="nav-short"><item.icon size={17} strokeWidth={2} /></span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span className="status-dot" />
          <span>Local simulation</span>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Information Storage Management</p>
            <strong>{current.label}</strong>
          </div>
          <div className="topbar-actions">
            <button
              type="button"
              className="icon-button"
              onClick={() => navigate('/methodology')}
              aria-label="Open help and methodology"
              title="Help and methodology"
            >
              <CircleHelp size={18} />
            </button>
            <button
              type="button"
              className="icon-button"
              onClick={() => setDark((value) => !value)}
              aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
              title={dark ? 'Switch to light theme' : 'Switch to dark theme'}
            >
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </div>
        </header>

        <div className="page-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/raid" element={<RaidPage />} />
            <Route path="/disk" element={<DiskPage />} />
            <Route path="/backup" element={<BackupPage />} />
            <Route path="/replication" element={<ReplicationPage />} />
            <Route path="/risk" element={<RiskPage />} />
            <Route path="/scenarios" element={<ScenariosPage />} />
            <Route path="/methodology" element={<MethodologyPage />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}

export default App
