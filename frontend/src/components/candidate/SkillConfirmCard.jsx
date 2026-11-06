import { useEffect, useState } from 'react'
import { App, Button, Card, Rate, Space, Table, Tag, Typography } from 'antd'
import { DeleteOutlined } from '@ant-design/icons'
import { API_ENDPOINTS } from '@/config/api'
import { NGUON_KY_NANG_LABEL } from '@/constants/candidate'
import SkillSelect from '@/components/SkillSelect'
import http, { getErrorMessage } from '@/utils/http'

// Ứng viên xác nhận, chỉnh mức độ, xóa hoặc thêm kỹ năng sau khi AI trích xuất
const SkillConfirmCard = ({ skills, onSaved }) => {
  const { message } = App.useApp()
  const [rows, setRows] = useState([])
  const [newSkillId, setNewSkillId] = useState()
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    setRows(skills.map((s) => ({ ...s })))
  }, [skills])

  const hasUnconfirmed = rows.some((r) => !r.is_confirmed)

  const handleLevelChange = (skillId, level) => {
    setRows((prev) => prev.map((r) => (r.skill_id === skillId ? { ...r, level } : r)))
  }

  const handleRemove = (skillId) => setRows((prev) => prev.filter((r) => r.skill_id !== skillId))

  const handleAdd = (skillId, option) => {
    if (!skillId || rows.some((r) => r.skill_id === skillId)) return
    setRows((prev) => [...prev, { skill_id: skillId, name: option.label, source: 'manual', is_confirmed: true, level: 3 }])
    setNewSkillId(undefined)
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await http.put(API_ENDPOINTS.CANDIDATE.SKILLS, {
        skills: rows.map((r) => ({ skill_id: r.skill_id, level: r.level || null })),
      })
      message.success('Đã lưu danh sách kỹ năng')
      onSaved()
    } catch (error) {
      message.error(getErrorMessage(error))
    } finally {
      setIsSaving(false)
    }
  }

  const columns = [
    { title: 'Kỹ năng', dataIndex: 'name' },
    {
      title: 'Nguồn', dataIndex: 'source', responsive: ['sm'],
      render: (source, r) => (
        <Space>
          <Tag>{NGUON_KY_NANG_LABEL[source]}</Tag>
          {!r.is_confirmed && <Tag color="orange">Chưa xác nhận</Tag>}
        </Space>
      ),
    },
    {
      title: 'Mức độ', dataIndex: 'level',
      render: (level, r) => <Rate count={5} value={level || 0} onChange={(v) => handleLevelChange(r.skill_id, v)} />,
    },
    {
      title: '', key: 'remove', width: 48,
      render: (_, r) => <Button type="text" danger icon={<DeleteOutlined />} aria-label="Xóa"
        onClick={() => handleRemove(r.skill_id)} />,
    },
  ]

  return (
    <Card title="Xác nhận kỹ năng"
      extra={<Button type="primary" loading={isSaving} onClick={handleSave}>Lưu & xác nhận</Button>}>
      {hasUnconfirmed && (
        <Typography.Paragraph type="warning">
          Một số kỹ năng do AI trích xuất chưa được xác nhận. Xóa kỹ năng sai và bấm “Lưu & xác nhận”.
        </Typography.Paragraph>
      )}
      <Table size="small" rowKey="skill_id" dataSource={rows} columns={columns} pagination={false} />
      <div style={{ marginTop: 12 }}>
        <SkillSelect mode={undefined} value={newSkillId} placeholder="Thêm kỹ năng khác"
          onChange={handleAdd} />
      </div>
    </Card>
  )
}

export default SkillConfirmCard
