// app/api/auth.ts
import { supabase } from '@/lib/supabase'
import { AuthError } from '@supabase/supabase-js'

interface UserMetadata {
  username: string
  siren_number: string
  phone: string
  address: string
}

export const signUpWithEmail = async (
  email: string,
  password: string,
  metadata: UserMetadata,
  captchaToken: string
) => {
  console.log('Starting signup process...')
  try {
    const { data: authData, error: authError } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          ...metadata,
          registration_incomplete: true
        },
        emailRedirectTo: `${window.location.origin}/auth/callback`,
        captchaToken
      }
    })

    if (authError) {
      if (authError.message.includes('User already registered')) {
        throw new Error('Un compte existe déjà avec cette adresse email. Veuillez vous connecter.')
      }
      throw authError
    }

    return authData;
  } catch (error) {
    console.error('Signup error:', error);
    throw error;
  }
}

export const signInWithEmail = async (
  email: string,
  password: string
) => {
  console.log('Starting signin process...')
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password
  })

  console.log('Signin response:', { data, error })
  if (error) throw error
  return data
}

export const signInWithGoogle = async () => {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${window.location.origin}/auth/callback`,
      queryParams: {
        prompt: 'select_account'
      }
    }
  })

  if (error) throw error
  return data
}

export const resetPassword = async (email: string) => {
  const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${window.location.origin}/auth/reset-password`,
  })

  if (error) throw error
  return data
}

export const updatePassword = async (newPassword: string) => {
  const { data, error } = await supabase.auth.updateUser({
    password: newPassword
  })

  if (error) throw error
  return data
}

export const updateUserMetadata = async (metadata: UserMetadata) => {
  const { data, error } = await supabase.auth.updateUser({
    data: {
      ...metadata,
      registration_incomplete: false
    }
  })

  if (error) throw error
  return data
}

export const requestPasswordReset = async (email: string) => {
  const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${window.location.origin}/auth/reset-password`,
  })

  if (error) throw error
  return data
}

export const updateUserPassword = async (newPassword: string) => {
  const { data, error } = await supabase.auth.updateUser({
    password: newPassword
  })

  if (error) throw error
  return data
}