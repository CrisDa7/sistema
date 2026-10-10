import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ProtectedRoute from './components/ProtectedRoute';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Clientes from './pages/Clientes';
import Areas from './pages/Areas';
import Planes from './pages/Planes';
import Membresias from './pages/Membresias';
import Pagos from './pages/Pagos';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public route - Login */}
          <Route path="/login" element={<Login />} />

          {/* Protected routes */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <div className="min-h-screen bg-black flex">
                  <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />

                  <div className="flex-1 flex flex-col lg:ml-64">
                    <Header onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />

                    <main className="flex-1 overflow-auto">
                      <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/clientes" element={<Clientes />} />
                        <Route path="/areas" element={<Areas />} />
                        <Route path="/planes" element={<Planes />} />
                        <Route path="/membresias" element={<Membresias />} />
                        <Route path="/pagos" element={<Pagos />} />
                      </Routes>
                    </main>
                  </div>

                  {/* Mobile overlay */}
                  {sidebarOpen && (
                    <div
                      className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                      onClick={() => setSidebarOpen(false)}
                    />
                  )}
                </div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
