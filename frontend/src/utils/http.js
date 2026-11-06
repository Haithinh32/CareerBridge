import axios from 'axios'
import { API_BASE_URL } from '@/config/api'

export const TOKEN_STORAGE_KEY = 'careerbridge_token'

export const readToken = () => {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY)
  } catch {
    return null
  }
}

export const writeToken = (token) => {
  try {
    if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token)
    else localStorage.removeItem(TOKEN_STORAGE_KEY)
  } catch {
    // Trình duyệt chặn localStorage: phiên chỉ tồn tại trong bộ nhớ
  }
}

const http = axios.create({ baseURL: API_BASE_URL })

http.interceptors.request.use((config) => {
  const token = readToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Lấy thông báo lỗi chuẩn {detail, code}; lỗi 422 của Pydantic trả về mảng
export const getErrorMessage = (error) => {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) return detail.map((d) => d.msg).join('; ')
  return 'Không kết nối được máy chủ'
}

export const getErrorCode = (error) => error?.response?.data?.code

export default http
