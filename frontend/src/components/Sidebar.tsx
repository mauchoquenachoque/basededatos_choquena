import { NavLink } from 'react-router-dom';

interface NavItem {
  to: string;
  label: string;
  icon: string;
}

const navItems: NavItem[] = [
  { to: '/',           label: 'Dashboard',   icon: '◈' },
  { to: '/connections', label: 'Connections', icon: '⬡' },
  { to: '/rules',      label: 'Masking Rules', icon: '◉' },
  { to: '/jobs',       label: 'Jobs',         icon: '▶' },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">🎭</div>
        <span className="logo-text">Enmask</span>
        <span className="logo-badge">SDM</span>
      </div>

      <nav className="sidebar-nav" aria-label="Main navigation">
        <span className="nav-section-label">Platform</span>
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            id={`nav-${item.label.toLowerCase().replace(/\s/g, '-')}`}
          >
            <span style={{ fontSize: 18, lineHeight: 1 }}>{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <p className="version-badge">Enmask v1.0.0 · Static Data Masking</p>
      </div>
    </aside>
  );
}
