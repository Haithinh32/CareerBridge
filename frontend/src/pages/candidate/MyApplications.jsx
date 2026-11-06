import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, Steps, Table, Tag, Typography } from 'antd'
import { API_ENDPOINTS } from '@/config/api'
import { TRANG_THAI_UNG_TUYEN, TRANG_THAI_UNG_TUYEN_UI } from '@/constants/candidate'
import http from '@/utils/http'
import { formatDate, formatDateTime } from '@/utils/format'

const PIPELINE = [
  TRANG_THAI_UNG_TUYEN.SUBMITTED,
  TRANG_THAI_UNG_TUYEN.VIEWED,
  TRANG_THAI_UNG_TUYEN.INTERVIEW,
  TRANG_THAI_UNG_TUYEN.HIRED,
]

const StatusTimeline = ({ application }) => {
  const reached = new Map(application.status_history.map((h) => [h.status, h.at]))
  const isRejected = application.status === TRANG_THAI_UNG_TUYEN.REJECTED
  const lastIndex = Math.max(...PIPELINE.map((s, i) => (reached.has(s) ? i : 0)))
  return (
    <Steps size="small" current={lastIndex} status={isRejected ? 'error' : 'process'}
      items={PIPELINE.map((s, i) => ({
        title: isRejected && i === lastIndex + 1 ? TRANG_THAI_UNG_TUYEN_UI.rejected.text : TRANG_THAI_UNG_TUYEN_UI[s].text,
        description: reached.has(s) ? formatDateTime(reached.get(s)) : null,
      }))} />
  )
}

const MyApplications = () => {
  const [items, setItems] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchApplications()
  }, [])

  const fetchApplications = async () => {
    try {
      const { data } = await http.get(API_ENDPOINTS.CANDIDATE.APPLICATIONS)
      setItems(data.items)
    } finally {
      setIsLoading(false)
    }
  }

  const columns = [
    { title: 'Vị trí', render: (_, a) => <Link to={`/viec-lam/${a.job_id}`}>{a.job_title}</Link> },
    { title: 'Doanh nghiệp', dataIndex: 'company_name', responsive: ['md'] },
    { title: 'Ngày nộp', dataIndex: 'created_at', render: formatDate, responsive: ['sm'] },
    { title: 'Phù hợp', dataIndex: 'match_score', render: (s) => (s ? `${Math.round(s)}%` : '—'), responsive: ['md'] },
    {
      title: 'Trạng thái', dataIndex: 'status',
      render: (s) => <Tag color={TRANG_THAI_UNG_TUYEN_UI[s].color}>{TRANG_THAI_UNG_TUYEN_UI[s].text}</Tag>,
    },
  ]

  return (
    <Card title={<Typography.Title level={4} style={{ margin: 0 }}>Hồ sơ đã nộp</Typography.Title>}>
      <Table rowKey="id" loading={isLoading} dataSource={items} columns={columns}
        expandable={{ expandedRowRender: (a) => <StatusTimeline application={a} /> }} />
    </Card>
  )
}

export default MyApplications
