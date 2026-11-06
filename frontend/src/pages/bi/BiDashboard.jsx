import { useEffect, useState } from 'react'
import { Card, Col, Row, Space, Statistic, Typography } from 'antd'
import { API_ENDPOINTS } from '@/config/api'
import { VAI_TRO } from '@/constants/roles'
import ChartCard from '@/components/ChartCard'
import SkillSelect from '@/components/SkillSelect'
import FunnelChart from '@/components/charts/FunnelChart'
import GroupedBarChart from '@/components/charts/GroupedBarChart'
import HorizontalBarChart from '@/components/charts/HorizontalBarChart'
import MultiLineChart from '@/components/charts/MultiLineChart'
import { useAuth } from '@/contexts/AuthContext'
import http from '@/utils/http'
import { formatPercent } from '@/utils/format'

const SALARY_SERIES = [
  { key: 'avg_min_million', label: 'Lương tối thiểu TB' },
  { key: 'avg_max_million', label: 'Lương tối đa TB' },
]
const SUPPLY_DEMAND_SERIES = [
  { key: 'demand_share', label: 'Cầu: % tin yêu cầu' },
  { key: 'supply_share', label: 'Cung: % ứng viên có' },
]
const formatMillion = (v) => (v === null || v === undefined ? '—' : `${v} tr`)
const formatShare = (v) => formatPercent(v)
const formatPercentValue = (v) => `${v}%`

