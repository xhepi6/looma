import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '@/lib/api'

interface AuthContextType {
  user: api.User | null
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  const [isInitialized, setIsInitialized] = useState(false)

  const isLoginPage = location.pathname === '/login'

  const { data: user, isLoading, error } = useQuery({
    queryKey: ['me'],
    queryFn: api.getMe,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
    staleTime: Infinity,
    enabled: !isLoginPage,
  })

  useEffect(() => {
    if (isLoginPage) {
      setIsInitialized(true)
      return
    }
    if (!isLoading) {
      setIsInitialized(true)
      if (error) {
        navigate('/login')
      }
    }
  }, [isLoading, error, isLoginPage, navigate])

  const loginMutation = useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      api.login(username, password),
    onSuccess: (data) => {
      queryClient.setQueryData(['me'], data.user)
      navigate('/board/1')
    },
  })

  const logoutMutation = useMutation({
    mutationFn: api.logout,
    onSuccess: () => {
      queryClient.clear()
      navigate('/login')
    },
  })

  const handleLogin = async (username: string, password: string) => {
    await loginMutation.mutateAsync({ username, password })
  }

  const handleLogout = async () => {
    await logoutMutation.mutateAsync()
  }

  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <AuthContext.Provider value={{ user: user ?? null, isLoading, login: handleLogin, logout: handleLogout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
