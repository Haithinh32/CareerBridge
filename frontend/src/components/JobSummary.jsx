import { Link } from 'react-router-dom'
import { Space, Tag, Typography } from 'antd'
import { EnvironmentOutlined, CalendarOutlined, DollarOutlined } from '@ant-design/icons'
import { CAP_BAC_LABEL, HINH_THUC_LABEL } from '@/constants/job'
import { formatDate, formatSalary } from '@/utils/format'

const JobSummary = ({ job, linkTo }) => (
  <Space direction="vertical" size={2} style={{ width: '100%' }}>
    <Link to={linkTo || `/viec-lam/${job.id}`}>
      <Typography.Text strong style={{ fontSize: 16 }}>{job.title}</Typography.Text>
    </Link>
    <Typography.Text className="muted">{job.company_name}</Typography.Text>
    <Space size={[12, 4]} wrap className="muted">
      <span><EnvironmentOutlined /> {job.location || job.location_raw || '—'}</span>
      <span><DollarOutlined /> {formatSalary(job.salary_min, job.salary_max, job.salary_raw)}</span>
      <span><CalendarOutlined /> Hạn {formatDate(job.deadline)}</span>
      <Tag>{HINH_THUC_LABEL[job.work_type]}</Tag>
      <Tag>{CAP_BAC_LABEL[job.level]}</Tag>
    </Space>
  </Space>
)

export default JobSummary
