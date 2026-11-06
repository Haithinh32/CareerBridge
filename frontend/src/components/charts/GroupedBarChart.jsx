import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { BAR_RADIUS_HORIZONTAL, BAR_SIZE, CHART_INK, SERIES_COLORS } from '@/constants/chart'

const ROW_HEIGHT = 40
const BAR_GAP = 2

// Hai chuỗi cạnh nhau (VD: cung - cầu kỹ năng), cùng một trục giá trị
const GroupedBarChart = ({ data, categoryKey, series, formatValue = (v) => v }) => (
  <ResponsiveContainer width="100%" height={Math.max(200, data.length * ROW_HEIGHT + 60)}>
    <BarChart data={data} layout="vertical" barGap={BAR_GAP} margin={{ top: 4, right: 24, bottom: 4, left: 8 }}>
      <CartesianGrid horizontal={false} stroke={CHART_INK.GRID} />
      <XAxis type="number" tick={{ fill: CHART_INK.MUTED, fontSize: 12 }} tickFormatter={formatValue}
        axisLine={{ stroke: CHART_INK.AXIS }} tickLine={false} />
      <YAxis type="category" dataKey={categoryKey} width={130} tick={{ fill: CHART_INK.TEXT_SECONDARY, fontSize: 12 }}
        axisLine={false} tickLine={false} />
      <Tooltip formatter={(v, name) => [formatValue(v), name]} cursor={{ fill: CHART_INK.GRID, fillOpacity: 0.4 }} />
      <Legend wrapperStyle={{ fontSize: 12 }} />
      {series.map((s, i) => (
        <Bar key={s.key} dataKey={s.key} name={s.label} fill={SERIES_COLORS[i]} barSize={BAR_SIZE / 1.4}
          radius={BAR_RADIUS_HORIZONTAL} />
      ))}
    </BarChart>
  </ResponsiveContainer>
)

export default GroupedBarChart
