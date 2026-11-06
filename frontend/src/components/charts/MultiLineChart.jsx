import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { CHART_HEIGHT, CHART_INK, SERIES_COLORS } from '@/constants/chart'

const DOT_RADIUS = 4

// series: [{ key, label }] - màu gán theo thứ tự slot cố định, có chú giải; một trục Y duy nhất
const MultiLineChart = ({ data, xKey, series, formatValue = (v) => v, yDomain }) => (
  <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
    <LineChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
      <CartesianGrid vertical={false} stroke={CHART_INK.GRID} />
      <XAxis dataKey={xKey} tick={{ fill: CHART_INK.MUTED, fontSize: 12 }}
        axisLine={{ stroke: CHART_INK.AXIS }} tickLine={false} />
      <YAxis tick={{ fill: CHART_INK.MUTED, fontSize: 12 }} axisLine={false} tickLine={false}
        tickFormatter={formatValue} domain={yDomain} width={48} />
      <Tooltip formatter={(v, name) => [formatValue(v), name]}
        cursor={{ stroke: CHART_INK.AXIS, strokeDasharray: '3 3' }} />
      {series.length > 1 && <Legend iconType="plainline" wrapperStyle={{ fontSize: 12, color: CHART_INK.TEXT_SECONDARY }} />}
      {series.map((s, i) => (
        <Line key={s.key} dataKey={s.key} name={s.label} stroke={SERIES_COLORS[i]} strokeWidth={2}
          dot={{ r: DOT_RADIUS, strokeWidth: 2, fill: '#fcfcfb' }} activeDot={{ r: DOT_RADIUS + 1 }}
          connectNulls />
      ))}
    </LineChart>
  </ResponsiveContainer>
)

export default MultiLineChart
