import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { App, Button, Card, Dropdown, Segmented, Space, Table, Tag, Typography } from 'antd'
import { API_ENDPOINTS } from '@/config/api'
import { BUOC_TIEP_THEO, TRANG_THAI_UNG_TUYEN, TRANG_THAI_UNG_TUYEN_UI } from '@/constants/candidate'
import MatchExplanation from '@/components/MatchExplanation'
import SkillTags from '@/components/SkillTags'
import http, { getErrorMessage } from '@/utils/http'
import { scoreColor } from '@/utils/format'

const FILTER = { ALL: 'all', APPLICANTS: 'applicants', DISCOVERED: 'discovered' }
const FILTER_OPTIONS = [
  { label: 'Tất cả', value: FILTER.ALL },
  { label: 'Đã ứng tuyển', value: FILTER.APPLICANTS },
  { label: 'Tìm thấy qua hệ thống', value: FILTER.DISCOVERED },
]

// Xếp hạng ứng viên phù hợp nhất cho một tin, kèm lý do khớp
const CandidateRanking = () => {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const { message } = App.useApp()
  const [job, setJob] = useState(null)
  const [items, setItems] = useState([])
  const [filter, setFilter] = useState(FILTER.ALL)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchJob()
    fetchRanking()
  }, [jobId])

  const visibleItems = items.filter((c) => (
    filter === FILTER.ALL || (filter === FILTER.APPLICANTS ? c.is_applicant : !c.is_applicant)
  ))

  const handleStatusChange = async (applicationId, status) => {
    try {
      await http.patch(API_ENDPOINTS.APPLICATIONS.STATUS(applicationId), { status })
      message.success(`Đã chuyển sang "${TRANG_THAI_UNG_TUYEN_UI[status].text}"`)
      fetchRanking()
    } catch (error) {
      message.error(getErrorMessage(error))
    }
  }

  const fetchJob = async () => {
    const { data } = await http.get(API_ENDPOINTS.JOBS.DETAIL(jobId))
    setJob(data)
  }

  const fetchRanking = async () => {
    setIsLoading(true)
    try {
      const { data } = await http.get(API_ENDPOINTS.JOBS.RANKING(jobId))
      setItems(data.items)
    } catch (error) {
      message.error(getErrorMessage(error))
    } finally {
      setIsLoading(false)
    }
  }

  const columns = [
    { title: '#', key: 'rank', width: 48, render: (_, __, index) => index + 1 },
    {
      title: 'Phù hợp', key: 'score', width: 90,
      render: (_, c) => <Tag color={scoreColor(c.match.score)}>{Math.round(c.match.score)}%</Tag>,
    },
    {
      title: 'Ứng viên', key: 'name',
      render: (_, c) => (
        <Space direction="vertical" size={0}>
          <Typography.Text strong>{c.full_name}</Typography.Text>
          <span className="muted">{[c.school_name, c.major, c.location].filter(Boolean).join(' · ')}</span>
        </Space>
      ),
    },
    { title: 'Kỹ năng khớp', key: 'skills', responsive: ['lg'], render: (_, c) => <SkillTags skills={c.match.matched_skills} color="green" /> },
    {
      title: 'Trạng thái', key: 'status',
      render: (_, c) => (c.is_applicant
        ? <Tag color={TRANG_THAI_UNG_TUYEN_UI[c.application_status].color}>{TRANG_THAI_UNG_TUYEN_UI[c.application_status].text}</Tag>
        : <Tag>Chưa ứng tuyển</Tag>),
    },
    {
      title: '', key: 'actions',
      render: (_, c) => (
        <Space wrap>
          <Button size="small" onClick={() => navigate(`/nha-tuyen-dung/ung-vien/${c.candidate_id}?job_id=${jobId}`)}>Xem hồ sơ</Button>
          {c.is_applicant && BUOC_TIEP_THEO[c.application_status].length > 0 && (
            <Dropdown menu={{
              items: BUOC_TIEP_THEO[c.application_status].map((s) => ({ key: s, label: TRANG_THAI_UNG_TUYEN_UI[s].text, danger: s === TRANG_THAI_UNG_TUYEN.REJECTED })),
              onClick: ({ key }) => handleStatusChange(c.application_id, key),
            }}>
              <Button size="small" type="primary">Cập nhật</Button>
            </Dropdown>
          )}
        </Space>
      ),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Typography.Title level={3} style={{ margin: 0 }}>Xếp hạng ứng viên</Typography.Title>
        {job && <Typography.Text className="muted">{job.title} · {job.company_name}</Typography.Text>}
      </div>
      <Card extra={<Segmented options={FILTER_OPTIONS} value={filter} onChange={setFilter} />}
        title={`${visibleItems.length} ứng viên`}>
        <Table rowKey="candidate_id" loading={isLoading} dataSource={visibleItems} columns={columns}
          expandable={{ expandedRowRender: (c) => <MatchExplanation match={c.match} /> }} />
      </Card>
    </Space>
  )
}

export default CandidateRanking
