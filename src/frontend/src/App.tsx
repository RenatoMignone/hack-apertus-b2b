import { Navigate, Route, Routes } from 'react-router-dom';
import TopNav from './components/TopNav';
import { ToastProvider } from './components/Toast';
import BoardPage from './pages/BoardPage';
import NewCasePage from './pages/NewCasePage';
import CaseWorkspace from './pages/CaseWorkspace';
import ConnectionGate from './components/ConnectionGate';
import ApiErrors from './components/ApiErrors';

// Two places: her cases (home) and one case. Plus the composer for a new case.
export default function App() {
  return (
    <ToastProvider>
      <ConnectionGate>
        <ApiErrors />
      <div className="flex h-full flex-col">
        <TopNav />
        <main className="min-h-0 flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<BoardPage />} />
            <Route path="/cases" element={<Navigate to="/" replace />} />
            <Route path="/cases/new" element={<NewCasePage />} />
            <Route path="/cases/:id" element={<CaseWorkspace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </ConnectionGate>
    </ToastProvider>
  );
}
