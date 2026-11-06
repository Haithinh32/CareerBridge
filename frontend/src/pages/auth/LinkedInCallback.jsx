import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Result, Spin } from 'antd'
import { HOME_BY_ROLE } from '@/constants/roles'
import { useAuth } from '@/contexts/AuthContext'

// Backend chuyển hướng về /dang-nhap/linkedin#token=... (token ở fragment, không lên server log)
const LinkedInCallback = () => {
  const { loginWithToken } = useAuth()
  const navigate = useNavigate()
  const token = new URLSearchParams(window.location.hash.slice(1)).get('token')

  useEffect(() => {
    if (!token) return
    loginWithToken(token).then((me) => {
      window.history.replaceState(null, '', window.location.pathname)
      navigate(me ? HOME_BY_ROLE[me.role] : '/dang-nhap', { replace: true })
    })
  }, [token, loginWithToken, navigate])

  if (!token) return <Result status="error" title="Đăng nhập LinkedIn thất bại" />
  return <Spin style={{ display: 'block', margin: 48 }} />
}

export default LinkedInCallback
