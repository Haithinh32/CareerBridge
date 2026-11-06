import { Descriptions, List, Progress, Space, Typography } from 'antd'
import { CheckCircleOutlined, InfoCircleOutlined } from '@ant-design/icons'
import { DAC_TRUNG_KHOP_LABEL } from '@/constants/candidate'
import SkillTags from '@/components/SkillTags'

const MatchExplanation = ({ match, compact = false }) => {
  if (!match) return null
  return (
    <Space direction="vertical" style={{ width: '100%' }} size="small">
      <Descriptions size="small" column={1} colon={false}>
        <Descriptions.Item label={<><CheckCircleOutlined /> Đã có</>}>
          <SkillTags skills={match.matched_skills} color="green" />
        </Descriptions.Item>
        <Descriptions.Item label="Thiếu (bắt buộc)">
          <SkillTags skills={match.missing_required_skills} color="red" emptyText="Không thiếu" />
        </Descriptions.Item>
        {!compact && (
          <Descriptions.Item label="Thiếu (ưu tiên)">
            <SkillTags skills={match.missing_optional_skills} color="orange" emptyText="Không thiếu" />
          </Descriptions.Item>
        )}
      </Descriptions>
      <List
        size="small"
        dataSource={compact ? match.reasons.slice(0, 3) : match.reasons}
        renderItem={(reason) => (
          <List.Item style={{ padding: '2px 0', border: 0 }}>
            <Typography.Text><InfoCircleOutlined className="muted" /> {reason}</Typography.Text>
          </List.Item>
        )}
      />
      {!compact && (
        <div>
          {Object.entries(match.features).map(([name, value]) => (
            <div key={name} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ width: 120 }} className="muted">{DAC_TRUNG_KHOP_LABEL[name] || name}</span>
              <Progress percent={Math.round(value * 100)} size="small" style={{ flex: 1, margin: 0 }} />
            </div>
          ))}
        </div>
      )}
    </Space>
  )
}

export default MatchExplanation
