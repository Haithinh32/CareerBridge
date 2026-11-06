import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Alert, App, Button, Card, Col, Empty, List, Row, Space, Spin, Tag, Tooltip, Typography } from 'antd'
import { DislikeOutlined, LikeOutlined } from '@ant-design/icons'
import { API_ENDPOINTS } from '@/config/api'
import JobSummary from '@/components/JobSummary'
import MatchExplanation from '@/components/MatchExplanation'
import http, { getErrorMessage } from '@/utils/http'
import { scoreColor } from '@/utils/format'

const Recommendations = () => {
  const { message } = App.useApp()
  const [items, setItems] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchRecommendations()
  }, [])

  const handleFeedback = async (jobId, isRelevant) => {
    try {
      await http.post(API_ENDPOINTS.RECOMMENDATIONS.FEEDBACK, { job_id: jobId, is_relevant: isRelevant })
      setItems((prev) => prev.map((it) => (it.job.id === jobId ? { ...it, feedback: isRelevant } : it)))
      message.success('Cảm ơn phản hồi của bạn')
    } catch (err) {
      message.error(getErrorMessage(err))
    }
  }

  const fetchRecommendations = async () => {
    try {
      const { data } = await http.get(API_ENDPOINTS.RECOMMENDATIONS.JOBS)
      setItems(data.items)
    } catch (err) {
      setError(getErrorMessage(err))
      setItems([])
    }
  }

  if (items === null) return <Spin style={{ display: 'block', margin: 48 }} />

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Typography.Title level={3} style={{ margin: 0 }}>Việc làm phù hợp với bạn</Typography.Title>
        <Typography.Text className="muted">
          Xếp theo % phù hợp giữa kỹ năng, kinh nghiệm, địa điểm và mong muốn của bạn với từng tin.
        </Typography.Text>
      </div>
      {error && (
        <Alert type="warning" showIcon message={error}
          action={<Link to="/quyen-rieng-tu"><Button size="small">Mở Quyền riêng tư</Button></Link>} />
      )}
      {!error && items.length === 0 && (
        <Empty description={<>Chưa có gợi ý. Hãy <Link to="/ho-so">tải CV và xác nhận kỹ năng</Link>.</>} />
      )}
      <List
        dataSource={items}
        renderItem={({ job, match, feedback, has_applied: hasApplied }) => (
          <Card style={{ marginBottom: 12 }}>
            <Row gutter={[16, 12]}>
              <Col xs={24} md={4} style={{ textAlign: 'center' }}>
                <Tag color={scoreColor(match.score)} style={{ fontSize: 20, padding: '8px 12px' }}>
                  {Math.round(match.score)}%
                </Tag>
                <div className="muted" style={{ marginTop: 4 }}>phù hợp</div>
              </Col>
              <Col xs={24} md={20}>
                <JobSummary job={job} />
                {hasApplied && <Tag color="blue" style={{ marginTop: 6 }}>Đã ứng tuyển</Tag>}
                <div style={{ marginTop: 8 }}><MatchExplanation match={match} compact /></div>
                <Space style={{ marginTop: 8 }} wrap>
                  <span className="muted">Gợi ý này có phù hợp không?</span>
                  <Tooltip title="Phù hợp">
                    <Button aria-label="Phù hợp" type={feedback === true ? 'primary' : 'default'}
                      icon={<LikeOutlined />} onClick={() => handleFeedback(job.id, true)} />
                  </Tooltip>
                  <Tooltip title="Không phù hợp">
                    <Button aria-label="Không phù hợp" danger={feedback === false}
                      type={feedback === false ? 'primary' : 'default'}
                      icon={<DislikeOutlined />} onClick={() => handleFeedback(job.id, false)} />
                  </Tooltip>
                  <Link to={`/viec-lam/${job.id}`}>Xem chi tiết</Link>
                </Space>
              </Col>
            </Row>
          </Card>
        )}
      />
    </Space>
  )
}

export default Recommendations
