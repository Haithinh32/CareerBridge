import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Alert, App, Button, Card, Col, Input, Modal, Progress, Row, Space, Spin, Tag, Typography } from 'antd'
import { HeartOutlined, SendOutlined } from '@ant-design/icons'
import { API_ENDPOINTS } from '@/config/api'
import { LOAI_CO_UI, TRANG_THAI_TIN, TRANG_THAI_TIN_UI } from '@/constants/job'
import { VAI_TRO } from '@/constants/roles'
import JobSummary from '@/components/JobSummary'
import MatchExplanation from '@/components/MatchExplanation'
import SkillTags from '@/components/SkillTags'
import { useAuth } from '@/contexts/AuthContext'
import http, { getErrorMessage } from '@/utils/http'

const JobDetail = () => {
  const { jobId } = useParams()
  const { user } = useAuth()
  const { message } = App.useApp()
  const [job, setJob] = useState(null)
  const [recommendation, setRecommendation] = useState(null)
  const [matchError, setMatchError] = useState(null)
  const [isApplyOpen, setIsApplyOpen] = useState(false)
  const [coverLetter, setCoverLetter] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const isCandidate = user?.role === VAI_TRO.CANDIDATE

  useEffect(() => {
    fetchJob()
    if (isCandidate) fetchMatch()
  }, [jobId, isCandidate])

  const handleApply = async () => {
    setIsSubmitting(true)
    try {
      await http.post(API_ENDPOINTS.JOBS.APPLY(jobId), { cover_letter: coverLetter || null })
      message.success('Đã nộp hồ sơ')
      setIsApplyOpen(false)
      fetchMatch()
    } catch (error) {
      message.error(getErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSave = async () => {
    try {
      if (recommendation?.is_saved) await http.delete(API_ENDPOINTS.JOBS.SAVE(jobId))
      else await http.post(API_ENDPOINTS.JOBS.SAVE(jobId))
      fetchMatch()
    } catch (error) {
      message.error(getErrorMessage(error))
    }
  }

  const fetchJob = async () => {
    try {
      const { data } = await http.get(API_ENDPOINTS.JOBS.DETAIL(jobId))
      setJob(data)
    } catch (error) {
      message.error(getErrorMessage(error))
    }
  }

  const fetchMatch = async () => {
    try {
      const { data } = await http.get(API_ENDPOINTS.RECOMMENDATIONS.EXPLAIN(jobId))
      setRecommendation(data)
      setMatchError(null)
    } catch (error) {
      setMatchError(getErrorMessage(error))
    }
  }

  if (!job) return <Spin style={{ display: 'block', margin: 48 }} />
  const statusUi = TRANG_THAI_TIN_UI[job.status]

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={15}>
        <Card>
          <Space direction="vertical" style={{ width: '100%' }}>
            <JobSummary job={job} />
            {job.status !== TRANG_THAI_TIN.OPEN && <Tag color={statusUi.color}>{statusUi.text}</Tag>}
            {job.flags.filter((f) => !f.is_resolved).map((f) => (
              <Alert key={f.id} type="warning" showIcon message={LOAI_CO_UI[f.flag_type].text} description={f.detail} />
            ))}
            <div><Typography.Text strong>Kỹ năng bắt buộc: </Typography.Text><SkillTags skills={job.required_skills} color="blue" /></div>
            <div><Typography.Text strong>Kỹ năng ưu tiên: </Typography.Text><SkillTags skills={job.optional_skills} /></div>
            <Typography.Paragraph style={{ whiteSpace: 'pre-line', marginTop: 12 }}>{job.description}</Typography.Paragraph>
          </Space>
        </Card>
      </Col>
      <Col xs={24} lg={9}>
        {isCandidate && (
          <Card title="Mức độ phù hợp với bạn">
            {matchError && <Alert type="info" showIcon message={matchError} />}
            {recommendation && (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Progress type="dashboard" percent={Math.round(recommendation.match.score)} />
                <MatchExplanation match={recommendation.match} />
                <Space wrap>
                  <Button type="primary" icon={<SendOutlined />} disabled={recommendation.has_applied || job.status !== TRANG_THAI_TIN.OPEN}
                    onClick={() => setIsApplyOpen(true)}>
                    {recommendation.has_applied ? 'Đã ứng tuyển' : 'Ứng tuyển'}
                  </Button>
                  <Button icon={<HeartOutlined />} onClick={handleSave}>
                    {recommendation.is_saved ? 'Bỏ lưu' : 'Lưu tin'}
                  </Button>
                </Space>
              </Space>
            )}
          </Card>
        )}
        {!user && <Alert type="info" showIcon message="Đăng nhập để xem mức độ phù hợp và ứng tuyển" />}
      </Col>
      <Modal title={`Ứng tuyển: ${job.title}`} open={isApplyOpen} onOk={handleApply}
        confirmLoading={isSubmitting} onCancel={() => setIsApplyOpen(false)} okText="Nộp hồ sơ">
        <Typography.Paragraph className="muted">
          Khi ứng tuyển, {job.company_name} được xem hồ sơ của bạn cho vị trí này. Quyền xem tự động
          bị thu hồi khi bạn bị từ chối hoặc vị trí đóng.
        </Typography.Paragraph>
        <Input.TextArea rows={5} maxLength={3000} placeholder="Thư giới thiệu (không bắt buộc)"
          value={coverLetter} onChange={(e) => setCoverLetter(e.target.value)} />
      </Modal>
    </Row>
  )
}

export default JobDetail
