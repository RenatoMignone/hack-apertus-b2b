import { Navigate, Route, Routes } from 'react-router-dom';
import TopNav from './components/TopNav';
import { ToastProvider } from './components/Toast';
import DeskPage from './pages/DeskPage';
import BoardPage from './pages/BoardPage';
import ActionsPage from './pages/ActionsPage';
import NewCasePage from './pages/NewCasePage';
import CaseWorkspace from './pages/CaseWorkspace';
import ConnectionGate from './components/ConnectionGate';
import ApiErrors from './components/ApiErrors';

export default function App() {
  return (
    <ToastProvider>
    <ConnectionGate>
    <ApiErrors />
    <div className="flex h-full flex-col">
      <TopNav />
      <main className="min-h-0 flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={<DeskPage />} />
          <Route path="/cases" element={<BoardPage />} />
          <Route path="/cases/new" element={<NewCasePage />} />
          <Route path="/cases/:id" element={<CaseWorkspace />} />
          <Route path="/actions" element={<ActionsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
    </ConnectionGate>
    </ToastProvider>
  );
}
