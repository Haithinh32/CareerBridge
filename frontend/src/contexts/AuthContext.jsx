import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { API_ENDPOINTS } from '@/config/api'
import http, { readToken, writeToken } from '@/utils/http'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  const fetchMe = useCallback(async () => {
    if (!readToken()) {
      setUser(null)
      setIsLoading(false)
      return null
    }
    try {
      const { data } = await http.get(API_ENDPOINTS.AUTH.ME)
      setUser(data)
      return data
    } catch {
      writeToken(null)
      setUser(null)
      return null
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMe()
  }, [fetchMe])

  const loginWithToken = useCallback(
    async (token) => {
      writeToken(token)
      return fetchMe()
    },
    [fetchMe],
  )

  const logout = useCallback(() => {
    writeToken(null)
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, isLoading, loginWithToken, logout, refresh: fetchMe }),
    [user, isLoading, loginWithToken, logout, fetchMe],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
