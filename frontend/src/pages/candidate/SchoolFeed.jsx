import { useEffect, useState } from 'react'
import { Alert, Card, List, Typography } from 'antd'
import { API_ENDPOINTS } from '@/config/api'
import JobSummary from '@/components/JobSummary'
import http, { getErrorMessage } from '@/utils/http'
import { formatDate } from '@/utils/format'

const SchoolFeed = () => {
  const [items, setItems] = useState([])
  const [error, setError] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchFeed()
  }, [])

  const fetchFeed = async () => {
    try {
      const { data } = await http.get(API_ENDPOINTS.CANDIDATE.SCHOOL_FEED)
      setItems(data.items)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card title={<Typography.Title level={4} style={{ margin: 0 }}>Tin tuyển dụng từ trường</Typography.Title>}>
      {error && <Alert type="info" showIcon message={error} style={{ marginBottom: 12 }} />}
      <List loading={isLoading} dataSource={items} locale={{ emptyText: 'Trường chưa đăng tin nào' }}
        renderItem={(post) => (
          <List.Item>
            <div style={{ width: '100%' }}>
              <div className="muted" style={{ marginBottom: 4 }}>{post.school_name} · {formatDate(post.created_at)}</div>
              {post.note && <Typography.Paragraph>{post.note}</Typography.Paragraph>}
              <JobSummary job={post.job} />
            </div>
          </List.Item>
        )} />
    </Card>
  )
}

export default SchoolFeed
