import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { Columns3, Info, LayoutGrid, ListChecks, Plus } from 'lucide-react';
import { api, apiMode } from '../api';
import { useLive } from '../api/useLive';
import logo from '../assets/logo.png';
import { useToast } from './Toast';

function DemoMenu() {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const toast = useToast();

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => !box.current?.contains(e.target as Node) && setOpen(false);
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false);
    document.addEventListener('mousedown', close);
    document.addEventListener('keydown', esc);
    return () => {
      document.removeEventListener('mousedown', close);
      document.removeEventListener('keydown', esc);
    };
  }, [open]);

  return (
    <div ref={box} className="relative">
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="flex items-center gap-1 rounded-full border border-warn/40 px-2.5 py-1 text-xs font-medium text-warn hover:bg-warn-soft"
      >
        <Info size={13} /> Demo
      </button>
      {open && (
        <div className="absolute right-0 top-9 z-50 w-64 rounded-xl border border-line bg-white p-3 text-sm shadow-lg">
          <p className="text-muted">Synthetic companies, real public sources. Not connected to the live agent yet.</p>
          <button
            onClick={async () => {
              if (!window.confirm('Reset all demo cases, kept items and action items?')) return;
              await api.resetDemo();
              setOpen(false);
              navigate('/');
              toast('Demo data reset');
            }}
            className="mt-2 w-full rounded-lg border border-line px-3 py-1.5 text-left font-medium hover:bg-canvas"
          >
            Reset demo data
          </button>
        </div>
      )}
    </div>
  );
}

export default function TopNav() {
  const actions = useLive(() => api.listActionItems());
  const open = actions?.filter((a) => a.status !== 'done').length ?? 0;

  const items = [
    { to: '/', label: 'My desk', Icon: LayoutGrid, end: true, badge: 0 },
    { to: '/cases', label: 'My cases', Icon: Columns3, end: false, badge: 0 },
    { to: '/actions', label: 'Action items', Icon: ListChecks, end: false, badge: open },
  ];

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-line bg-white px-4 lg:gap-6 lg:px-5">
      <Link to="/" aria-label="My desk" className="shrink-0">
        <img src={logo} alt="Bern Economic Development Agency" className="h-7 w-auto lg:h-8" />
      </Link>
      <nav aria-label="Main" className="flex min-w-0 items-center gap-1">
        {items.map(({ to, label, Icon, end, badge }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            title={label}
            className={({ isActive }) =>
              `flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-lg px-2.5 py-1.5 text-sm ${
                isActive ? 'bg-canvas font-medium text-ink' : 'text-muted hover:bg-canvas hover:text-ink'
              }`
            }
          >
            <Icon size={16} aria-hidden />
            <span className="hidden md:inline">{label}</span>
            {badge > 0 && (
              <span className="rounded-full bg-brand px-1.5 text-xs font-semibold text-white" aria-label={`${badge} open`}>
                {badge}
              </span>
            )}
          </NavLink>
        ))}
      </nav>
      <div className="ml-auto flex shrink-0 items-center gap-2">
        {apiMode === 'mock' ? <DemoMenu /> : <span className="text-xs text-muted">Connected</span>}
        <Link
          to="/cases/new"
          className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-lg bg-brand px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-dark"
        >
          <Plus size={16} aria-hidden /> <span className="hidden sm:inline">New case</span>
        </Link>
      </div>
    </header>
  );
}
