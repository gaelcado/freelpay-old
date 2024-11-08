import axios from 'axios'
import { supabase } from './supabase'

const API_URL = process.env.NEXT_PUBLIC_API_URL

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true
})

// Intercepteur pour ajouter le token à chaque requête
api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession()
  
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
}, (error) => {
  return Promise.reject(error)
})

export default api 