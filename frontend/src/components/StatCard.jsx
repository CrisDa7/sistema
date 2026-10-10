export default function StatCard({ icon: Icon, label, value, color = '#E50914' }) {
  return (
    <div className="bg-[#111111] border border-[#272727] rounded-2xl p-5 hover:border-[#333333] transition-colors">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-[#191919] rounded-xl border border-[#272727] flex items-center justify-center flex-shrink-0">
          <Icon className="w-6 h-6" style={{ color }} />
        </div>
        <div className="flex-1">
          <p className="text-3xl font-bold text-white mb-0.5">{value}</p>
          <p className="text-sm text-[#A1A1AA] font-medium">{label}</p>
        </div>
      </div>
      <p className="text-xs text-[#666] mt-3">* Datos demostrativos</p>
    </div>
  );
}
