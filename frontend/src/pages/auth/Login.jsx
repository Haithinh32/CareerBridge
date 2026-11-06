import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { App, Button, Card, Divider, Form, Input, Typography } from 'antd'
import { LinkedinFilled } from '@ant-design/icons'
import { API_ENDPOINTS } from '@/config/api'
import { HOME_BY_ROLE } from '@/constants/roles'
import { useAuth } from '@/contexts/AuthContext'
import http, { getErrorMessage } from '@/utils/http'

const Login = () => {
  const { loginWithToken } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const { message } = App.useApp()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (values) => {
    setIsSubmitting(true)
    try {
      const { data } = await http.post(API_ENDPOINTS.AUTH.LOGIN, values)
      const me = await loginWithToken(data.access_token)
      navigate(location.state?.from || HOME_BY_ROLE[me.role], { replace: true })
    } catch (error) {
      message.error(getErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleLinkedIn = async () => {
    try {
      const { data } = await http.get(API_ENDPOINTS.AUTH.LINKEDIN_URL)
      window.location.href = data.url
    } catch (error) {
      message.error(getErrorMessage(error))
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 16 }}>
      <Card style={{ width: '100%', maxWidth: 400 }}>
        <Typography.Title level={3}>Đăng nhập CareerBridge</Typography.Title>
        <Form layout="vertical" onFinish={handleSubmit} requiredMark={false}>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
            <Input autoComplete="email" />
          </Form.Item>
          <Form.Item name="password" label="Mật khẩu" rules={[{ required: true }]}>
            <Input.Password autoComplete="current-password" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block loading={isSubmitting}>Đăng nhập</Button>
        </Form>
        <Divider plain>hoặc</Divider>
        <Button block icon={<LinkedinFilled />} onClick={handleLinkedIn}>Đăng nhập nhanh bằng LinkedIn</Button>
        <Typography.Paragraph style={{ marginTop: 16, marginBottom: 0 }}>
          Chưa có tài khoản? <Link to="/dang-ky">Đăng ký</Link> · <Link to="/viec-lam">Xem việc làm</Link>
        </Typography.Paragraph>
      </Card>
    </div>
  )
}

export default Login
