import { useEffect, useState } from 'react'
import { App, Button, Card, List, Typography } from 'antd'
import { API_ENDPOINTS } from '@/config/api'
import JobSummary from '@/components/JobSummary'
import http, { getErrorMessage } from '@/utils/http'

const SavedJobs = () => {
  const { message } = App.useApp()
  const [items, setItems] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchSavedJobs()
  }, [])

  const handleUnsave = async (jobId) => {
    try {
      await http.delete(API_ENDPOINTS.JOBS.SAVE(jobId))
      setItems((prev) => prev.filter((j) => j.id !== jobId))
    } catch (error) {
      message.error(getErrorMessage(error))
    }
  }

  const fetchSavedJobs = async () => {
    try {
      const { data } = await http.get(API_ENDPOINTS.CANDIDATE.SAVED_JOBS)
      setItems(data.items)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card title={<Typography.Title level={4} style={{ margin: 0 }}>Tin đã lưu</Typography.Title>}>
      <List loading={isLoading} dataSource={items} locale={{ emptyText: 'Chưa lưu tin nào' }}
        renderItem={(job) => (
          <List.Item actions={[<Button key="unsave" onClick={() => handleUnsave(job.id)}>Bỏ lưu</Button>]}>
            <JobSummary job={job} />
          </List.Item>
        )} />
    </Card>
  )
}

export default SavedJobs
