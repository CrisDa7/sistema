import { Search, Bell, User } from 'lucide-react';

export default function Header({ onMenuToggle }) {
  return (
    <header className="flex items-center justify-between h-16 px-6 border-b border-[#272727] bg-black">
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuToggle}
          className="lg:hidden p-2 rounded-lg hover:bg-[#191919] transition-colors"
        >
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <h1 className="text-xl font-semibold text-white">Dashboard</h1>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden md:flex items-center px-4 py-2.5 bg-[#191919] rounded-xl border border-[#272727]">
          <Search className="w-4 h-4 text-[#A1A1AA] mr-2" />
          <input
            type="text"
            placeholder="Buscar..."
            className="bg-transparent border-none outline-none text-white placeholder-[#A1A1AA] w-48 text-sm"
            disabled
          />
        </div>

        <div className="flex items-center gap-3">
          <button className="p-2 rounded-xl hover:bg-[#191919] transition-colors relative">
            <Bell className="w-5 h-5 text-[#A1A1AA]" />
          </button>
          <div className="flex items-center gap-3 pl-3 border-l border-[#272727]">
            <div className="w-9 h-9 bg-[#191919] rounded-xl border border-[#272727] flex items-center justify-center">
              <User className="w-5 h-5 text-[#A1A1AA]" />
            </div>
            <div className="hidden md:block">
              <p className="text-sm font-medium text-white">Administrador</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
