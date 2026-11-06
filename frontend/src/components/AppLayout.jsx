import { useMemo, useState } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Button, Drawer, Grid, Layout, Menu, Space, Typography } from 'antd'
import {
  AimOutlined,
  AuditOutlined,
  BarChartOutlined,
  BookOutlined,
  DashboardOutlined,
  FileSearchOutlined,
  HeartOutlined,
  LockOutlined,
  MenuOutlined,
  NotificationOutlined,
  ProfileOutlined,
  SafetyOutlined,
  SearchOutlined,
  StarOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import { VAI_TRO, VAI_TRO_LABEL } from '@/constants/roles'
import { useAuth } from '@/contexts/AuthContext'

const MENU_BY_ROLE = {
  [VAI_TRO.CANDIDATE]: [
    { key: '/goi-y', icon: <StarOutlined />, label: 'Gợi ý việc làm' },
    { key: '/viec-lam', icon: <SearchOutlined />, label: 'Tìm việc' },
    { key: '/ho-so', icon: <ProfileOutlined />, label: 'Hồ sơ & CV' },
    { key: '/thieu-hut-ky-nang', icon: <AimOutlined />, label: 'Thiếu hụt kỹ năng' },
    { key: '/ung-tuyen', icon: <AuditOutlined />, label: 'Hồ sơ đã nộp' },
    { key: '/tin-da-luu', icon: <HeartOutlined />, label: 'Tin đã lưu' },
    { key: '/feed-truong', icon: <NotificationOutlined />, label: 'Tin từ trường' },
    { key: '/quyen-rieng-tu', icon: <LockOutlined />, label: 'Quyền riêng tư' },
  ],
  [VAI_TRO.EMPLOYER]: [
    { key: '/nha-tuyen-dung/tin', icon: <FileSearchOutlined />, label: 'Tin tuyển dụng' },
    { key: '/bi', icon: <BarChartOutlined />, label: 'BI Dashboard' },
    { key: '/viec-lam', icon: <SearchOutlined />, label: 'Thị trường' },
  ],
  [VAI_TRO.SCHOOL]: [
    { key: '/nha-truong/feed', icon: <NotificationOutlined />, label: 'Feed & liên kết' },
    { key: '/nha-truong/bao-cao', icon: <TeamOutlined />, label: 'Báo cáo kỹ năng' },
    { key: '/bi', icon: <BarChartOutlined />, label: 'Thị trường lao động' },
  ],
  [VAI_TRO.ADMIN]: [
    { key: '/quan-tri/tin-cach-ly', icon: <SafetyOutlined />, label: 'Tin cách ly' },
    { key: '/quan-tri/chat-luong', icon: <DashboardOutlined />, label: 'Chất lượng dữ liệu' },
    { key: '/quan-tri/tu-dien', icon: <BookOutlined />, label: 'Từ điển kỹ năng' },
    { key: '/bi', icon: <BarChartOutlined />, label: 'BI Dashboard' },
  ],
}
const PUBLIC_MENU = [{ key: '/viec-lam', icon: <SearchOutlined />, label: 'Việc làm' }]

const AppLayout = () => {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const screens = Grid.useBreakpoint()
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)

  const items = user ? MENU_BY_ROLE[user.role] : PUBLIC_MENU
  const selectedKey = useMemo(
    () => items.map((i) => i.key).filter((k) => location.pathname.startsWith(k))
      .sort((a, b) => b.length - a.length)[0],
    [items, location.pathname],
  )

  const handleNavigate = ({ key }) => {
    navigate(key)
    setIsDrawerOpen(false)
  }

  const handleLogout = () => {
    logout()
    navigate('/dang-nhap')
  }

  const menu = (
    <Menu mode="inline" selectedKeys={selectedKey ? [selectedKey] : []} items={items}
      onClick={handleNavigate} style={{ borderInlineEnd: 0 }} />
  )

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {screens.md && (
        <Layout.Sider theme="light" width={230} style={{ borderRight: '1px solid #f0f0f0' }}>
          <div style={{ padding: '20px 24px' }}>
            <Link to="/"><Typography.Title level={4} style={{ margin: 0 }}>CareerBridge</Typography.Title></Link>
          </div>
          {menu}
        </Layout.Sider>
      )}
      <Layout>
        <Layout.Header style={{ background: '#fff', padding: '0 16px', display: 'flex',
          alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #f0f0f0' }}>
          <Space>
            {!screens.md && <Button icon={<MenuOutlined />} onClick={() => setIsDrawerOpen(true)} />}
            {!screens.md && <Typography.Text strong>CareerBridge</Typography.Text>}
          </Space>
          {user ? (
            <Space>
              <Typography.Text className="muted">{user.full_name} · {VAI_TRO_LABEL[user.role]}</Typography.Text>
              <Button onClick={handleLogout}>Đăng xuất</Button>
            </Space>
          ) : (
            <Space>
              <Button onClick={() => navigate('/dang-nhap')}>Đăng nhập</Button>
              <Button type="primary" onClick={() => navigate('/dang-ky')}>Đăng ký</Button>
            </Space>
          )}
        </Layout.Header>
        <Layout.Content>
          <div className="page-content"><Outlet /></div>
        </Layout.Content>
      </Layout>
      <Drawer open={isDrawerOpen} onClose={() => setIsDrawerOpen(false)} placement="left"
        width={260} title="CareerBridge">
        {menu}
      </Drawer>
    </Layout>
  )
}

export default AppLayout
