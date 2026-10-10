import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const COLORS = {
  vigentes: '#E50914',
  porVencer: '#F97316',
  vencidas: '#A1A1AA',
};

export default function CustomDonutChart({ data }) {
  return (
    <div className="flex flex-col lg:flex-row items-center justify-center gap-6 h-[280px]">
      <div className="flex-1 w-full max-w-[220px]">
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={5}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[entry.color]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#191919',
                border: '1px solid #272727',
                borderRadius: '12px',
                color: '#FFFFFF',
                padding: '12px',
              }}
              itemStyle={{ color: '#A1A1AA', fontSize: 13 }}
              labelStyle={{ color: '#FFFFFF', fontSize: 13 }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="flex-shrink-0 lg:w-32">
        <Legend
          payload={data.map((entry) => ({
            id: entry.name,
            type: 'circle',
            value: `${entry.name} (${entry.value})`,
            color: COLORS[entry.color],
          }))}
          iconType="circle"
          verticalAlign="middle"
          align="left"
          layout="vertical"
          wrapperStyle={{ color: '#A1A1AA', fontSize: 13 }}
        />
      </div>
    </div>
  );
}
