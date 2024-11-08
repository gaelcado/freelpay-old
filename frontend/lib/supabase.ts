import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (typeof window === 'undefined') {
  // Côté serveur (build)
  console.warn('Supabase client initialized in server environment')
}

export const supabase = createClient(
  supabaseUrl || '',
  supabaseKey || '', 
  {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
      flowType: 'pkce'
    }
  }
)