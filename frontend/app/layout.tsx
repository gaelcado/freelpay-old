import '../styles/global.css'
import { Inter } from 'next/font/google'
import { ThemeProvider } from '@/components/ui/theme-provider'
import { Toaster } from '@/components/ui/toaster'
import { AuthProvider } from '@/components/AuthContext'
import Navbar from '@/components/ui/Navbar'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Freelpay - Get Paid Instantly',
  description: 'Freelpay helps freelancers get paid as soon as the invoice is created.',
  icons: {
    icon: '/assets/favicon.png',
  },
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
            <Navbar />
            {children}
            <Toaster />
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  )
}