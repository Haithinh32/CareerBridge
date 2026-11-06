import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Alert, App, Card, List, Select, Space, Typography, Upload } from 'antd'
import { InboxOutlined } from '@ant-design/icons'
import { API_ENDPOINTS } from '@/config/api'
import { LOAI_TAI_LIEU, LOAI_TAI_LIEU_LABEL } from '@/constants/candidate'
import SkillTags from '@/components/SkillTags'
import http, { getErrorCode, getErrorMessage } from '@/utils/http'

const ACCEPTED_TYPES = '.pdf,.docx'
const CONSENT_REQUIRED = 'CONSENT_REQUIRED'

const CvUploadCard = ({ onAnalyzed }) => {
  const { message } = App.useApp()
  const [documentType, setDocumentType] = useState(LOAI_TAI_LIEU.CV)
  const [analysis, setAnalysis] = useState(null)
  const [needsConsent, setNeedsConsent] = useState(false)

  const handleUpload = async ({ file, onSuccess, onError }) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('document_type', documentType)
    try {
      const { data } = await http.post(API_ENDPOINTS.CANDIDATE.DOCUMENTS, formData)
      setAnalysis(data)
      setNeedsConsent(false)
      message.success(`AI đã trích ${data.extracted_skills.length} kỹ năng — hãy xác nhận bên dưới`)
      onSuccess(data)
      onAnalyzed()
    } catch (error) {
      setNeedsConsent(getErrorCode(error) === CONSENT_REQUIRED)
      message.error(getErrorMessage(error))
      onError(error)
    }
  }

  return (
    <Card title="Tải lên CV, đồ án hoặc hồ sơ LinkedIn (PDF)">
      <Space direction="vertical" style={{ width: '100%' }}>
        <Select value={documentType} onChange={setDocumentType} style={{ width: 240 }}
          options={Object.entries(LOAI_TAI_LIEU_LABEL).map(([value, label]) => ({ value, label }))} />
        {needsConsent && (
          <Alert type="warning" showIcon
            message={<>Bạn cần bật “Phân tích CV tự động” trong <Link to="/quyen-rieng-tu">Quyền riêng tư</Link>.</>} />
        )}
        <Upload.Dragger accept={ACCEPTED_TYPES} customRequest={handleUpload} showUploadList={false} multiple={false}>
          <p className="ant-upload-drag-icon"><InboxOutlined /></p>
          <p className="ant-upload-text">Kéo thả hoặc bấm để chọn file PDF / DOCX</p>
          <p className="ant-upload-hint">AI sẽ đọc file và trích kỹ năng, học vấn, dự án</p>
        </Upload.Dragger>
        {analysis && (
          <Card size="small" type="inner" title={`Kết quả phân tích: ${analysis.document.file_name}`}>
            <Typography.Paragraph>
              <strong>Kỹ năng tìm thấy:</strong> <SkillTags skills={analysis.extracted_skills} color="purple" />
            </Typography.Paragraph>
            <Typography.Paragraph>
              <strong>Kinh nghiệm ước tính:</strong> {analysis.years_experience} năm
            </Typography.Paragraph>
            {analysis.education.length > 0 && (
              <List size="small" header={<strong>Học vấn</strong>} dataSource={analysis.education}
                renderItem={(e) => <List.Item>{e.school} {e.degree && `· ${e.degree}`} {e.gpa && `· GPA ${e.gpa}`}</List.Item>} />
            )}
            {analysis.projects.length > 0 && (
              <List size="small" header={<strong>Dự án</strong>} dataSource={analysis.projects}
                renderItem={(p) => <List.Item>{p.name} {p.skills?.length > 0 && <span className="muted">({p.skills.join(', ')})</span>}</List.Item>} />
            )}
          </Card>
        )}
      </Space>
    </Card>
  )
}

export default CvUploadCard
