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
          // Créer l'entrée dans la table users seulement après confirmation email
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/signup`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${session.access_token}`
            },
            body: JSON.stringify({
              id: user.id,
              username: user.user_metadata.username,
              email: user.email,
              siret_number: user.user_metadata.siret_number,
              phone: user.user_metadata.phone,
              address: user.user_metadata.address
            })
          });

          if (!response.ok) {
            throw new Error('Failed to create user profile');
          }

          router.push('/dashboard')
        } catch (error) {
          console.error('Error creating user profile:', error)
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