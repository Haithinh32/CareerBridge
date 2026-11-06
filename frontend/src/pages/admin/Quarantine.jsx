import { useEffect, useState } from 'react'
import { App, Button, Card, Form, Input, List, Modal, Space, Tag, Typography } from 'antd'
import { API_ENDPOINTS } from '@/config/api'
import { HANH_DONG_DUYET, LOAI_CO_UI } from '@/constants/job'
import JobSummary from '@/components/JobSummary'
import SkillSelect from '@/components/SkillSelect'
import SkillTags from '@/components/SkillTags'
import http, { getErrorMessage } from '@/utils/http'

// Duyệt tin trong vùng cách ly: sửa, cho đăng, loại, hoặc bổ sung từ điển kỹ năng
const Quarantine = () => {
  const { message } = App.useApp()
  const [jobs, setJobs] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [reviewing, setReviewing] = useState(null)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchQuarantine()
  }, [])

  const handleOpenReview = (job) => {
    setReviewing(job)
    form.setFieldsValue({
      title: job.title,
      description: job.description,
      required_skills: job.required_skills.map((s) => s.skill_id),
      note: '',
      alias: '',
      alias_skill_id: undefined,
    })
  }

  const handleReview = async (action) => {
    const values = form.getFieldsValue()
    const payload = {
      action,
      note: values.note || null,
      updates: action === HANH_DONG_DUYET.APPROVE ? {
        title: values.title,
        description: values.description,
        skills: (values.required_skills || []).map((id) => ({ skill_id: id, is_required: true })),
      } : null,
      new_aliases: values.alias && values.alias_skill_id ? [{ alias: values.alias, skill_id: values.alias_skill_id }] : [],
    }
    try {
      await http.post(API_ENDPOINTS.ADMIN.REVIEW(reviewing.id), payload)
      message.success(action === HANH_DONG_DUYET.APPROVE ? 'Đã duyệt, tin được đăng' : 'Đã loại tin')
      setReviewing(null)
      fetchQuarantine()
    } catch (error) {
      message.error(getErrorMessage(error))
    }
  }

  const handleScan = async () => {
    const { data } = await http.post(API_ENDPOINTS.ADMIN.SCAN)
    message.info(data.message)
    fetchQuarantine()
  }

  const fetchQuarantine = async () => {
    setIsLoading(true)
    try {
      const { data } = await http.get(API_ENDPOINTS.ADMIN.QUARANTINE)
      setJobs(data.items)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Space style={{ justifyContent: 'space-between', width: '100%' }} wrap>
        <Typography.Title level={3} style={{ margin: 0 }}>Tin trong vùng cách ly ({jobs.length})</Typography.Title>
        <Button onClick={handleScan}>Quét lại toàn bộ tin</Button>
      </Space>
      <List loading={isLoading} dataSource={jobs} locale={{ emptyText: 'Không có tin nào cần duyệt' }}
        renderItem={(job) => (
          <Card style={{ marginBottom: 12 }}>
            <JobSummary job={job} />
            <Space direction="vertical" style={{ marginTop: 8, width: '100%' }}>
              {job.flags.map((f) => (
                <div key={f.id}>
                  <Tag color={LOAI_CO_UI[f.flag_type].color}>{LOAI_CO_UI[f.flag_type].text}</Tag>
                  <span>{f.detail}</span> <span className="muted">(điểm {f.score})</span>
                </div>
              ))}
              <div><span className="muted">Kỹ năng: </span><SkillTags skills={job.required_skills} /></div>
              <Button type="primary" onClick={() => handleOpenReview(job)}>Duyệt</Button>
            </Space>
          </Card>
        )} />
      <Modal open={Boolean(reviewing)} title="Duyệt tin" width={720} onCancel={() => setReviewing(null)}
        footer={[
          <Button key="reject" danger onClick={() => handleReview(HANH_DONG_DUYET.REJECT)}>Loại tin</Button>,
          <Button key="approve" type="primary" onClick={() => handleReview(HANH_DONG_DUYET.APPROVE)}>Sửa & cho đăng</Button>,
        ]}>
        <Form form={form} layout="vertical">
          <Form.Item name="title" label="Tiêu đề"><Input /></Form.Item>
          <Form.Item name="description" label="Mô tả"><Input.TextArea rows={6} /></Form.Item>
          <Form.Item name="required_skills" label="Kỹ năng"><SkillSelect /></Form.Item>
          <Typography.Text strong>Bổ sung từ điển (từ đồng nghĩa mà hệ thống chưa nhận ra)</Typography.Text>
          <Space.Compact style={{ width: '100%', margin: '8px 0 16px' }}>
            <Form.Item name="alias" noStyle><Input placeholder="VD: reactjs" style={{ width: '40%' }} /></Form.Item>
            <Form.Item name="alias_skill_id" noStyle><SkillSelect mode={undefined} placeholder="thuộc kỹ năng" style={{ width: '60%' }} /></Form.Item>
          </Space.Compact>
          <Form.Item name="note" label="Ghi chú xử lý"><Input maxLength={1000} /></Form.Item>
        </Form>
      </Modal>
    </Space>
  )
}

export default Quarantine
