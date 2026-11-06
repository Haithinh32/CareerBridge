import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert, App, Button, Card, Col, DatePicker, Form, Input, InputNumber, Row, Select, Typography } from 'antd'
import dayjs from 'dayjs'
import { API_ENDPOINTS } from '@/config/api'
import { CAP_BAC, CAP_BAC_LABEL, DIA_DIEM, HINH_THUC, HINH_THUC_LABEL, LOAI_CO_UI, TRANG_THAI_TIN } from '@/constants/job'
import SkillSelect from '@/components/SkillSelect'
import http, { getErrorMessage } from '@/utils/http'

const MILLION = 1_000_000
const toOptions = (labels) => Object.entries(labels).map(([value, label]) => ({ value, label }))

// Tin có cấu trúc: vị trí, kỹ năng bắt buộc/ưu tiên, lương, địa điểm, hạn nộp
const JobForm = () => {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const { message, modal } = App.useApp()
  const [form] = Form.useForm()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const isEdit = Boolean(jobId)

  useEffect(() => {
    if (isEdit) fetchJob()
  }, [jobId])

  const handleSubmit = async (values) => {
    const required = values.required_skills || []
    const optional = (values.optional_skills || []).filter((id) => !required.includes(id))
    const payload = {
      title: values.title,
      description: values.description,
      location: values.location,
      work_type: values.work_type,
      level: values.level,
      salary_min: values.salary_min ? Math.round(values.salary_min * MILLION) : null,
      salary_max: values.salary_max ? Math.round(values.salary_max * MILLION) : null,
      min_years_experience: values.min_years_experience || 0,
      deadline: values.deadline.format('YYYY-MM-DD'),
      skills: [
        ...required.map((id) => ({ skill_id: id, is_required: true })),
        ...optional.map((id) => ({ skill_id: id, is_required: false })),
      ],
    }
    setIsSubmitting(true)
    try {
      const { data } = isEdit
        ? await http.put(API_ENDPOINTS.JOBS.UPDATE(jobId), payload)
        : await http.post(API_ENDPOINTS.JOBS.CREATE, payload)
      if (data.status === TRANG_THAI_TIN.QUARANTINED) {
        modal.warning({
          title: 'Tin đang chờ quản trị viên duyệt',
          content: data.flags.map((f) => `${LOAI_CO_UI[f.flag_type].text}: ${f.detail}`).join('\n'),
        })
      } else {
        message.success('Đã lưu tin tuyển dụng')
      }
      navigate('/nha-tuyen-dung/tin')
    } catch (error) {
      message.error(getErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  const fetchJob = async () => {
    const { data } = await http.get(API_ENDPOINTS.JOBS.DETAIL(jobId))
    form.setFieldsValue({
      ...data,
      location: data.location || data.location_raw,
      salary_min: data.salary_min ? data.salary_min / MILLION : null,
      salary_max: data.salary_max ? data.salary_max / MILLION : null,
      deadline: data.deadline ? dayjs(data.deadline) : null,
      required_skills: data.required_skills.map((s) => s.skill_id),
      optional_skills: data.optional_skills.map((s) => s.skill_id),
    })
  }

  return (
    <Card title={<Typography.Title level={4} style={{ margin: 0 }}>{isEdit ? 'Sửa tin tuyển dụng' : 'Đăng tin tuyển dụng'}</Typography.Title>}>
      <Alert type="info" showIcon style={{ marginBottom: 16 }}
        message="Tin được kiểm tra tự động: tin trùng, tin 'fresher' đòi nhiều năm kinh nghiệm hoặc có dấu hiệu lừa đảo sẽ chờ quản trị viên duyệt." />
      <Form form={form} layout="vertical" onFinish={handleSubmit}
        initialValues={{ work_type: HINH_THUC.FULL_TIME, level: CAP_BAC.JUNIOR, min_years_experience: 0 }}>
        <Form.Item name="title" label="Vị trí" rules={[{ required: true, min: 3 }]}><Input /></Form.Item>
        <Row gutter={12}>
          <Col xs={24} md={8}><Form.Item name="level" label="Cấp bậc"><Select options={toOptions(CAP_BAC_LABEL)} /></Form.Item></Col>
          <Col xs={24} md={8}><Form.Item name="work_type" label="Hình thức"><Select options={toOptions(HINH_THUC_LABEL)} /></Form.Item></Col>
          <Col xs={24} md={8}>
            <Form.Item name="location" label="Địa điểm" rules={[{ required: true }]}>
              <Select options={DIA_DIEM.map((d) => ({ value: d, label: d }))} />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="required_skills" label="Kỹ năng bắt buộc" rules={[{ required: true, message: 'Chọn ít nhất 1 kỹ năng' }]}>
          <SkillSelect />
        </Form.Item>
        <Form.Item name="optional_skills" label="Kỹ năng ưu tiên"><SkillSelect /></Form.Item>
        <Row gutter={12}>
          <Col xs={12} md={6}><Form.Item name="salary_min" label="Lương từ (triệu)"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item></Col>
          <Col xs={12} md={6}><Form.Item name="salary_max" label="Đến (triệu)"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item></Col>
          <Col xs={12} md={6}><Form.Item name="min_years_experience" label="Số năm kinh nghiệm"><InputNumber min={0} max={30} step={0.5} style={{ width: '100%' }} /></Form.Item></Col>
          <Col xs={12} md={6}>
            <Form.Item name="deadline" label="Hạn nộp" rules={[{ required: true }]}>
              <DatePicker format="DD/MM/YYYY" style={{ width: '100%' }} disabledDate={(d) => d.isBefore(dayjs(), 'day')} />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="description" label="Mô tả công việc" rules={[{ required: true, min: 20 }]}>
          <Input.TextArea rows={8} />
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={isSubmitting}>{isEdit ? 'Lưu thay đổi' : 'Đăng tin'}</Button>
      </Form>
    </Card>
  )
}

export default JobForm
