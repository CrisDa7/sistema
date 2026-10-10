import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Dumbbell,
  ClipboardList,
  Ticket,
  CreditCard,
  LogOut,
} from 'lucide-react';
import logo from '../assets/active-gym-logo-transparent.png';
import { useAuth } from '../hooks/useAuth';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Clientes', href: '/clientes', icon: Users },
  { name: 'Áreas', href: '/areas', icon: Dumbbell },
  { name: 'Planes', href: '/planes', icon: ClipboardList },
  { name: 'Membresías', href: '/membresias', icon: Ticket },
  { name: 'Pagos', href: '/pagos', icon: CreditCard },
];

export default function Sidebar({ isOpen, onToggle }) {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-50 w-64 bg-[#050505] border-r border-[#272727] transition-transform duration-300 ease-in-out ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      } lg:translate-x-0`}
    >
      <div className="flex flex-col h-full">
        {/* Logo Area */}
        <div className="flex items-center justify-center h-28 border-b border-[#272727] px-4">
          <img
            src={logo}
            alt="Active Gym Logo"
            className="h-20 w-auto object-contain"
          />
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `flex items-center px-4 py-3 rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'bg-[#E50914] text-white shadow-lg shadow-[#E50914]/20'
                    : 'text-[#A1A1AA] hover:text-white hover:bg-[#191919]'
                }`
              }
              onClick={() => {
                if (window.innerWidth < 1024) onToggle();
              }}
            >
              <item.icon className="w-5 h-5 mr-3" />
              <span className="font-medium">{item.name}</span>
            </NavLink>
          ))}
        </nav>

        {/* Logout */}
        <div className="px-4 pb-6">
          <button
            onClick={handleLogout}
            className="w-full flex items-center px-4 py-3 rounded-lg text-[#A1A1AA] hover:text-white hover:bg-[#191919] transition-all duration-200"
          >
            <LogOut className="w-5 h-5 mr-3" />
            <span className="font-medium">Cerrar sesión</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
