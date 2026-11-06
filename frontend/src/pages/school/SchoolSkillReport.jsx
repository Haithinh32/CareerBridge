import { useEffect, useState } from 'react'
import { Alert, Space, Typography } from 'antd'
import { API_ENDPOINTS } from '@/config/api'
import ChartCard from '@/components/ChartCard'
import GroupedBarChart from '@/components/charts/GroupedBarChart'
import http from '@/utils/http'
import { formatPercent } from '@/utils/format'

const SERIES = [
  { key: 'demand_share', label: 'Thị trường cần (% tin)' },
  { key: 'supply_share', label: 'Sinh viên trường có (%)' },
]

// Báo cáo tổng hợp: kỹ năng thị trường đang cần so với kỹ năng sinh viên của trường
const SchoolSkillReport = () => {
  const [items, setItems] = useState([])

  useEffect(() => {
    fetchReport()
  }, [])

  const fetchReport = async () => {
    const { data } = await http.get(API_ENDPOINTS.SCHOOLS.SKILL_REPORT)
    setItems(data.items)
  }

  const biggestGaps = [...items].sort((a, b) => b.gap - a.gap).slice(0, 3)

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Typography.Title level={3} style={{ margin: 0 }}>Báo cáo kỹ năng thị trường đang cần</Typography.Title>
        <Typography.Text className="muted">
          Chỉ tính sinh viên đã đồng ý chia sẻ số liệu tổng hợp với nhà trường; không hiển thị dữ liệu cá nhân.
        </Typography.Text>
      </div>
      {biggestGaps.length > 0 && (
        <Alert type="info" showIcon
          message={`Khoảng trống lớn nhất: ${biggestGaps.map((g) => `${g.skill} (${formatPercent(g.gap)})`).join(', ')}`}
          description="Gợi ý đưa các kỹ năng này vào học phần, workshop hoặc chương trình thực tập." />
      )}
      <ChartCard title="Cung - cầu kỹ năng" data={items} rowKey="skill"
        columns={[
          { title: 'Kỹ năng', dataIndex: 'skill' },
          { title: 'Thị trường cần', dataIndex: 'demand_share', align: 'right', render: (v) => formatPercent(v) },
          { title: 'Sinh viên có', dataIndex: 'supply_share', align: 'right', render: (v) => formatPercent(v) },
          { title: 'Khoảng trống', dataIndex: 'gap', align: 'right', render: (v) => formatPercent(v) },
        ]}>
        <GroupedBarChart data={items} categoryKey="skill" series={SERIES} formatValue={(v) => formatPercent(v)} />
      </ChartCard>
    </Space>
  )
}

export default SchoolSkillReport
