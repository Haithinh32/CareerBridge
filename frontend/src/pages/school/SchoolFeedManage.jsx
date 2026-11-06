import { useEffect, useState } from 'react'
import { App, Button, Card, Col, Input, List, Modal, Popconfirm, Row, Select, Space, Typography } from 'antd'
import { API_ENDPOINTS } from '@/config/api'
import JobSummary from '@/components/JobSummary'
import http, { getErrorMessage } from '@/utils/http'
import { formatDate } from '@/utils/format'

// Nhà trường liên kết doanh nghiệp và đẩy tin của doanh nghiệp liên kết lên feed sinh viên
const SchoolFeedManage = () => {
  const { message } = App.useApp()
  const [companies, setCompanies] = useState([])
  const [links, setLinks] = useState([])
  const [linkedJobs, setLinkedJobs] = useState([])
  const [feed, setFeed] = useState([])
  const [selectedCompany, setSelectedCompany] = useState()
  const [postingJob, setPostingJob] = useState(null)
  const [note, setNote] = useState('')

  useEffect(() => {
    fetchAll()
  }, [])

  const linkedIds = new Set(links.map((c) => c.id))

  const handleLink = async () => {
    if (!selectedCompany) return
    try {
      await http.post(API_ENDPOINTS.SCHOOLS.LINKS, { company_id: selectedCompany })
      setSelectedCompany(undefined)
      fetchAll()
    } catch (error) {
      message.error(getErrorMessage(error))
    }
  }

  const handleUnlink = async (companyId) => {
    await http.delete(API_ENDPOINTS.SCHOOLS.LINK(companyId))
    fetchAll()
  }

  const handlePost = async () => {
    try {
      await http.post(API_ENDPOINTS.SCHOOLS.FEED, { job_id: postingJob.id, note: note || null })
      message.success('Đã đăng lên feed sinh viên')
      setPostingJob(null)
      setNote('')
      fetchAll()
    } catch (error) {
      message.error(getErrorMessage(error))
    }
  }

  const fetchAll = async () => {
    const get = (url) => http.get(url).then((res) => res.data.items)
    const [allCompanies, linked, jobs, posts] = await Promise.all([
      get(API_ENDPOINTS.COMPANIES.LIST),
      get(API_ENDPOINTS.SCHOOLS.LINKS),
      get(API_ENDPOINTS.SCHOOLS.LINKED_JOBS),
      get(API_ENDPOINTS.SCHOOLS.FEED),
    ])
    setCompanies(allCompanies)
    setLinks(linked)
    setLinkedJobs(jobs)
    setFeed(posts)
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Typography.Title level={3} style={{ margin: 0 }}>Feed tuyển dụng & doanh nghiệp liên kết</Typography.Title>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={10}>
          <Card title="Doanh nghiệp liên kết">
            <Space.Compact style={{ width: '100%', marginBottom: 12 }}>
              <Select style={{ width: '100%' }} placeholder="Chọn doanh nghiệp đã xác minh" value={selectedCompany}
                onChange={setSelectedCompany} showSearch optionFilterProp="label"
                options={companies.filter((c) => !linkedIds.has(c.id)).map((c) => ({ value: c.id, label: c.name }))} />
              <Button type="primary" onClick={handleLink}>Liên kết</Button>
            </Space.Compact>
            <List dataSource={links} locale={{ emptyText: 'Chưa liên kết doanh nghiệp nào' }}
              renderItem={(c) => (
                <List.Item actions={[
                  <Popconfirm key="unlink" title="Hủy liên kết?" onConfirm={() => handleUnlink(c.id)}>
                    <Button size="small" type="link" danger>Hủy</Button>
                  </Popconfirm>,
                ]}>
                  <List.Item.Meta title={c.name} description={c.industry} />
                </List.Item>
              )} />
          </Card>
        </Col>
        <Col xs={24} lg={14}>
          <Card title="Tin đang mở của doanh nghiệp liên kết">
            <List dataSource={linkedJobs} pagination={{ pageSize: 5 }}
              renderItem={(job) => (
                <List.Item actions={[<Button key="post" size="small" onClick={() => setPostingJob(job)}>Đăng lên feed</Button>]}>
                  <JobSummary job={job} />
                </List.Item>
              )} />
          </Card>
        </Col>
      </Row>
      <Card title="Feed đã đăng cho sinh viên">
        <List dataSource={feed} pagination={{ pageSize: 5 }}
          renderItem={(post) => (
            <List.Item>
              <div style={{ width: '100%' }}>
                <div className="muted">{formatDate(post.created_at)} {post.note && `· ${post.note}`}</div>
                <JobSummary job={post.job} />
              </div>
            </List.Item>
          )} />
      </Card>
      <Modal open={Boolean(postingJob)} title={`Đăng lên feed: ${postingJob?.title || ''}`}
        onOk={handlePost} onCancel={() => setPostingJob(null)} okText="Đăng">
        <Input.TextArea rows={3} placeholder="Lời nhắn cho sinh viên (không bắt buộc)" value={note}
          onChange={(e) => setNote(e.target.value)} maxLength={1000} />
      </Modal>
    </Space>
  )
}

export default SchoolFeedManage
