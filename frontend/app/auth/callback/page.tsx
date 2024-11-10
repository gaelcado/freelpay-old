'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { supabase } from '@/lib/supabase'

export default function AuthCallback() {
  const router = useRouter()

  useEffect(() => {
    const handleAuthCallback = async () => {
      const { data: { session }, error } = await supabase.auth.getSession()
      
      if (error) {
        console.error('Auth error:', error)
        router.push('/')
        return
      }

      if (session) {
        try {
          const { user } = session
          // Check if user already exists
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/me`, {
            headers: {
              'Authorization': `Bearer ${session.access_token}`
            }
          });

          if (response.status === 404) {
            // User doesn't exist, create new profile
            const createResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/signup`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session.access_token}`
              },
              body: JSON.stringify({
                id: user.id,
                username: user.user_metadata.username || user.email?.split('@')[0],
                email: user.email,
                siren_number: user.user_metadata.siren_number,
                phone: user.user_metadata.phone || '',
                address: user.user_metadata.address || ''
              })
            });

            if (!createResponse.ok) {
              throw new Error('Failed to create user profile');
            }
          }

          router.push('/dashboard')
        } catch (error) {
          console.error('Error handling auth callback:', error)
          router.push('/')
        }
      } else {
        router.push('/')
      }
    }

    handleAuthCallback()
  }, [router])

  return <div>Loading...</div>
} 