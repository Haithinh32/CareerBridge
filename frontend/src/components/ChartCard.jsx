import { useState } from 'react'
import { Card, Empty, Segmented, Table } from 'antd'

const VIEW = { CHART: 'chart', TABLE: 'table' }
const VIEW_OPTIONS = [
  { label: 'Biểu đồ', value: VIEW.CHART },
  { label: 'Bảng', value: VIEW.TABLE },
]

// Mỗi biểu đồ có chế độ xem bảng: dữ liệu không bao giờ chỉ được truyền đạt bằng màu sắc
const ChartCard = ({ title, subtitle, data, columns, children, rowKey = 'label' }) => {
  const [view, setView] = useState(VIEW.CHART)
  const isEmpty = !data || data.length === 0

  return (
    <Card
      title={<div>{title}{subtitle && <div className="muted" style={{ fontSize: 12, fontWeight: 400 }}>{subtitle}</div>}</div>}
      extra={!isEmpty && <Segmented size="small" options={VIEW_OPTIONS} value={view} onChange={setView} />}
      className="chart-surface"
      styles={{ body: { minHeight: 200 } }}
    >
      {isEmpty && <Empty description="Chưa có dữ liệu" />}
      {!isEmpty && view === VIEW.CHART && children}
      {!isEmpty && view === VIEW.TABLE && (
        <Table size="small" dataSource={data} columns={columns} rowKey={rowKey}
          pagination={data.length > 10 ? { pageSize: 10 } : false} />
      )}
    </Card>
  )
}

export default ChartCard
