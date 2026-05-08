import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ToastContainer from './components/ToastContainer';
import Dashboard from './pages/Dashboard';
import Connections from './pages/Connections';
import Rules from './pages/Rules';
import Jobs from './pages/Jobs';
import Login from './pages/Login';
import { useToast } from './hooks/useToast';
import { AuthProvider, ProtectedRoute, useAuth } from './hooks/useAuth';
import { RESOLVED_API_BASE } from './services/api';

const topbarMeta: Record<string, { title: string; desc: string }> = {
  '/':            { title: 'Dashboard',      desc: 'Platform overview and quick stats' },
  '/connections': { title: 'Connections',    desc: 'Manage your PostgreSQL and MongoDB database connections' },
  '/rules':       { title: 'Masking Rules',  desc: 'Define deterministic masking rules per column' },
  '/jobs':        { title: 'Jobs',           desc: 'Run and monitor masking jobs' },
};

function Topbar() {
  const { user, logout } = useAuth();
  const path = window.location.pathname;
  const meta = topbarMeta[path] ?? topbarMeta['/'];

  return (
    <header className="topbar">
      <div className="topbar-title">
        <h1>{meta.title}</h1>
        <p>{meta.desc}</p>
      </div>
      <div className="topbar-actions">
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
          API:{' '}
          <code style={{ color: 'var(--color-accent-2)' }}>{RESOLVED_API_BASE}</code>
        </span>
        {user && (
          <div className="user-badge">
            <span>{user.name}</span>
            <small>{user.role}</small>
            <button className="btn btn-clear" onClick={logout}>Cerrar sesión</button>
          </div>
        )}
      </div>
    </header>
  );
}

function AppLayout({ addToast }: { addToast: (message: string, type?: 'success' | 'error' | 'info') => void }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-content">
        <Topbar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/connections" element={<Connections addToast={addToast} />} />
          <Route path="/rules" element={<Rules addToast={addToast} />} />
          <Route path="/jobs" element={<Jobs addToast={addToast} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </div>
  );
}

function AppRouter({ addToast }: { addToast: (message: string, type?: 'success' | 'error' | 'info') => void }) {
  return (
    <Routes>
      <Route path="/login" element={<Login addToast={addToast} />} />
      <Route path="/*" element={<ProtectedRoute><AppLayout addToast={addToast} /></ProtectedRoute>} />
    </Routes>
  );
}

export default function App() {
  const { toasts, addToast } = useToast();

  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRouter addToast={addToast} />
      </BrowserRouter>
      <ToastContainer toasts={toasts} />
    </AuthProvider>
  );
}
