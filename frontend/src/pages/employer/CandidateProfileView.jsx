import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { Card, Descriptions, List, Result, Spin, Typography } from 'antd'
import { API_ENDPOINTS } from '@/config/api'
import { HINH_THUC_LABEL } from '@/constants/job'
import SkillTags from '@/components/SkillTags'
import http, { getErrorMessage } from '@/utils/http'

// Chỉ xem được khi doanh nghiệp còn quyền: ứng viên đã ứng tuyển (chưa bị từ chối, vị trí chưa đóng)
// hoặc ứng viên bật "cho phép tìm thấy"
const CandidateProfileView = () => {
  const { candidateId } = useParams()
  const [searchParams] = useSearchParams()
  const jobId = searchParams.get('job_id')
  const [profile, setProfile] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchProfile()
  }, [candidateId, jobId])

  const fetchProfile = async () => {
    try {
      const { data } = await http.get(API_ENDPOINTS.APPLICATIONS.CANDIDATE_PROFILE(candidateId), {
        params: { job_id: jobId || undefined },
      })
      setProfile(data)
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  if (error) return <Result status="403" title="Không thể xem hồ sơ" subTitle={error} />
  if (!profile) return <Spin style={{ display: 'block', margin: 48 }} />

  return (
    <Card title={<Typography.Title level={4} style={{ margin: 0 }}>{profile.full_name}</Typography.Title>}>
      <Descriptions column={{ xs: 1, md: 2 }} bordered size="small">
        <Descriptions.Item label="Email">{profile.email}</Descriptions.Item>
        <Descriptions.Item label="Trường">{profile.school_name || '—'}</Descriptions.Item>
        <Descriptions.Item label="Ngành">{profile.major || '—'}</Descriptions.Item>
        <Descriptions.Item label="Năm học">{profile.study_year || '—'}</Descriptions.Item>
        <Descriptions.Item label="Vị trí mục tiêu">{profile.target_position || '—'}</Descriptions.Item>
        <Descriptions.Item label="Kinh nghiệm">{profile.years_experience} năm</Descriptions.Item>
        <Descriptions.Item label="Địa điểm">{profile.location || '—'}</Descriptions.Item>
        <Descriptions.Item label="Hình thức">{profile.work_types.map((w) => HINH_THUC_LABEL[w]).join(', ') || '—'}</Descriptions.Item>
        <Descriptions.Item label="Lịch rảnh" span={2}>{profile.availability || '—'}</Descriptions.Item>
        <Descriptions.Item label="Kỹ năng" span={2}>
          <SkillTags skills={profile.skills.filter((s) => s.is_confirmed)} color="blue" />
        </Descriptions.Item>
      </Descriptions>
      <List header={<strong>Dự án</strong>} dataSource={profile.projects} style={{ marginTop: 16 }}
        locale={{ emptyText: 'Chưa có dự án' }}
        renderItem={(p) => (
          <List.Item>
            <List.Item.Meta title={p.name} description={p.description} />
          </List.Item>
        )} />
    </Card>
  )
}

export default CandidateProfileView
