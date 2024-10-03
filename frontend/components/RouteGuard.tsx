import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useToast } from '@/components/ui/use-toast'

export function RouteGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [authorized, setAuthorized] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    const authCheck = () => {
      const token = localStorage.getItem('token')
      if (!token) {
        setAuthorized(false)
        toast({
          title: 'Unauthorized',
          description: 'Please log in to access this page.',
          variant: 'destructive',
        })
        router.push('/')
      } else {
        setAuthorized(true)
      }
    }

    authCheck()
  }, [router, toast])

  return authorized ? <>{children}</> : null
}

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('token')
    setIsAuthenticated(!!token)
  }, [])

  return isAuthenticated
}
