import { CreditCard } from 'lucide-react';

export default function Pagos() {
  return (
    <div className="p-6">
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <CreditCard className="w-16 h-16 text-[#A1A1AA] mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Gestión de Pagos</h2>
          <p className="text-[#A1A1AA]">Sección en desarrollo</p>
          <p className="text-xs text-[#666] mt-4">* Datos demostrativos</p>
        </div>
      </div>
    </div>
  );
}
