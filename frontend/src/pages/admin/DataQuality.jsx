import { useEffect, useState } from 'react'
import { Alert, App, Button, Card, Col, Descriptions, List, Row, Space, Statistic, Tag, Typography } from 'antd'
import { WarningOutlined } from '@ant-design/icons'
import { API_ENDPOINTS } from '@/config/api'
import { DAC_TRUNG_KHOP_LABEL } from '@/constants/candidate'
import { CHI_SO_CHAT_LUONG_LABEL } from '@/constants/chart'
import { LOAI_CO_UI } from '@/constants/job'
import ChartCard from '@/components/ChartCard'
import MultiLineChart from '@/components/charts/MultiLineChart'
import http, { getErrorMessage } from '@/utils/http'
import { formatDate, formatDateTime, formatPercent } from '@/utils/format'

const METRIC_KEYS = ['completeness', 'accuracy', 'freshness', 'uniqueness']
const QUALITY_SERIES = METRIC_KEYS.map((key) => ({ key, label: CHI_SO_CHAT_LUONG_LABEL[key] }))
const PERCENT_DOMAIN = [0, 1]

// Bảng theo dõi chất lượng dữ liệu + điều khiển các tác vụ chạy ngầm
const DataQuality = () => {
  const { message } = App.useApp()
  const [dashboard, setDashboard] = useState(null)
  const [weights, setWeights] = useState(null)
  const [runningTask, setRunningTask] = useState(null)

  useEffect(() => {
    fetchDashboard()
    fetchWeights()
  }, [])

  const handleRunTask = async (key, url) => {
    setRunningTask(key)
    try {
      const { data } = await http.post(url)
      message.success(data.message)
      fetchDashboard()
      fetchWeights()
    } catch (error) {
      message.error(getErrorMessage(error))
    } finally {
      setRunningTask(null)
    }
  }

  const handleAcknowledge = async (alertId) => {
    await http.post(API_ENDPOINTS.ADMIN.ACK_ALERT(alertId))
    fetchDashboard()
  }

  const fetchDashboard = async () => {
    const { data } = await http.get(API_ENDPOINTS.ADMIN.QUALITY)
    setDashboard(data)
  }

  const fetchWeights = async () => {
    const { data } = await http.get(API_ENDPOINTS.ADMIN.WEIGHTS)
    setWeights(data)
  }

  if (!dashboard) return null
  const latest = dashboard.snapshots.at(-1)
  const chartData = dashboard.snapshots.map((s) => ({ ...s, day: formatDate(s.taken_at) }))
  const openAlerts = dashboard.alerts.filter((a) => !a.is_acknowledged)

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Space style={{ justifyContent: 'space-between', width: '100%' }} wrap>
        <Typography.Title level={3} style={{ margin: 0 }}>Chất lượng dữ liệu</Typography.Title>
        <Space wrap>
          <Button loading={runningTask === 'ingest'} onClick={() => handleRunTask('ingest', API_ENDPOINTS.ADMIN.INGEST)}>Thu thập tin</Button>
          <Button loading={runningTask === 'scan'} onClick={() => handleRunTask('scan', API_ENDPOINTS.ADMIN.SCAN)}>Quét tin</Button>
          <Button loading={runningTask === 'retrain'} onClick={() => handleRunTask('retrain', API_ENDPOINTS.ADMIN.RETRAIN)}>Học lại trọng số</Button>
          <Button type="primary" loading={runningTask === 'snapshot'} onClick={() => handleRunTask('snapshot', API_ENDPOINTS.ADMIN.SNAPSHOT)}>Chụp chỉ số</Button>
        </Space>
      </Space>

      {openAlerts.map((a) => (
        <Alert key={a.id} type="error" showIcon icon={<WarningOutlined />}
          message={`Cảnh báo: ${a.message}`} description={formatDateTime(a.created_at)}
          action={<Button size="small" onClick={() => handleAcknowledge(a.id)}>Đã xem</Button>} />
      ))}

      {latest && (
        <Row gutter={[16, 16]}>
          {METRIC_KEYS.map((key) => (
            <Col key={key} xs={12} md={6}>
              <Card size="small"><Statistic title={CHI_SO_CHAT_LUONG_LABEL[key]} value={formatPercent(latest[key], 1)} /></Card>
            </Col>
          ))}
        </Row>
      )}

      <Row gutter={[16, 16]}>
        <Col xs={24} xl={16}>
          <ChartCard title="Chỉ số chất lượng theo thời gian" subtitle={`${latest?.total_jobs ?? 0} tin ở lần chụp gần nhất`}
            data={chartData} rowKey="id"
            columns={[
              { title: 'Ngày', dataIndex: 'day' },
              ...METRIC_KEYS.map((key) => ({ title: CHI_SO_CHAT_LUONG_LABEL[key], dataIndex: key, align: 'right', render: (v) => formatPercent(v, 1) })),
            ]}>
            <MultiLineChart data={chartData} xKey="day" series={QUALITY_SERIES} yDomain={PERCENT_DOMAIN}
              formatValue={(v) => formatPercent(v)} />
          </ChartCard>
        </Col>
        <Col xs={24} xl={8}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Card title={`Cờ chưa xử lý · ${dashboard.quarantined_jobs} tin đang cách ly`}>
              <List size="small" dataSource={Object.entries(dashboard.open_flags_by_type)}
                locale={{ emptyText: 'Không có cờ nào' }}
                renderItem={([type, count]) => (
                  <List.Item extra={<strong>{count}</strong>}>
                    <Tag color={LOAI_CO_UI[type]?.color}>{LOAI_CO_UI[type]?.text || type}</Tag>
                  </List.Item>
                )} />
            </Card>
            {weights && (
              <Card title={`Trọng số thuật toán khớp · v${weights.version}`}>
                <Descriptions size="small" column={1}>
                  {Object.entries(weights.weights).map(([name, value]) => (
                    <Descriptions.Item key={name} label={DAC_TRUNG_KHOP_LABEL[name] || name}>{formatPercent(value, 1)}</Descriptions.Item>
                  ))}
                </Descriptions>
                <div className="muted" style={{ fontSize: 12 }}>
                  {weights.sample_size ? `Học từ ${weights.sample_size} phản hồi` : 'Trọng số mặc định'}
                  {weights.metrics?.cv_auc && ` · AUC kiểm định chéo ${weights.metrics.cv_auc}`}
                </div>
              </Card>
            )}
          </Space>
        </Col>
      </Row>
    </Space>
  )
}

export default DataQuality
