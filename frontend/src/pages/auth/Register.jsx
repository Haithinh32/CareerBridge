import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { App, Button, Card, Form, Input, Radio, Typography } from 'antd'
import { API_ENDPOINTS } from '@/config/api'
import { HOME_BY_ROLE, VAI_TRO, VAI_TRO_LABEL } from '@/constants/roles'
import { useAuth } from '@/contexts/AuthContext'
import http, { getErrorMessage } from '@/utils/http'

const SELF_REGISTER_ROLES = [VAI_TRO.CANDIDATE, VAI_TRO.EMPLOYER, VAI_TRO.SCHOOL]
const TAX_CODE_PATTERN = /^\d{10}(-?\d{3})?$/

const Register = () => {
  const { loginWithToken } = useAuth()
  const navigate = useNavigate()
  const { message } = App.useApp()
  const [form] = Form.useForm()
  const role = Form.useWatch('role', form)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (values) => {
    setIsSubmitting(true)
    try {
      const { data } = await http.post(API_ENDPOINTS.AUTH.REGISTER, values)
      const me = await loginWithToken(data.access_token)
      message.success('Đăng ký thành công')
      navigate(me.role === VAI_TRO.CANDIDATE ? '/quyen-rieng-tu' : HOME_BY_ROLE[me.role], { replace: true })
    } catch (error) {
      message.error(getErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 16 }}>
      <Card style={{ width: '100%', maxWidth: 460 }}>
        <Typography.Title level={3}>Tạo tài khoản</Typography.Title>
        <Form form={form} layout="vertical" onFinish={handleSubmit} requiredMark={false}
          initialValues={{ role: VAI_TRO.CANDIDATE }}>
          <Form.Item name="role" label="Bạn là">
            <Radio.Group optionType="button" buttonStyle="solid"
              options={SELF_REGISTER_ROLES.map((r) => ({ value: r, label: VAI_TRO_LABEL[r] }))} />
          </Form.Item>
          <Form.Item name="full_name" label="Họ tên người đại diện" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
            <Input autoComplete="email" />
          </Form.Item>
          <Form.Item name="password" label="Mật khẩu" rules={[{ required: true, min: 8, message: 'Ít nhất 8 ký tự' }]}>
            <Input.Password autoComplete="new-password" />
          </Form.Item>
          {role === VAI_TRO.EMPLOYER && (
            <>
              <Form.Item name="company_name" label="Tên doanh nghiệp" rules={[{ required: true }]}>
                <Input />
              </Form.Item>
              <Form.Item name="tax_code" label="Mã số thuế" extra="Dùng để xác minh doanh nghiệp (10 hoặc 13 số)"
                rules={[{ required: true, pattern: TAX_CODE_PATTERN, message: 'Mã số thuế gồm 10 hoặc 13 chữ số' }]}>
                <Input />
              </Form.Item>
            </>
          )}
          {role === VAI_TRO.SCHOOL && (
            <Form.Item name="school_name" label="Tên trường" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
          )}
          <Button type="primary" htmlType="submit" block loading={isSubmitting}>Đăng ký</Button>
        </Form>
        <Typography.Paragraph style={{ marginTop: 16, marginBottom: 0 }}>
          Đã có tài khoản? <Link to="/dang-nhap">Đăng nhập</Link>
        </Typography.Paragraph>
      </Card>
    </div>
  )
}

export default Register
