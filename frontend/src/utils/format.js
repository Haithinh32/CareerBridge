import dayjs from 'dayjs'

const MILLION = 1_000_000

const toMillion = (value) => {
  const m = value / MILLION
  return Number.isInteger(m) ? `${m}` : m.toFixed(1)
}

export const formatSalary = (min, max, raw) => {
  if (min && max) return min === max ? `${toMillion(min)} triệu` : `${toMillion(min)} - ${toMillion(max)} triệu`
  if (min) return `Từ ${toMillion(min)} triệu`
  if (max) return `Đến ${toMillion(max)} triệu`
  return raw || 'Thỏa thuận'
}

export const formatDate = (value) => (value ? dayjs(value).format('DD/MM/YYYY') : '—')

export const formatDateTime = (value) => (value ? dayjs(value).format('DD/MM/YYYY HH:mm') : '—')

export const formatPercent = (ratio, digits = 0) =>
  ratio === null || ratio === undefined ? '—' : `${(ratio * 100).toFixed(digits)}%`

export const scoreColor = (score) => {
  if (score >= 70) return 'green'
  if (score >= 45) return 'gold'
  return 'default'
}
