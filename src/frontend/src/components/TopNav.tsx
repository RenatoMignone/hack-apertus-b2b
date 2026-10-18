import { Link, NavLink } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { api } from '../api';
import { useLive } from '../api/useLive';
import logo from '../assets/logo.png';

export default function TopNav() {
  const actions = useLive(() => api.listActionItems());
  const open = actions?.filter((a) => a.status !== 'done').length ?? 0;

  const items = [
    { to: '/', label: 'My desk', end: true, badge: 0 },
    { to: '/cases', label: 'My cases', end: false, badge: 0 },
    { to: '/actions', label: 'Action items', end: false, badge: open },
  ];

  return (
    <header className="flex h-14 shrink-0 items-center gap-6 border-b border-line bg-white px-5">
      <Link to="/" aria-label="My desk">
        <img src={logo} alt="Bern Economic Development Agency" className="h-8 w-auto" />
      </Link>
      <nav className="flex items-center gap-1">
        {items.map(({ to, label, end, badge }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm ${isActive ? 'bg-canvas font-medium text-ink' : 'text-muted hover:bg-canvas hover:text-ink'}`
            }
          >
            {label}
            {badge > 0 && <span className="rounded-full bg-brand px-1.5 text-xs font-semibold text-white">{badge}</span>}
          </NavLink>
        ))}
      </nav>
      <div className="ml-auto flex items-center gap-3">
        <span className="text-xs text-warn" title="Synthetic companies, real public source excerpts. Not connected to the live agent.">
          Demo data
        </span>
        <Link to="/cases/new" className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-dark">
          <Plus size={16} /> New case
        </Link>
      </div>
    </header>
  );
}
