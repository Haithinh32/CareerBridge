import { useEffect, useState } from 'react'
import { App, Button, Card, Col, Form, Input, InputNumber, Row, Select, Space, Spin, Switch, Typography } from 'antd'
import { API_ENDPOINTS } from '@/config/api'
import { DIA_DIEM, HINH_THUC_LABEL } from '@/constants/job'
import CvUploadCard from '@/components/candidate/CvUploadCard'
import SkillConfirmCard from '@/components/candidate/SkillConfirmCard'
import http, { getErrorMessage } from '@/utils/http'

const PREFERENCE_FIELDS = [
  'school_id', 'major', 'study_year', 'location', 'work_types', 'availability',
  'target_position', 'years_experience',
]

const CandidateProfile = () => {
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const [profile, setProfile] = useState(null)
  const [schools, setSchools] = useState([])
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    fetchProfile()
    fetchSchools()
  }, [])

  const handleSavePreferences = async (values) => {
    setIsSaving(true)
    try {
      const { data } = await http.put(API_ENDPOINTS.CANDIDATE.PROFILE, values)
      setProfile(data)
      message.success('Đã lưu thông tin')
    } catch (error) {
      message.error(getErrorMessage(error))
    } finally {
      setIsSaving(false)
    }
  }

  const handleDiscoverableChange = async (checked) => {
    try {
      const { data } = await http.patch(API_ENDPOINTS.CANDIDATE.DISCOVERABLE, { is_discoverable: checked })
      setProfile(data)
    } catch (error) {
      message.error(getErrorMessage(error))
    }
  }

  const fetchProfile = async () => {
    const { data } = await http.get(API_ENDPOINTS.CANDIDATE.PROFILE)
    setProfile(data)
    form.setFieldsValue(Object.fromEntries(PREFERENCE_FIELDS.map((f) => [f, data[f]])))
  }

  const fetchSchools = async () => {
    const { data } = await http.get(API_ENDPOINTS.SCHOOLS.LIST)
    setSchools(data.items)
  }

  if (!profile) return <Spin style={{ display: 'block', margin: 48 }} />

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Typography.Title level={3} style={{ margin: 0 }}>Hồ sơ của {profile.full_name}</Typography.Title>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <CvUploadCard onAnalyzed={fetchProfile} />
            <SkillConfirmCard skills={profile.skills} onSaved={fetchProfile} />
          </Space>
        </Col>
        <Col xs={24} lg={12}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Card>
              <Space align="start">
                <Switch checked={profile.is_discoverable} onChange={handleDiscoverableChange} />
                <div>
                  <Typography.Text strong>Cho phép nhà tuyển dụng tìm thấy tôi</Typography.Text>
                  <div className="muted">Hồ sơ xuất hiện trong danh sách xếp hạng ứng viên. Tắt bất cứ lúc nào.</div>
                </div>
              </Space>
            </Card>
            <Card title="Mong muốn & thông tin học tập">
              <Form form={form} layout="vertical" onFinish={handleSavePreferences}>
                <Form.Item name="target_position" label="Vị trí mục tiêu"><Input placeholder="VD: Backend Developer" /></Form.Item>
                <Row gutter={12}>
                  <Col xs={24} sm={16}>
                    <Form.Item name="school_id" label="Trường">
                      <Select allowClear showSearch optionFilterProp="label"
                        options={schools.map((s) => ({ value: s.id, label: s.name }))} />
                    </Form.Item>
                  </Col>
                  <Col xs={24} sm={8}>
                    <Form.Item name="study_year" label="Năm học"><InputNumber min={1} max={8} style={{ width: '100%' }} /></Form.Item>
                  </Col>
                </Row>
                <Form.Item name="major" label="Ngành"><Input /></Form.Item>
                <Row gutter={12}>
                  <Col xs={24} sm={12}>
                    <Form.Item name="location" label="Địa điểm mong muốn">
                      <Select allowClear options={DIA_DIEM.map((d) => ({ value: d, label: d }))} />
                    </Form.Item>
                  </Col>
                  <Col xs={24} sm={12}>
                    <Form.Item name="years_experience" label="Số năm kinh nghiệm">
                      <InputNumber min={0} max={40} step={0.5} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                </Row>
                <Form.Item name="work_types" label="Hình thức làm việc">
                  <Select mode="multiple" options={Object.entries(HINH_THUC_LABEL).map(([value, label]) => ({ value, label }))} />
                </Form.Item>
                <Form.Item name="availability" label="Lịch rảnh"><Input placeholder="VD: Các buổi chiều trong tuần" /></Form.Item>
                <Button type="primary" htmlType="submit" loading={isSaving}>Lưu</Button>
              </Form>
            </Card>
          </Space>
        </Col>
      </Row>
    </Space>
  )
}

export default CandidateProfile
