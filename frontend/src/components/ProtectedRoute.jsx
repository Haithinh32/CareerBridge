import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { Result, Spin } from 'antd'
import { useAuth } from '@/contexts/AuthContext'

const ProtectedRoute = ({ roles }) => {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) return <Spin style={{ display: 'block', margin: 48 }} />
  if (!user) return <Navigate to="/dang-nhap" state={{ from: location.pathname }} replace />
  if (roles && !roles.includes(user.role)) {
    return <Result status="403" title="Không có quyền truy cập trang này" />
  }
  return <Outlet />
}

export default ProtectedRoute