const BiDashboard = () => {
  const { user } = useAuth()
  const [overview, setOverview] = useState(null)
  const [candidatesBySkill, setCandidatesBySkill] = useState([])
  const [salaryTrend, setSalaryTrend] = useState([])
  const [salaryBySkill, setSalaryBySkill] = useState([])
  const [funnel, setFunnel] = useState([])
  const [skillDemand, setSkillDemand] = useState([])
  const [jobsByLocation, setJobsByLocation] = useState([])
  const [supplyDemand, setSupplyDemand] = useState([])
  const [salarySkillId, setSalarySkillId] = useState()

  const isEmployer = user?.role === VAI_TRO.EMPLOYER

  useEffect(() => {
    fetchDashboard()
  }, [])

  useEffect(() => {
    fetchSalaryTrend()
  }, [salarySkillId])

  const fetchDashboard = async () => {
    const get = (url) => http.get(url).then((res) => res.data)
    const [ov, cbs, sbs, fn, sd, jbl, sup] = await Promise.all([
      get(API_ENDPOINTS.BI.OVERVIEW),
      get(API_ENDPOINTS.BI.CANDIDATES_BY_SKILL),
      get(API_ENDPOINTS.BI.SALARY_BY_SKILL),
      get(API_ENDPOINTS.BI.FUNNEL),
      get(API_ENDPOINTS.BI.SKILL_DEMAND),
      get(API_ENDPOINTS.BI.JOBS_BY_LOCATION),
      get(API_ENDPOINTS.BI.SUPPLY_DEMAND),
    ])
    setOverview(ov)
    setCandidatesBySkill(cbs.items)
    setSalaryBySkill(sbs.items)
    setFunnel(fn.items)
    setSkillDemand(sd.items)
    setJobsByLocation(jbl.items)
    setSupplyDemand(sup.items)
  }

  const fetchSalaryTrend = async () => {
    const { data } = await http.get(API_ENDPOINTS.BI.SALARY_TREND, { params: { skill_id: salarySkillId } })
    setSalaryTrend(data.items)
  }

  const labelValueColumns = (valueTitle, format = (v) => v) => [
    { title: 'Nhãn', dataIndex: 'label' },
    { title: valueTitle, dataIndex: 'value', align: 'right', render: format },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Typography.Title level={3} style={{ margin: 0 }}>BI Dashboard thị trường lao động</Typography.Title>
        <Typography.Text className="muted">
          {isEmployer ? 'Số liệu tuyển dụng (phễu, tỷ lệ trúng tuyển) chỉ tính tin của doanh nghiệp bạn; số liệu thị trường tính toàn hệ thống.'
            : 'Số liệu toàn hệ thống.'}
        </Typography.Text>
      </div>

      {overview && (
        <Row gutter={[16, 16]}>
          {[
            ['Ứng viên', overview.total_candidates],
            ['Tin đang mở', overview.total_open_jobs],
            ['Lượt ứng tuyển', overview.total_applications],
            ['Doanh nghiệp xác minh', overview.total_companies],
            ['Lương TB (triệu/tháng)', overview.avg_salary_million ?? '—'],
            ['Tỷ lệ trúng tuyển', formatPercent(overview.hire_rate, 1)],
          ].map(([title, value]) => (
            <Col key={title} xs={12} md={8} xl={4}>
              <Card size="small"><Statistic title={title} value={value} /></Card>
            </Col>
          ))}
        </Row>
      )}

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={12}>
          <ChartCard title="Xu hướng lương theo tháng" subtitle="Trung bình triệu VND/tháng của tin đăng trong tháng"
            data={salaryTrend} rowKey="month"
            columns={[
              { title: 'Tháng', dataIndex: 'month' },
              { title: 'Tối thiểu TB', dataIndex: 'avg_min_million', align: 'right', render: formatMillion },
              { title: 'Tối đa TB', dataIndex: 'avg_max_million', align: 'right', render: formatMillion },
              { title: 'Số tin', dataIndex: 'job_count', align: 'right' },
            ]}>
            <div style={{ marginBottom: 8, maxWidth: 260 }}>
              <SkillSelect allowClear placeholder="Lọc theo kỹ năng" value={salarySkillId}
                onChange={setSalarySkillId} size="small" />
            </div>
            <MultiLineChart data={salaryTrend} xKey="month" series={SALARY_SERIES} formatValue={formatMillion} />
          </ChartCard>
        </Col>
        <Col xs={24} xl={12}>
          <ChartCard title="Tỷ lệ chuyển đổi tuyển dụng" subtitle="Nhãn trên cột: % so với số hồ sơ ứng tuyển"
            data={funnel} rowKey="stage"
            columns={[
              { title: 'Bước', dataIndex: 'stage' },
              { title: 'Số hồ sơ', dataIndex: 'count', align: 'right' },
              { title: 'So với bước trước', dataIndex: 'rate_from_previous', align: 'right', render: (v) => formatPercent(v, 1) },
              { title: 'So với ứng tuyển', dataIndex: 'rate_from_start', align: 'right', render: (v) => formatPercent(v, 1) },
            ]}>
            <FunnelChart data={funnel} />
          </ChartCard>
        </Col>
        <Col xs={24} xl={12}>
          <ChartCard title="Số lượng ứng viên theo kỹ năng" data={candidatesBySkill}
            columns={labelValueColumns('Số ứng viên')}>
            <HorizontalBarChart data={candidatesBySkill} valueLabel="Ứng viên" />
          </ChartCard>
        </Col>
        <Col xs={24} xl={12}>
          <ChartCard title="Kỹ năng thị trường đang cần" subtitle="% tin đang mở yêu cầu kỹ năng"
            data={skillDemand} columns={labelValueColumns('% tin', formatPercentValue)}>
            <HorizontalBarChart data={skillDemand} valueLabel="% tin" formatValue={formatPercentValue} />
          </ChartCard>
        </Col>
        <Col xs={24} xl={12}>
          <ChartCard title="Cung - cầu kỹ năng" data={supplyDemand} rowKey="skill"
            columns={[
              { title: 'Kỹ năng', dataIndex: 'skill' },
              { title: 'Cầu', dataIndex: 'demand_share', align: 'right', render: formatShare },
              { title: 'Cung', dataIndex: 'supply_share', align: 'right', render: formatShare },
              { title: 'Chênh lệch', dataIndex: 'gap', align: 'right', render: formatShare },
            ]}>
            <GroupedBarChart data={supplyDemand} categoryKey="skill" series={SUPPLY_DEMAND_SERIES} formatValue={formatShare} />
          </ChartCard>
        </Col>
        <Col xs={24} xl={12}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <ChartCard title="Lương trung bình theo kỹ năng" subtitle="Triệu VND/tháng (điểm giữa khoảng lương)"
              data={salaryBySkill}
              columns={[...labelValueColumns('Lương TB', formatMillion), { title: 'Số tin', dataIndex: 'extra', align: 'right' }]}>
              <HorizontalBarChart data={salaryBySkill} valueLabel="Lương TB" formatValue={formatMillion} />
            </ChartCard>
            <ChartCard title="Tin đang mở theo địa điểm" data={jobsByLocation} columns={labelValueColumns('Số tin')}>
              <HorizontalBarChart data={jobsByLocation} valueLabel="Số tin" />
            </ChartCard>
          </Space>
        </Col>
      </Row>
    </Space>
  )
}

export default BiDashboard
