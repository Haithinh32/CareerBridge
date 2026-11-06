import { useEffect, useState } from 'react'
import { Select } from 'antd'
import { API_ENDPOINTS } from '@/config/api'
import http from '@/utils/http'

// Chọn kỹ năng từ từ điển; tìm được cả theo từ đồng nghĩa/viết tắt
const SkillSelect = ({ value, onChange, mode, placeholder = 'Chọn kỹ năng', ...rest }) => {
  const [skills, setSkills] = useState([])

  useEffect(() => {
    fetchSkills()
  }, [])

  const fetchSkills = async () => {
    const { data } = await http.get(API_ENDPOINTS.SKILLS.LIST)
    setSkills(data.items)
  }

  const options = skills.map((s) => ({
    value: s.id,
    label: s.name,
    search: [s.name, ...s.aliases.map((a) => a.alias)].join(' ').toLowerCase(),
  }))

  return (
    <Select
      mode={mode}
      value={value}
      onChange={onChange}
      options={options}
      placeholder={placeholder}
      showSearch
      filterOption={(input, option) => option.search.includes(input.toLowerCase())}
      style={{ width: '100%' }}
      {...rest}
    />
  )
}

export default SkillSelect
