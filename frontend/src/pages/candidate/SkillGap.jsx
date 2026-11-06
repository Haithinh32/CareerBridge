import { useEffect, useState } from 'react'
import { Alert, Card, Col, Input, List, Progress, Row, Space, Tag, Typography } from 'antd'
import { LinkOutlined } from '@ant-design/icons'
import { API_ENDPOINTS } from '@/config/api'
import SkillTags from '@/components/SkillTags'
import http, { getErrorMessage } from '@/utils/http'
import { formatPercent } from '@/utils/format'

const SkillGap = () => {
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    fetchReport()
  }, [])

  const handleSearch = (target) => fetchReport(target || undefined)

  const fetchReport = async (targetPosition) => {
    setIsLoading(true)
    try {
      const { data } = await http.get(API_ENDPOINTS.RECOMMENDATIONS.SKILL_GAP, {
        params: { target_position: targetPosition },
      })
      setReport(data)
      setError(null)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Typography.Title level={3} style={{ margin: 0 }}>Báo cáo thiếu hụt kỹ năng</Typography.Title>
        <Typography.Text className="muted">
          So sánh kỹ năng của bạn với kỹ năng các tin tuyển dụng cùng vị trí đang yêu cầu.
        </Typography.Text>
      </div>
      <Input.Search placeholder="Vị trí mục tiêu, VD: Data Analyst" enterButton="Phân tích"
        loading={isLoading} onSearch={handleSearch} style={{ maxWidth: 480 }} />
      {error && <Alert type="info" showIcon message={error} />}
      {report && (
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <Card title={`Mức sẵn sàng: ${report.target_position}`}>
              <Progress type="circle" percent={Math.round(report.readiness * 100)} />
              <Typography.Paragraph className="muted" style={{ marginTop: 12 }}>
                Dựa trên {report.jobs_analyzed} tin tuyển dụng. Tỷ lệ tính theo mức độ phổ biến của
                từng kỹ năng trong các tin đó.
              </Typography.Paragraph>
              <Typography.Text strong>Bạn đã có:</Typography.Text>
              <div><SkillTags skills={report.have_skills} color="green" /></div>
            </Card>
          </Col>
          <Col xs={24} md={16}>
            <Card title="Kỹ năng cần học thêm">
              <List
                dataSource={report.missing_skills}
                locale={{ emptyText: 'Bạn đã có đủ các kỹ năng phổ biến cho vị trí này' }}
                renderItem={(item) => (
                  <List.Item>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Space wrap>
                        <Typography.Text strong>{item.skill.name}</Typography.Text>
                        <Tag>{formatPercent(item.demand_share)} tin yêu cầu</Tag>
                        {item.is_required_often && <Tag color="red">Thường là bắt buộc</Tag>}
                      </Space>
                      {item.courses.length === 0 && <span className="muted">Chưa có khóa học gợi ý</span>}
                      {item.courses.map((c) => (
                        <a key={c.id} href={c.url} target="_blank" rel="noreferrer">
                          <LinkOutlined /> {c.title} · {c.provider}
                          {c.duration_hours && ` · ~${c.duration_hours} giờ`} {c.is_free && <Tag color="green">Miễn phí</Tag>}
                        </a>
                      ))}
                    </Space>
                  </List.Item>
                )}
              />
            </Card>
          </Col>
        </Row>
      )}
    </Space>
  )
}

export default SkillGap
