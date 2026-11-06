import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { BAR_RADIUS_VERTICAL, CHART_HEIGHT, CHART_INK, ORDINAL_BLUE } from '@/constants/chart'
import { formatPercent } from '@/utils/format'

const FUNNEL_BAR_SIZE = 48

// Phễu tuyển dụng: các bước có thứ tự -> thang một sắc độ, đậm dần theo bước
const FunnelChart = ({ data }) => (
  <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
    <BarChart data={data} margin={{ top: 28, right: 8, bottom: 4, left: 0 }}>
      <CartesianGrid vertical={false} stroke={CHART_INK.GRID} />
      <XAxis dataKey="stage" tick={{ fill: CHART_INK.TEXT_SECONDARY, fontSize: 12 }}
        axisLine={{ stroke: CHART_INK.AXIS }} tickLine={false} />
      <YAxis tick={{ fill: CHART_INK.MUTED, fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
      <Tooltip cursor={{ fill: CHART_INK.GRID, fillOpacity: 0.4 }}
        formatter={(v, _, item) => [`${v} hồ sơ (${formatPercent(item.payload.rate_from_start, 1)} so với ứng tuyển)`, 'Số lượng']} />
      <Bar dataKey="count" barSize={FUNNEL_BAR_SIZE} radius={BAR_RADIUS_VERTICAL}>
        {data.map((entry, i) => <Cell key={entry.stage} fill={ORDINAL_BLUE[i % ORDINAL_BLUE.length]} />)}
        <LabelList dataKey="rate_from_start" position="top" formatter={(v) => formatPercent(v)}
          style={{ fill: CHART_INK.TEXT_SECONDARY, fontSize: 12 }} />
      </Bar>
    </BarChart>
  </ResponsiveContainer>
)

export default FunnelChart
