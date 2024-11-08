// components/AuthContext.tsx
'use client'

import { createContext, useContext, useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import { Session } from '@supabase/supabase-js'

const AuthContext = createContext<{
  isAuthenticated: boolean
  setIsAuthenticated: (value: boolean) => void
  session: Session | null
  setSession: (session: Session | null) => void
  getAccessToken: () => Promise<string | null>
}>({
  isAuthenticated: false,
  setIsAuthenticated: () => {},
  session: null,
  setSession: () => {},
  getAccessToken: async () => null,
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [session, setSession] = useState<Session | null>(null)

  const getAccessToken = async () => {
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token ?? null
  }

  useEffect(() => {
    const checkAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      setSession(session)
      setIsAuthenticated(!!session)
    }
    
    checkAuth()

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setIsAuthenticated(!!session)
    })

    return () => subscription.unsubscribe()
  }, [])

  return (
    <AuthContext.Provider value={{ isAuthenticated, setIsAuthenticated, session, setSession, getAccessToken }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)