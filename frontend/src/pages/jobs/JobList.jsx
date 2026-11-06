import { useEffect, useState } from 'react'
import { Card, Col, Input, List, Row, Select, Space, Typography } from 'antd'
import { API_ENDPOINTS } from '@/config/api'
import { DIA_DIEM, HINH_THUC_LABEL } from '@/constants/job'
import JobSummary from '@/components/JobSummary'
import SkillSelect from '@/components/SkillSelect'
import SkillTags from '@/components/SkillTags'
import http from '@/utils/http'

const PAGE_SIZE = 10

const JobList = () => {
  const [filters, setFilters] = useState({ q: '', location: undefined, work_type: undefined, skill_id: undefined })
  const [page, setPage] = useState(1)
  const [result, setResult] = useState({ items: [], total: 0 })
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    fetchJobs()
  }, [filters, page])

  const handleFilterChange = (key, value) => {
    setPage(1)
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  const fetchJobs = async () => {
    setIsLoading(true)
    try {
      const params = { ...filters, skip: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE }
      const { data } = await http.get(API_ENDPOINTS.JOBS.LIST, { params })
      setResult(data)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Typography.Title level={3} style={{ margin: 0 }}>Việc làm đang tuyển</Typography.Title>
      <Card>
        <Row gutter={[12, 12]}>
          <Col xs={24} md={8}>
            <Input.Search placeholder="Vị trí, doanh nghiệp" allowClear
              onSearch={(v) => handleFilterChange('q', v)} />
          </Col>
          <Col xs={12} md={5}>
            <Select placeholder="Địa điểm" allowClear style={{ width: '100%' }}
              options={DIA_DIEM.map((d) => ({ value: d, label: d }))}
              onChange={(v) => handleFilterChange('location', v)} />
          </Col>
          <Col xs={12} md={5}>
            <Select placeholder="Hình thức" allowClear style={{ width: '100%' }}
              options={Object.entries(HINH_THUC_LABEL).map(([value, label]) => ({ value, label }))}
              onChange={(v) => handleFilterChange('work_type', v)} />
          </Col>
          <Col xs={24} md={6}>
            <SkillSelect mode={undefined} allowClear placeholder="Kỹ năng"
              onChange={(v) => handleFilterChange('skill_id', v)} />
          </Col>
        </Row>
      </Card>
      <List
        loading={isLoading}
        dataSource={result.items}
        pagination={{ current: page, pageSize: PAGE_SIZE, total: result.total, onChange: setPage }}
        renderItem={(job) => (
          <Card style={{ marginBottom: 12 }}>
            <JobSummary job={job} />
            <div style={{ marginTop: 8 }}>
              <SkillTags skills={job.required_skills} color="blue" />
            </div>
          </Card>
        )}
      />
    </Space>
  )
}

export default JobList
