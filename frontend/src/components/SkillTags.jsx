import { Space, Tag } from 'antd'

const SkillTags = ({ skills = [], color, emptyText = '—' }) => {
  if (!skills.length) return <span className="muted">{emptyText}</span>
  return (
    <Space size={[4, 4]} wrap>
      {skills.map((s) => <Tag key={s.skill_id} color={color}>{s.name}</Tag>)}
    </Space>
  )
}

export default SkillTags
