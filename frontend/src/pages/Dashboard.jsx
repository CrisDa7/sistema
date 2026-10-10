import { Users, Dumbbell, ClipboardList, CreditCard } from 'lucide-react';
import Card from '../components/Card';
import StatCard from '../components/StatCard';
import CustomLineChart from '../components/LineChart';
import CustomDonutChart from '../components/DonutChart';

export default function Dashboard() {
  // Datos demostrativos - NO son datos reales
  const demoStats = {
    clientesActivos: 156,
    areasServicio: 8,
    planesDisponibles: 5,
    pagosMes: 142,
  };

  const clientesRegistradosData = [
    { month: 'May', value: 156 },
    { month: 'Jun', value: 168 },
    { month: 'Jul', value: 185 },
    { month: 'Ago', value: 192 },
    { month: 'Sep', value: 201 },
    { month: 'Oct', value: 215 },
  ];

  const membresiasData = [
    { name: 'Vigentes', value: 98, color: 'vigentes' },
    { name: 'Por vencer', value: 23, color: 'porVencer' },
    { name: 'Vencidas', value: 35, color: 'vencidas' },
  ];

  const proximosVencimientos = [
    { cliente: 'Juan Pérez', plan: 'Mensual', vencimiento: '13/10/2026', dias: 3 },
    { cliente: 'María García', plan: 'Trimestral', vencimiento: '15/10/2026', dias: 5 },
    { cliente: 'Carlos López', plan: 'Anual', vencimiento: '17/10/2026', dias: 7 },
    { cliente: 'Ana Martínez', plan: 'Mensual', vencimiento: '20/10/2026', dias: 10 },
  ];

  const ultimosPagos = [
    { fecha: '10/10/2026', cliente: 'Ana Martínez', concepto: 'Mensual', monto: '$50.00', estado: 'Completado' },
    { fecha: '09/10/2026', cliente: 'Pedro Sánchez', concepto: 'Trimestral', monto: '$140.00', estado: 'Completado' },
    { fecha: '08/10/2026', cliente: 'Laura Torres', concepto: 'Anual', monto: '$480.00', estado: 'Completado' },
    { fecha: '07/10/2026', cliente: 'Roberto Díaz', concepto: 'Mensual', monto: '$50.00', estado: 'Completado' },
  ];

  const getDiasColor = (dias) => {
    if (dias <= 3) return 'text-[#E50914]';
    if (dias <= 7) return 'text-[#F97316]';
    return 'text-[#A1A1AA]';
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-white mb-2">¡Hola, Administrador!</h2>
        <p className="text-[#A1A1AA]">Resumen general de tu gimnasio</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <StatCard icon={Users} label="Clientes activos" value={demoStats.clientesActivos} />
        <StatCard icon={Dumbbell} label="Áreas de servicio" value={demoStats.areasServicio} />
        <StatCard icon={ClipboardList} label="Planes disponibles" value={demoStats.planesDisponibles} />
        <StatCard icon={CreditCard} label="Pagos del mes" value={demoStats.pagosMes} />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-xl font-semibold text-white">Clientes registrados</h3>
              <p className="text-sm text-[#A1A1AA]">Últimos 6 meses</p>
            </div>
            <div className="flex items-center gap-2 px-3 py-1 bg-[#191919] rounded-lg border border-[#272727]">
              <span className="text-sm text-[#A1A1AA]">Mes</span>
              <svg className="w-4 h-4 text-[#A1A1AA]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
          <CustomLineChart data={clientesRegistradosData} />
          <p className="text-xs text-[#666] mt-3">* Datos demostrativos</p>
        </Card>

        <Card>
          <div className="mb-4">
            <h3 className="text-xl font-semibold text-white mb-2">Estado de membresías</h3>
            <p className="text-sm text-[#A1A1AA]">Distribución actual</p>
          </div>
          <CustomDonutChart data={membresiasData} />
          <p className="text-xs text-[#666] mt-3">* Datos demostrativos</p>
        </Card>
      </div>

      {/* Tables Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <div className="mb-4">
            <h3 className="text-xl font-semibold text-white mb-2">Próximos vencimientos</h3>
            <p className="text-sm text-[#A1A1AA]">Membresías por vencer</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#272727]">
                  <th className="text-left py-3 px-4 text-[#A1A1AA] font-medium text-sm">Cliente</th>
                  <th className="text-left py-3 px-4 text-[#A1A1AA] font-medium text-sm">Plan</th>
                  <th className="text-left py-3 px-4 text-[#A1A1AA] font-medium text-sm">Vencimiento</th>
                  <th className="text-right py-3 px-4 text-[#A1A1AA] font-medium text-sm">Días</th>
                </tr>
              </thead>
              <tbody>
                {proximosVencimientos.map((item, index) => (
                  <tr key={index} className="border-b border-[#272727] last:border-0">
                    <td className="py-3 px-4 text-white text-sm">{item.cliente}</td>
                    <td className="py-3 px-4 text-[#A1A1AA] text-sm">{item.plan}</td>
                    <td className="py-3 px-4 text-[#A1A1AA] text-sm">{item.vencimiento}</td>
                    <td className={`py-3 px-4 text-sm font-medium text-right ${getDiasColor(item.dias)}`}>
                      {item.dias} días
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-[#666] mt-3">* Datos demostrativos</p>
        </Card>

        <Card>
          <div className="mb-4">
            <h3 className="text-xl font-semibold text-white mb-2">Últimos pagos</h3>
            <p className="text-sm text-[#A1A1AA]">Transacciones recientes</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#272727]">
                  <th className="text-left py-3 px-4 text-[#A1A1AA] font-medium text-sm">Fecha</th>
                  <th className="text-left py-3 px-4 text-[#A1A1AA] font-medium text-sm">Cliente</th>
                  <th className="text-left py-3 px-4 text-[#A1A1AA] font-medium text-sm">Concepto</th>
                  <th className="text-right py-3 px-4 text-[#A1A1AA] font-medium text-sm">Monto</th>
                  <th className="text-right py-3 px-4 text-[#A1A1AA] font-medium text-sm">Estado</th>
                </tr>
              </thead>
              <tbody>
                {ultimosPagos.map((item, index) => (
                  <tr key={index} className="border-b border-[#272727] last:border-0">
                    <td className="py-3 px-4 text-[#A1A1AA] text-sm">{item.fecha}</td>
                    <td className="py-3 px-4 text-white text-sm">{item.cliente}</td>
                    <td className="py-3 px-4 text-[#A1A1AA] text-sm">{item.concepto}</td>
                    <td className="py-3 px-4 text-white text-sm text-right">{item.monto}</td>
                    <td className="py-3 px-4 text-sm text-right">
                      <span className="px-2 py-1 bg-[#191919] rounded text-[#A1A1AA] text-xs">
                        {item.estado}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-[#666] mt-3">* Datos demostrativos</p>
        </Card>
      </div>
    </div>
  );
}
