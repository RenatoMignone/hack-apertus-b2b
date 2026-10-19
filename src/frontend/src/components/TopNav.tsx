import { Button as RadixButton, TabNav, Badge } from '@radix-ui/themes';
import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Columns3, Info, LayoutGrid, Plus } from 'lucide-react';
import { api, apiMode } from '../api';
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
        <Info size={13} /><span className="hidden sm:inline">Demo</span>
      </button>
      {open && (
        <div className="absolute right-0 top-9 z-50 w-64 rounded-xl border border-line bg-white p-3 text-sm shadow-lg">
          <p className="text-muted">Synthetic companies, real public sources. Not connected to the live agent yet.</p>
          <p className="mt-1 text-xs text-muted">Reset clears all demo cases and kept items.</p>
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
  const { pathname } = useLocation();
  // "My cases" covers the board and every case page, but not the new-case composer.
  const onCases = pathname === '/cases' || (pathname.startsWith('/cases/') && pathname !== '/cases/new');
  const tabs = [
    { to: '/', label: 'My desk', Icon: LayoutGrid, active: pathname === '/' },
    { to: '/cases', label: 'My cases', Icon: Columns3, active: onCases },
  ];

  return (
    <header className="flex h-[72px] shrink-0 items-center gap-2 border-b border-line bg-white px-3 sm:gap-5 sm:px-5 lg:gap-9 lg:px-8">
      <Link to="/" aria-label="My desk" className="shrink-0">
        <svg viewBox="0 0 400 190" role="img" aria-label="B2B" className="h-10 w-auto lg:h-11">
          <polyline points="0,150 80,150 175,55 220,100 265,55 310,100 375,22" fill="none"
            stroke="var(--color-brand)" strokeWidth="16" strokeLinejoin="miter" />
          <polygon points="398,2 352,10 386,44" fill="var(--color-brand)" />
          <text x="130" y="185" fontSize="96" fontWeight="800" fill="currentColor" letterSpacing="-2">B2B</text>
        </svg>
      </Link>
      <TabNav.Root aria-label="Main" className="self-stretch flex items-center">
        {tabs.map(({ to, label, Icon, active }) => <TabNav.Link key={to} asChild active={active}>
          <Link to={to} aria-label={label}><span className="inline-flex items-center gap-2"><Icon size={16} aria-hidden /><span className="hidden sm:inline">{label}</span></span></Link>
        </TabNav.Link>)}
      </TabNav.Root>
      <div className="ml-auto flex shrink-0 items-center gap-2">
        {apiMode === 'mock' ? <DemoMenu /> : <Badge color="teal" variant="soft" className="hidden sm:inline-flex">Workspace session</Badge>}
        <RadixButton asChild><Link to="/cases/new" aria-label="New case"><Plus size={16} aria-hidden /><span className="hidden sm:inline">New case</span></Link></RadixButton>
      </div>
    </header>
  );
}
