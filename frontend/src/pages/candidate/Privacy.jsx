import { useEffect, useState } from 'react'
import { Alert, App, Card, List, Space, Switch, Table, Tag, Typography } from 'antd'
import { API_ENDPOINTS } from '@/config/api'
import {
  LY_DO_THU_HOI_LABEL,
  MUC_DICH_DONG_Y_UI,
  NGUON_TRUY_CAP_LABEL,
} from '@/constants/candidate'
import http, { getErrorMessage } from '@/utils/http'
import { formatDateTime } from '@/utils/format'

const Privacy = () => {
  const { message } = App.useApp()
  const [consents, setConsents] = useState([])
  const [grants, setGrants] = useState([])
  const [pendingPurpose, setPendingPurpose] = useState(null)

  useEffect(() => {
    fetchConsents()
    fetchGrants()
  }, [])

  const handleToggle = async (purpose, isGranted) => {
    setPendingPurpose(purpose)
    try {
      const { data } = await http.put(API_ENDPOINTS.PRIVACY.CONSENT(purpose), { is_granted: isGranted })
      setConsents((prev) => prev.map((c) => (c.purpose === purpose ? data : c)))
      message.success(isGranted ? 'Đã đồng ý' : 'Đã rút lại đồng ý')
      fetchGrants()
    } catch (error) {
      message.error(getErrorMessage(error))
    } finally {
      setPendingPurpose(null)
    }
  }

  const fetchConsents = async () => {
    const { data } = await http.get(API_ENDPOINTS.PRIVACY.CONSENTS)
    setConsents(data.items)
  }

  const fetchGrants = async () => {
    const { data } = await http.get(API_ENDPOINTS.PRIVACY.ACCESS_GRANTS)
    setGrants(data.items)
  }

  const grantColumns = [
    { title: 'Doanh nghiệp', dataIndex: 'company_name' },
    { title: 'Vị trí', dataIndex: 'job_title', responsive: ['md'] },
    { title: 'Nguồn', dataIndex: 'source', render: (s) => NGUON_TRUY_CAP_LABEL[s], responsive: ['sm'] },
    {
      title: 'Trạng thái', key: 'state',
      render: (_, g) => (g.revoked_at
        ? <Space direction="vertical" size={0}><Tag>Đã thu hồi</Tag><span className="muted">{LY_DO_THU_HOI_LABEL[g.revoke_reason]} · {formatDateTime(g.revoked_at)}</span></Space>
        : <Tag color="green">Đang có quyền xem</Tag>),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Typography.Title level={3} style={{ margin: 0 }}>Quyền riêng tư</Typography.Title>
        <Typography.Text className="muted">
          Bạn đồng ý riêng cho từng mục đích và có thể rút lại bất cứ lúc nào (Luật Bảo vệ dữ liệu cá nhân 2025).
        </Typography.Text>
      </div>
      <Card title="Đồng ý theo mục đích">
        <List
          dataSource={consents}
          renderItem={(c) => (
            <List.Item
              actions={[
                <Switch key="toggle" checked={c.is_granted} loading={pendingPurpose === c.purpose}
                  onChange={(v) => handleToggle(c.purpose, v)} aria-label={MUC_DICH_DONG_Y_UI[c.purpose].title} />,
              ]}>
              <List.Item.Meta
                title={MUC_DICH_DONG_Y_UI[c.purpose].title}
                description={
                  <>
                    {MUC_DICH_DONG_Y_UI[c.purpose].description}
                    <div className="muted" style={{ fontSize: 12 }}>
                      {c.is_granted && `Đồng ý lúc ${formatDateTime(c.granted_at)}`}
                      {!c.is_granted && c.revoked_at && `Rút lại lúc ${formatDateTime(c.revoked_at)}`}
                    </div>
                  </>
                }
              />
            </List.Item>
          )}
        />
      </Card>
      <Card title="Doanh nghiệp có quyền xem hồ sơ của bạn">
        <Alert type="info" showIcon style={{ marginBottom: 12 }}
          message="Quyền xem tự động bị thu hồi khi doanh nghiệp từ chối bạn hoặc đóng vị trí (Điều 25)." />
        <Table rowKey="id" size="small" dataSource={grants} columns={grantColumns} pagination={{ pageSize: 10 }} />
      </Card>
    </Space>
  )
}

export default Privacy
