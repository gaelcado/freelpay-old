/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL || "https://likdyvggwpejufmqdbxo.supabase.co",
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxpa2R5dmdnd3BlanVmbXFkYnhvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzA2NzU1MDIsImV4cCI6MjA0NjI1MTUwMn0.2T1vu3ZDsJtGNOk3eXlssTXS7n5AKaTlxvyHgWJUWGk"
  },
  output: 'standalone',
  typescript: {
    ignoreBuildErrors: true
  }
}

module.exports = nextConfig
