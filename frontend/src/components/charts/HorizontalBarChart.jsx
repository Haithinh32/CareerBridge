import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { BAR_RADIUS_HORIZONTAL, BAR_SIZE, CHART_INK, SERIES_COLORS } from '@/constants/chart'

const ROW_HEIGHT = 28
const MIN_HEIGHT = 160

// Một chuỗi số liệu -> một màu, không cần chú giải (tiêu đề thẻ đã gọi tên)
const HorizontalBarChart = ({ data, valueLabel, formatValue = (v) => v, color = SERIES_COLORS[0] }) => (
  <ResponsiveContainer width="100%" height={Math.max(MIN_HEIGHT, data.length * ROW_HEIGHT + 40)}>
    <BarChart data={data} layout="vertical" margin={{ top: 4, right: 48, bottom: 4, left: 8 }}>
      <CartesianGrid horizontal={false} stroke={CHART_INK.GRID} />
      <XAxis type="number" tick={{ fill: CHART_INK.MUTED, fontSize: 12 }} axisLine={{ stroke: CHART_INK.AXIS }}
        tickLine={false} tickFormatter={formatValue} />
      <YAxis type="category" dataKey="label" width={130} tick={{ fill: CHART_INK.TEXT_SECONDARY, fontSize: 12 }}
        axisLine={false} tickLine={false} />
      <Tooltip cursor={{ fill: CHART_INK.GRID, fillOpacity: 0.4 }}
        formatter={(v) => [formatValue(v), valueLabel]} />
      <Bar dataKey="value" fill={color} barSize={BAR_SIZE} radius={BAR_RADIUS_HORIZONTAL}>
        <LabelList dataKey="value" position="right" formatter={formatValue}
          style={{ fill: CHART_INK.TEXT_SECONDARY, fontSize: 11 }} />
      </Bar>
    </BarChart>
  </ResponsiveContainer>
)

export default HorizontalBarChart
