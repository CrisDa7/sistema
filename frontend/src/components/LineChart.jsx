import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function CustomLineChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#272727" vertical={false} />
        <XAxis
          dataKey="month"
          stroke="#A1A1AA"
          fontSize={13}
          tickLine={false}
          axisLine={false}
          tick={{ fill: '#A1A1AA' }}
        />
        <YAxis
          stroke="#A1A1AA"
          fontSize={13}
          tickLine={false}
          axisLine={false}
          tick={{ fill: '#A1A1AA' }}
        />
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
        <Line
          type="monotone"
          dataKey="value"
          stroke="#E50914"
          strokeWidth={3}
          dot={{ fill: '#E50914', stroke: '#E50914', strokeWidth: 2, r: 5 }}
          activeDot={{ r: 7, stroke: '#E50914', strokeWidth: 3 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
