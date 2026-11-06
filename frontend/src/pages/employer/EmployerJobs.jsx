import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Alert, App, Button, Card, Popconfirm, Space, Table, Tag, Tooltip, Typography } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { API_ENDPOINTS } from '@/config/api'
import { LOAI_CO_UI, TRANG_THAI_TIN, TRANG_THAI_TIN_UI } from '@/constants/job'
import { useAuth } from '@/contexts/AuthContext'
import http, { getErrorMessage } from '@/utils/http'
import { formatDate, formatSalary } from '@/utils/format'

const VERIFIED = 'verified'

const EmployerJobs = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { message } = App.useApp()
  const [jobs, setJobs] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchJobs()
  }, [])

  const handleClose = async (jobId) => {
    try {
      await http.post(API_ENDPOINTS.JOBS.CLOSE(jobId))
      message.success('Đã đóng vị trí. Quyền xem hồ sơ ứng viên đã được thu hồi.')
      fetchJobs()
    } catch (error) {
      message.error(getErrorMessage(error))
    }
  }

  const fetchJobs = async () => {
    try {
      const { data } = await http.get(API_ENDPOINTS.JOBS.MINE)
      setJobs(data.items)
    } finally {
      setIsLoading(false)
    }
  }

  const columns = [
    {
      title: 'Vị trí', key: 'title',
      render: (_, job) => (
        <Space direction="vertical" size={0}>
          <Link to={`/viec-lam/${job.id}`}>{job.title}</Link>
          <span className="muted">{job.location} · {formatSalary(job.salary_min, job.salary_max, job.salary_raw)}</span>
        </Space>
      ),
    },
    {
      title: 'Trạng thái', key: 'status',
      render: (_, job) => (
        <Space direction="vertical" size={2}>
          <Tag color={TRANG_THAI_TIN_UI[job.status].color}>{TRANG_THAI_TIN_UI[job.status].text}</Tag>
          {job.flags.filter((f) => !f.is_resolved).map((f) => (
            <Tooltip key={f.id} title={f.detail}><Tag color={LOAI_CO_UI[f.flag_type].color}>{LOAI_CO_UI[f.flag_type].text}</Tag></Tooltip>
          ))}
        </Space>
      ),
    },
    { title: 'Hạn nộp', dataIndex: 'deadline', render: formatDate, responsive: ['md'] },
    { title: 'Hồ sơ', dataIndex: 'application_count', align: 'right' },
    {
      title: '', key: 'actions',
      render: (_, job) => (
        <Space wrap>
          <Button size="small" type="primary" onClick={() => navigate(`/nha-tuyen-dung/tin/${job.id}/ung-vien`)}>
            Xếp hạng ứng viên
          </Button>
          {job.status === TRANG_THAI_TIN.OPEN && (
            <>
              <Button size="small" onClick={() => navigate(`/nha-tuyen-dung/tin/${job.id}/sua`)}>Sửa</Button>
              <Popconfirm title="Đóng vị trí này?" description="Mọi quyền xem hồ sơ ứng viên sẽ bị thu hồi."
                onConfirm={() => handleClose(job.id)} okText="Đóng" cancelText="Hủy">
                <Button size="small" danger>Đóng</Button>
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Space style={{ justifyContent: 'space-between', width: '100%' }} wrap>
        <Typography.Title level={3} style={{ margin: 0 }}>Tin tuyển dụng của doanh nghiệp</Typography.Title>
        <Button type="primary" icon={<PlusOutlined />} disabled={user?.company_verification !== VERIFIED}
          onClick={() => navigate('/nha-tuyen-dung/tin/moi')}>Đăng tin</Button>
      </Space>
      {user?.company_verification !== VERIFIED && (
        <Alert type="warning" showIcon message="Doanh nghiệp chưa được xác minh mã số thuế, chưa thể đăng tin." />
      )}
      <Card><Table rowKey="id" loading={isLoading} dataSource={jobs} columns={columns} /></Card>
    </Space>
  )
}

export default EmployerJobs
