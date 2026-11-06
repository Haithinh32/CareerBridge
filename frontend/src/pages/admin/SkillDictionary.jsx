import { useEffect, useState } from 'react'
import { App, Button, Card, Form, Input, Popconfirm, Space, Table, Tag, Typography } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { API_ENDPOINTS } from '@/config/api'
import http, { getErrorMessage } from '@/utils/http'

// Quản lý từ điển kỹ năng: tên chuẩn, nhóm, từ đồng nghĩa và viết tắt
const SkillDictionary = () => {
  const { message } = App.useApp()
  const [skills, setSkills] = useState([])
  const [query, setQuery] = useState('')
  const [aliasDrafts, setAliasDrafts] = useState({})
  const [form] = Form.useForm()

  useEffect(() => {
    fetchSkills()
  }, [])

  const run = async (action, successText) => {
    try {
      await action()
      if (successText) message.success(successText)
      fetchSkills()
    } catch (error) {
      message.error(getErrorMessage(error))
    }
  }

  const handleCreate = (values) => run(async () => {
    const aliases = (values.aliases || '').split(',').map((a) => a.trim()).filter(Boolean)
    await http.post(API_ENDPOINTS.SKILLS.CREATE, { name: values.name, category: values.category || 'Khác', aliases })
    form.resetFields()
  }, 'Đã thêm kỹ năng')

  const handleAddAlias = (skillId) => run(async () => {
    await http.post(API_ENDPOINTS.SKILLS.ADD_ALIAS(skillId), { alias: aliasDrafts[skillId] })
    setAliasDrafts((prev) => ({ ...prev, [skillId]: '' }))
  })

  const handleDeleteAlias = (aliasId) => run(() => http.delete(API_ENDPOINTS.SKILLS.DELETE_ALIAS(aliasId)))
  const handleDeleteSkill = (skillId) => run(() => http.delete(API_ENDPOINTS.SKILLS.DELETE(skillId)), 'Đã xóa kỹ năng')

  const fetchSkills = async () => {
    const { data } = await http.get(API_ENDPOINTS.SKILLS.LIST)
    setSkills(data.items)
  }

  const needle = query.trim().toLowerCase()
  const visible = needle
    ? skills.filter((s) => s.name.toLowerCase().includes(needle) || s.aliases.some((a) => a.alias.includes(needle)))
    : skills

  const columns = [
    { title: 'Kỹ năng', dataIndex: 'name', width: 180 },
    { title: 'Nhóm', dataIndex: 'category', width: 140, responsive: ['md'] },
    {
      title: 'Từ đồng nghĩa / viết tắt', key: 'aliases',
      render: (_, s) => (
        <Space size={[4, 4]} wrap>
          {s.aliases.map((a) => (
            <Tag key={a.id} closable onClose={(e) => { e.preventDefault(); handleDeleteAlias(a.id) }}>{a.alias}</Tag>
          ))}
          <Space.Compact size="small">
            <Input style={{ width: 120 }} placeholder="thêm" value={aliasDrafts[s.id] || ''}
              onChange={(e) => setAliasDrafts((prev) => ({ ...prev, [s.id]: e.target.value }))}
              onPressEnter={() => handleAddAlias(s.id)} />
            <Button icon={<PlusOutlined />} aria-label="Thêm từ đồng nghĩa" onClick={() => handleAddAlias(s.id)} />
          </Space.Compact>
        </Space>
      ),
    },
    {
      title: '', key: 'delete', width: 80,
      render: (_, s) => (
        <Popconfirm title={`Xóa kỹ năng ${s.name}?`} onConfirm={() => handleDeleteSkill(s.id)}>
          <Button size="small" type="link" danger>Xóa</Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Typography.Title level={3} style={{ margin: 0 }}>Từ điển kỹ năng ({skills.length})</Typography.Title>
      <Card title="Thêm kỹ năng">
        <Form form={form} layout="inline" onFinish={handleCreate} style={{ rowGap: 8 }}>
          <Form.Item name="name" rules={[{ required: true }]}><Input placeholder="Tên chuẩn, VD: Kubernetes" /></Form.Item>
          <Form.Item name="category"><Input placeholder="Nhóm, VD: DevOps" /></Form.Item>
          <Form.Item name="aliases"><Input placeholder="Từ đồng nghĩa, cách nhau dấu phẩy" style={{ width: 260 }} /></Form.Item>
          <Button type="primary" htmlType="submit">Thêm</Button>
        </Form>
      </Card>
      <Card extra={<Input.Search placeholder="Tìm kỹ năng / từ đồng nghĩa" allowClear onChange={(e) => setQuery(e.target.value)} />}>
        <Table rowKey="id" size="small" dataSource={visible} columns={columns} pagination={{ pageSize: 20 }} />
      </Card>
    </Space>
  )
}

export default SkillDictionary
